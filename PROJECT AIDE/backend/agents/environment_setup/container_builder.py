"""
container_builder.py

Generates pragmatic Dockerfiles and VSCode DevContainer configuration for a repository,
optionally builds the Docker image (if Docker CLI available), and runs basic sanity checks.

Design goals:
 - Safe defaults, easy-to-understand generated artifacts
 - Support multi-ecosystem projects (python, node, java) with layered Dockerfile
 - Keep workspace bind-mount friendly for local development
 - Capture logs and structured result object for Feedback/Walkthrough agents
"""

from __future__ import annotations
import os
import shutil
import subprocess
import json
import tempfile
import textwrap
import platform
from typing import Tuple, Dict, List, Optional, Any

# Import your dependency_resolver helper
try:
    from agents.environment_setup.dependency_resolver import resolve_repo_dependencies
except ImportError:
    # Allow running when executed as a script
    import os as _os, sys as _sys
    _BACKEND_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
    _PROJECT_ROOT = _os.path.dirname(_BACKEND_DIR)
    if _PROJECT_ROOT not in _sys.path:
        _sys.path.insert(0, _PROJECT_ROOT)
    from agents.environment_setup.dependency_resolver import resolve_repo_dependencies  # type: ignore

# Simple logger fallback (replace with your project's logger)
import logging
logger = logging.getLogger("container_builder")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)
logger.setLevel(logging.INFO)


class ContainerBuildResult:
    def __init__(self):
        self.dockerfile_path: Optional[str] = None
        self.devcontainer_path: Optional[str] = None
        self.image_name: Optional[str] = None
        self.build_logs: List[str] = []
        self.sanity_logs: Dict[str, List[str]] = {}
        self.success: bool = True
        self.error: Optional[str] = None
        self.suggested_commands: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dockerfile_path": self.dockerfile_path,
            "devcontainer_path": self.devcontainer_path,
            "image_name": self.image_name,
            "build_logs": self.build_logs,
            "sanity_logs": self.sanity_logs,
            "success": self.success,
            "error": self.error,
            "suggested_commands": self.suggested_commands,
        }


# Helpers ---------------------------------------------------------------------
def _run_cmd(cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = 300) -> Tuple[int, str, str]:
    """Run a shell command and capture stdout/stderr. Returns (rc, stdout, stderr)."""
    shell = platform.system() == "Windows"
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",  # Force UTF-8 decoding
            errors="replace",   # Replace undecodable characters
            timeout=timeout,
            shell=shell  # Use shell=True on Windows for cmd.exe
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except subprocess.TimeoutExpired as e:
        return 124, "", f"TimeoutExpired: {str(e)}"
    except Exception as e:
        return 1, "", str(e)


def docker_available() -> bool:
    rc, out, err = _run_cmd(["docker", "--version"])
    return rc == 0


