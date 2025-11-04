# runtime_detector.py
# Detects project runtime requirements based on files, config, or code content.

import os
import re
import json
import subprocess
from typing import Dict, Optional, List


def detect_python_version(repo_path: str) -> Optional[str]:
    """Detect Python version from requirements.txt or runtime files."""
    candidates = [
        os.path.join(repo_path, "runtime.txt"),
        os.path.join(repo_path, "Pipfile"),
        os.path.join(repo_path, "pyproject.toml"),
        os.path.join(repo_path, "requirements.txt"),
    ]

    for file_path in candidates:
        if not os.path.exists(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # runtime.txt format: python-3.10.4
            match = re.search(r"python[-=:\s]*([\d.]+)", content, re.IGNORECASE)
            if match:
                return match.group(1)
        except Exception:
            continue

    # fallback: check installed Python version
    try:
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        return result.stdout.strip().split()[-1]
    except Exception:
        return None


def detect_node_version(repo_path: str) -> Optional[str]:
    """Detect Node.js version from package.json or .nvmrc."""
    pkg_file = os.path.join(repo_path, "package.json")
    nvm_file = os.path.join(repo_path, ".nvmrc")

    if os.path.exists(nvm_file):
        with open(nvm_file, "r", encoding="utf-8") as f:
            return f.read().strip()

    if os.path.exists(pkg_file):
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            engines = data.get("engines", {})
            if "node" in engines:
                return engines["node"].replace(">=", "").strip()
        except Exception:
            pass

    # fallback: check installed node version
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        return result.stdout.strip().lstrip("v")
    except Exception:
        return None


def detect_java_version(repo_path: str) -> Optional[str]:
    """Detect Java version from pom.xml or gradle files."""
    for file_name in ["pom.xml", "build.gradle", "gradle.properties"]:
        file_path = os.path.join(repo_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                match = re.search(r"(1\.\d{1,2}|\d{2})", text)
                if match:
                    return match.group(1)

    # fallback: check installed java version
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        match = re.search(r'version "([\d._]+)"', result.stderr)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def detect_runtimes(repo_path: str) -> Dict[str, Optional[str]]:
    """Main detector entry point."""
    return {
        "python": detect_python_version(repo_path),
        "node": detect_node_version(repo_path),
        "java": detect_java_version(repo_path),
    }