# Dockerfile generation utilities ---------------------------------------------
def generate_dockerfile_text(summary: Dict[str, Any], repo_root_in_container: str = "/workspace") -> str:
    """
    Generate a multi-stage, pragmatic Dockerfile that tries to handle Python/Node/Java.
    - Uses official base images for each language.
    - Orders steps to maximize Docker cache when building.
    - Designed for dev: mounts code at runtime to avoid rebuilding for code changes.
    - Includes better error handling and timeout management.
    """
    types = summary.get("types", [])
    pieces: List[str] = []
    
    # Use Python slim base for Python projects, Ubuntu for multi-language
    if "python" in types and len(types) == 1:
        # Use a more stable base image with better error handling
        # Try to use a more accessible base image if Docker Hub is having issues
        base = "python:3.11-slim"
        pieces.append(f"# Using {base} - if this fails, try: python:3.11-alpine or ubuntu:22.04\n")
        pieces.append(f"FROM {base} AS base\n")
        pieces.append("ENV DEBIAN_FRONTEND=noninteractive\n")
        pieces.append("ENV PIP_DEFAULT_TIMEOUT=300\n")
        pieces.append("ENV PIP_DISABLE_PIP_VERSION_CHECK=1\n")
        pieces.append("# Update package lists with retry logic\n")
        pieces.append("RUN for i in 1 2 3; do \\\n"
                      "    apt-get update --fix-missing && break || sleep 5; \\\n"
                      "done\n")
        pieces.append("# Install system packages with retry logic\n")
        pieces.append("RUN for i in 1 2 3; do \\\n"
                      "    apt-get install -y --no-install-recommends \\\n"
                      "        ca-certificates curl git build-essential \\\n"
                      "        libpq-dev && break || sleep 5; \\\n"
                      "done\n")
        pieces.append("# Clean up\n")
        pieces.append("RUN apt-get clean \\\n"
                      "    && rm -rf /var/lib/apt/lists/* \\\n"
                      "    && rm -rf /tmp/* \\\n"
                      "    && rm -rf /var/tmp/*\n")
    else:
        # Multi-language or non-Python projects
        base = "ubuntu:22.04"
        pieces.append(f"FROM {base} AS base\n")
        pieces.append("ENV DEBIAN_FRONTEND=noninteractive\n")
        pieces.append("# Update package lists with retry logic\n")
        pieces.append("RUN for i in 1 2 3; do \\\n"
                      "    apt-get update --fix-missing && break || sleep 5; \\\n"
                      "done\n")
        pieces.append("# Install system packages with retry logic\n")
        pieces.append("RUN for i in 1 2 3; do \\\n"
                      "    apt-get install -y --no-install-recommends \\\n"
                      "        ca-certificates curl git build-essential")
        
        if "python" in types:
            pieces.append(" \\\n        python3 python3-venv python3-pip")
        if "node" in types:
            pieces.append(" \\\n        nodejs npm")
        if "java" in types:
            pieces.append(" \\\n        openjdk-11-jdk maven")
        
        pieces.append(" && break || sleep 5; \\\n"
                      "done\n")
        pieces.append("# Clean up\n")
        pieces.append("RUN apt-get clean \\\n"
                      "    && rm -rf /var/lib/apt/lists/* \\\n"
                      "    && rm -rf /tmp/* \\\n"
                      "    && rm -rf /var/tmp/*\n")
    
    # Create workspace dir
    pieces.append(f"WORKDIR {repo_root_in_container}\n")
    
    # Copy only dependency manifests first for caching
    if "python" in types:
        pieces.append("COPY requirements.txt* ./\n")
        pieces.append("# Clean and deduplicate requirements (simple approach)\n")
        pieces.append("RUN if [ -f requirements.txt ]; then \\\n"
                      "    awk '!seen[$1]++ && !/^#/ && NF' requirements.txt > requirements_clean.txt; \\\n"
                      "fi\n")
        pieces.append("RUN python3 -m pip install --upgrade pip setuptools wheel \\\n")
        pieces.append("    && if [ -f requirements_lightweight.txt ]; then \\\n")
        pieces.append("        echo 'Installing lightweight requirements (without heavy ML packages)...' && \\\n")
        pieces.append("        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements_lightweight.txt || \\\n")
        pieces.append("        (echo 'Lightweight install failed, trying full requirements...' && \\\n")
        pieces.append("         python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements_clean.txt || \\\n")
        pieces.append("         python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt); \\\n")
        pieces.append("    elif [ -f requirements_clean.txt ]; then \\\n")
        pieces.append("        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements_clean.txt || \\\n")
        pieces.append("        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt; \\\n")
        pieces.append("    elif [ -f requirements.txt ]; then \\\n")
        pieces.append("        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt; \\\n")
        pieces.append("    fi\n")
    
    if "node" in types:
        pieces.append("COPY package*.json ./\n")
        pieces.append("RUN if [ -f package.json ]; then \\\n")
        pieces.append("    npm install --no-audit --no-fund --no-optional --timeout=300000; \\\n")
        pieces.append("fi\n")
    
    if "java" in types:
        pieces.append("COPY pom.xml ./\n")
        pieces.append("RUN if [ -f pom.xml ]; then \\\n")
        pieces.append("    mvn -B dependency:resolve -Dmaven.wagon.http.connectionTimeout=300000; \\\n")
        pieces.append("fi\n")
    
    # Copy rest of the code (for production builds you'd choose different strategy)
    pieces.append("COPY . .\n")
    
    # Default command is a no-op; dev workflow mounts and runs commands interactively
    pieces.append("CMD [\"bash\"]\n")
    return "".join(pieces)


def generate_dockerignore_text() -> str:
    """Generate a .dockerignore file to reduce build context and improve performance."""
    return """# Git
.git
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.yarn-integrity

# Java
target/
*.class
*.jar
*.war
*.ear
*.zip
*.tar.gz
*.rar

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.temp
*.bak
*.backup

# Build artifacts
dist/
build/
*.egg-info/
"""


def generate_devcontainer_json(summary: Dict[str, Any], image_name: Optional[str] = None, repo_root_in_container: str = "/workspace") -> str:
    """
    Generate a VS Code Dev Containers config that either references a built image or a Dockerfile.
    """
    config: Dict[str, Any] = {
        "name": "DevContainer",
        "workspaceFolder": repo_root_in_container,
        "remoteUser": "root",
        "customizations": {
            "vscode": {
                "extensions": [
                    "ms-python.python",
                    "ms-python.vscode-pylance",
                    "ms-azuretools.vscode-docker",
                    "esbenp.prettier-vscode"
                ]
            }
        },
        "mounts": [f"source=${{localWorkspaceFolder}},target={repo_root_in_container},type=bind"],
        "postCreateCommand": []
    }

    if image_name:
        config["image"] = image_name
    else:
        config["build"] = {
            "dockerfile": "Dockerfile",
            "context": ".",
        }

    # Basic post-create sanity commands per ecosystem
    checks = summary.get("sanity_checks", {})
    post_cmds: List[str] = []
    for cmds in checks.values():
        post_cmds.extend(cmds)
    if post_cmds:
        config["postCreateCommand"] = " && ".join(post_cmds)

    return json.dumps(config, indent=2)


def clean_requirements_file(repo_root: str) -> str:
    """Clean and deduplicate requirements.txt file. Returns path to cleaned file."""
    req_path = os.path.join(repo_root, "requirements.txt")
    clean_path = os.path.join(repo_root, "requirements_clean.txt")
    lightweight_path = os.path.join(repo_root, "requirements_lightweight.txt")
    
    if not os.path.exists(req_path):
        return req_path
    
    try:
        import re
        lines = []
        seen = set()
        heavy_packages = {'tensorflow', 'torch', 'torchvision', 'torchaudio', 'transformers', 'datasets', 'accelerate'}
        
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (before any version specifiers)
                    pkg = re.split(r'[>=<!=]', line)[0].strip().lower()
                    if pkg not in seen:
                        seen.add(pkg)
                        lines.append(line)
        
        # Write cleaned requirements
        with open(clean_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        # Create lightweight version without heavy packages
        lightweight_lines = []
        for line in lines:
            pkg = re.split(r'[>=<!=]', line)[0].strip().lower()
            if pkg not in heavy_packages:
                lightweight_lines.append(line)
        
        with open(lightweight_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lightweight_lines))
        
        logger.info(f"Cleaned requirements.txt: {len(lines)} unique packages")
        logger.info(f"Lightweight requirements.txt: {len(lightweight_lines)} packages (removed heavy ML packages)")
        return clean_path
        
    except Exception as e:
        logger.warning(f"Failed to clean requirements.txt: {e}")
        return req_path


def write_artifacts(repo_root: str, summary: Dict[str, Any], image_name: Optional[str] = None) -> Tuple[str, str]:
    """Write Dockerfile, .dockerignore, and .devcontainer/devcontainer.json into the repo root."""
    dockerfile_text = generate_dockerfile_text(summary)
    dockerignore_text = generate_dockerignore_text()
    devcontainer_text = generate_devcontainer_json(summary, image_name=image_name)

    # Clean requirements.txt if it exists
    if "python" in summary.get("types", []):
        clean_requirements_file(repo_root)

    # Write Dockerfile
    dockerfile_path = os.path.join(repo_root, "Dockerfile")
    with open(dockerfile_path, "w", encoding="utf-8") as f:
        f.write(dockerfile_text)
    
    # Write .dockerignore
    dockerignore_path = os.path.join(repo_root, ".dockerignore")
    with open(dockerignore_path, "w", encoding="utf-8") as f:
        f.write(dockerignore_text)
    
    # Write DevContainer config
    devcontainer_dir = os.path.join(repo_root, ".devcontainer")
    os.makedirs(devcontainer_dir, exist_ok=True)
    devcontainer_path = os.path.join(devcontainer_dir, "devcontainer.json")
    with open(devcontainer_path, "w", encoding="utf-8") as f:
        f.write(devcontainer_text)

    return dockerfile_path, devcontainer_path


def build_image(repo_root: str, image_name: str) -> Tuple[bool, List[str]]:
    """Attempt to build a Docker image; returns (success, logs)."""
    logs: List[str] = []
    if not docker_available():
        logs.append("Docker not available; skipping build")
        return False, logs
    
    # Try building with the generated Dockerfile first
    build_cmd = ["docker", "build", "--progress=plain", "--no-cache", "-t", image_name, "."]
    logger.info(f"Building Docker image: {' '.join(build_cmd)}")
    
    rc, out, err = _run_cmd(build_cmd, cwd=repo_root, timeout=7200)  # Increased timeout to 2 hours
    
    # If Docker Hub connectivity fails, try with Ubuntu base image
    if rc != 0 and "http: server gave http response to https client" in '\n'.join([out, err]).lower():
        logs.append("Docker Hub connectivity failed, trying Ubuntu base image...")
        
        # Create a fallback Dockerfile with Ubuntu base
        fallback_dockerfile = """FROM ubuntu:22.04 AS base
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Update package lists with retry logic
RUN for i in 1 2 3; do \\
    apt-get update --fix-missing && break || sleep 5; \\
done

# Install system packages with retry logic
RUN for i in 1 2 3; do \\
    apt-get install -y --no-install-recommends \\
        ca-certificates curl git build-essential \\
        python3 python3-venv python3-pip \\
        libpq-dev && break || sleep 5; \\
done

# Clean up
RUN apt-get clean \\
    && rm -rf /var/lib/apt/lists/* \\
    && rm -rf /tmp/* \\
    && rm -rf /var/tmp/*

WORKDIR /workspace
COPY requirements.txt* ./

# Clean and deduplicate requirements (simple approach)
RUN if [ -f requirements.txt ]; then \\
    awk '!seen[$1]++ && !/^#/ && NF' requirements.txt > requirements_clean.txt; \\
fi

RUN python3 -m pip install --upgrade pip setuptools wheel \\
    && if [ -f requirements_lightweight.txt ]; then \\
        echo 'Installing lightweight requirements (without heavy ML packages)...' && \\
        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements_lightweight.txt || \\
        (echo 'Lightweight install failed, trying full requirements...' && \\
         python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements_clean.txt || \\
         python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt); \\
    elif [ -f requirements_clean.txt ]; then \\
        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements_clean.txt || \\
        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt; \\
    elif [ -f requirements.txt ]; then \\
        python3 -m pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt; \\
    fi

COPY . .
CMD ["bash"]
"""
        
        # Write fallback Dockerfile
        fallback_path = os.path.join(repo_root, "Dockerfile.fallback")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(fallback_dockerfile)
        
        # Try building with fallback Dockerfile
        fallback_cmd = ["docker", "build", "--progress=plain", "--no-cache", "-f", "Dockerfile.fallback", "-t", image_name, "."]
        logger.info(f"Trying fallback build: {' '.join(fallback_cmd)}")
        
        rc, out, err = _run_cmd(fallback_cmd, cwd=repo_root, timeout=7200)
        
        # Clean up fallback file
        try:
            os.remove(fallback_path)
        except:
            pass
    
    # Clean up logs - remove empty lines and combine output
    all_output = []
    if out:
        all_output.extend(out.split('\n'))
    if err:
        all_output.extend(err.split('\n'))
    
    # Filter out empty lines and add meaningful context
    logs.extend([line for line in all_output if line.strip()])
    
    if rc != 0:
        logs.append(f"Build failed with exit code: {rc}")
        logger.error(f"Docker build failed for {repo_root}. Exit code: {rc}")
        
        # Check for specific error patterns and provide helpful suggestions
        error_text = '\n'.join(all_output).lower()
        
        if "http: server gave http response to https client" in error_text:
            logs.append("")
            logs.append("DIAGNOSIS: Docker Hub connectivity issue detected.")
            logs.append("SOLUTION: Check Docker Desktop proxy settings:")
            logs.append("1. Open Docker Desktop → Settings → Resources → Proxies")
            logs.append("2. Disable 'Manual proxy configuration' if enabled")
            logs.append("3. Click 'Apply & Restart'")
            logs.append("4. Try building again")
        elif "timeout" in error_text or "timeoutexpired" in error_text:
            logs.append("")
            logs.append("DIAGNOSIS: Build timeout detected.")
            logs.append("SOLUTION: Try building with lighter dependencies:")
            logs.append("1. Remove heavy packages like tensorflow, torch from requirements.txt")
            logs.append("2. Use --no-cache flag (already applied)")
            logs.append("3. Check your internet connection")
        elif "no space left on device" in error_text:
            logs.append("")
            logs.append("DIAGNOSIS: Insufficient disk space.")
            logs.append("SOLUTION: Free up disk space:")
            logs.append("1. Clean Docker: docker system prune -a")
            logs.append("2. Remove unused images: docker image prune -a")
            logs.append("3. Check available disk space")
        elif "requirements" in error_text and "error" in error_text:
            logs.append("")
            logs.append("DIAGNOSIS: Requirements.txt issues detected.")
            logs.append("SOLUTION: Fix requirements.txt:")
            logs.append("1. Remove duplicate package entries")
            logs.append("2. Fix conflicting version specifications")
            logs.append("3. Remove packages with Python version constraints if causing issues")
        elif "http: server gave http response to https client" in error_text:
            logs.append("")
            logs.append("DIAGNOSIS: Docker Hub connectivity issue detected.")
            logs.append("SOLUTION: Fix Docker Hub connectivity:")
            logs.append("1. Check Docker Desktop proxy settings:")
            logs.append("   - Open Docker Desktop → Settings → Resources → Proxies")
            logs.append("   - Disable 'Manual proxy configuration' if enabled")
            logs.append("   - Click 'Apply & Restart'")
            logs.append("2. Alternative: Use a different registry:")
            logs.append("   - Try: docker pull python:3.11-slim")
            logs.append("   - If that fails, check your internet connection")
            logs.append("3. Restart Docker Desktop completely")
            logs.append("4. WORKAROUND: Try building with Ubuntu base instead:")
            logs.append("   - Edit Dockerfile: change FROM python:3.11-slim to FROM ubuntu:22.04")
            logs.append("   - Add: RUN apt-get update && apt-get install -y python3 python3-pip")
    else:
        logger.info(f"Successfully built Docker image: {image_name}")
    
    return rc == 0, logs


def run_local_sanity_checks(summary: Dict[str, Any], repo_root: str) -> Dict[str, List[str]]:
    """Run basic sanity checks on the host (best effort)."""
    results: Dict[str, List[str]] = {}
    checks = summary.get("sanity_checks", {})
    is_windows = platform.system().lower().startswith("win")
    
    for eco, cmds in checks.items():
        out_lines: List[str] = []
        for cmd in cmds:
            # Clean up command for Windows
            clean_cmd = cmd.replace(" || true", "").strip()
            
            if is_windows:
                # For Windows, use cmd.exe and handle Python commands specially
                if clean_cmd.startswith("python"):
                    # Use python.exe directly on Windows
                    cmd_parts = clean_cmd.split()
                    if cmd_parts[0] == "python":
                        cmd_parts[0] = "python.exe"
                    rc, out, err = _run_cmd(cmd_parts, cwd=repo_root, timeout=300)
                else:
                    rc, out, err = _run_cmd(["cmd", "/c", clean_cmd], cwd=repo_root, timeout=300)
            else:
                rc, out, err = _run_cmd(["bash", "-lc", clean_cmd], cwd=repo_root, timeout=300)
            
            line = f"$ {clean_cmd}\n(rc={rc})\n{out}\n{err}"
            out_lines.append(line.strip())
            
            # Log the result
            if rc == 0:
                logger.info(f"Sanity check passed for {eco}: {clean_cmd}")
            else:
                logger.warning(f"Sanity check failed for {eco}: {clean_cmd} (rc={rc})")
        
        results[eco] = out_lines
    return results


def run_environment_setup(repo_root: str, image_name: Optional[str] = None, build: bool = False) -> ContainerBuildResult:
    """
    High-level orchestration: detect dependencies, generate artifacts, optionally build,
    and run sanity checks. Returns a structured result object.
    """
    result = ContainerBuildResult()
    result.suggested_commands = [
        "# Open in DevContainer:",
        "code . --folder-uri vscode-remote://dev-container+<container_id>/workspace",
        "# Or build and run locally:",
        f"docker build -t {image_name or 'my-image'} .",
        f"docker run --rm -it -v \"$PWD\":/workspace {image_name or 'my-image'} bash",
    ]
    
    try:
        # Validate repo root exists
        if not os.path.exists(repo_root):
            result.success = False
            result.error = f"Repository path does not exist: {repo_root}"
            return result
        
        # Detect dependencies
        summary = resolve_repo_dependencies(repo_root)
        detected_types = summary.get("types", [])
        logger.info("Detected ecosystems: %s", ", ".join(detected_types))
        
        if not detected_types:
            logger.warning("No supported project types detected in repository")

        # Generate artifacts
        dockerfile_path, devcontainer_path = write_artifacts(repo_root, summary, image_name=image_name)
        result.dockerfile_path = dockerfile_path
        result.devcontainer_path = devcontainer_path
        logger.info(f"Generated Dockerfile: {dockerfile_path}")
        logger.info(f"Generated DevContainer config: {devcontainer_path}")

        # Optionally build Docker image
        if build and image_name:
            logger.info(f"Building Docker image: {image_name}")
            ok, build_logs = build_image(repo_root, image_name)
            result.image_name = image_name
            result.build_logs = [l for l in build_logs if l]
            if not ok:
                result.success = False
                result.error = "Docker build failed"
                logger.error("Docker build failed")
            else:
                logger.info("Docker build completed successfully")

        # Run local sanity checks regardless of build
        logger.info("Running local sanity checks...")
        sanity = run_local_sanity_checks(summary, repo_root)
        result.sanity_logs = sanity

        # Check if any sanity checks failed
        sanity_failures = []
        for eco, logs in sanity.items():
            for log in logs:
                if "(rc=1)" in log or "(rc=2)" in log:
                    sanity_failures.append(f"{eco}: {log.split('$')[1].split('(rc=')[0].strip()}")
        
        if sanity_failures and not build:
            # Only warn if we didn't build (since build would have its own errors)
            logger.warning(f"Some sanity checks failed: {', '.join(sanity_failures)}")

        return result
        
    except Exception as e:
        result.success = False
        result.error = str(e)
        logger.exception(f"Fatal error during environment setup for {repo_root}")
        return result