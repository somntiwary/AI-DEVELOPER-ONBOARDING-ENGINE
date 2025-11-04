# ===========================================
# path_generator.py
# Dynamic Onboarding Path Generator
# Integrates Phase 1 (Repo Analysis), Phase 2 (Environment Setup), Phase 3 (Documentation)
# ===========================================

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from agents.repo_analysis.analysis import analyze_repository
    from agents.environment_setup.dependency_resolver import resolve_repo_dependencies
    from agents.environment_setup.runtime_detector import detect_runtimes
    from agents.documentation.doc_generator import DocumentationAgent
except ImportError:
    # Allow running when executed as a script
    import sys
    from pathlib import Path as _Path
    _BACKEND_DIR = _Path(__file__).parent.parent
    _PROJECT_ROOT = _BACKEND_DIR.parent
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from agents.repo_analysis.analysis import analyze_repository
    from agents.environment_setup.dependency_resolver import resolve_repo_dependencies
    from agents.environment_setup.runtime_detector import detect_runtimes
    from agents.documentation.doc_generator import DocumentationAgent

class PathGenerator:
    """
    Generates an intelligent, ordered onboarding path
    for new developers or AI agents based on project type.
    Integrates data from all three phases for comprehensive walkthroughs.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.project_type = self.detect_project_type()
        self.steps: List[Dict[str, Any]] = []
        
        # Phase integration data
        self.repo_analysis = None
        self.environment_data = None
        self.documentation_data = None

    # ----------------------------------------------------
    # STEP 1: Detect project type based on files present
    # ----------------------------------------------------
    def detect_project_type(self) -> str:
        files = [f.name.lower() for f in self.project_path.iterdir() if f.is_file()]

        if "requirements.txt" in files or any(f.endswith(".py") for f in files):
            return "python"
        elif "package.json" in files:
            return "node"
        elif any(f.endswith(".java") for f in files) or "pom.xml" in files:
            return "java"
        else:
            return "unknown"

    # ----------------------------------------------------
    # STEP 2: Initialize comprehensive onboarding with all phases
    # ----------------------------------------------------
    def initialize_comprehensive_onboarding(self) -> Dict[str, Any]:
        """
        Step 1: Onboarding Initialization
        - Detect repo type using Phase 1 metadata
        - Fetch environment requirements from Phase 2
        - Load documentation & guides from Phase 3
        """
        print(f"🔍 Initializing comprehensive onboarding for: {self.project_path}")
        
        # Phase 1: Repository Analysis
        print("📊 Phase 1: Analyzing repository structure...")
        try:
            # Note: analyze_repository expects a repo_url, but we have a local path
            # For now, we'll create a mock analysis based on the local project
            self.repo_analysis = self._analyze_local_repository()
            print(f"✅ Repository analysis complete: {len(self.repo_analysis.get('components', []))} components found")
        except Exception as e:
            print(f"⚠️ Repository analysis failed: {e}")
            self.repo_analysis = {"components": [], "structure": {}}
        
        # Phase 2: Environment Requirements
        print("🔧 Phase 2: Detecting environment requirements...")
        try:
            runtime_info = detect_runtimes(str(self.project_path))
            dependencies = resolve_repo_dependencies(str(self.project_path))
            self.environment_data = {
                "runtime": runtime_info,
                "dependencies": dependencies
            }
            print(f"✅ Environment analysis complete: {self.project_type} project detected")
        except Exception as e:
            print(f"⚠️ Environment analysis failed: {e}")
            self.environment_data = {"runtime": {}, "dependencies": {}}
        
        # Phase 3: Documentation & Guides
        print("📚 Phase 3: Loading documentation and guides...")
        try:
            doc_agent = DocumentationAgent(base_path=self.project_path)
            self.documentation_data = {
                "docs": doc_agent.collect_docs(),
                "readme": doc_agent.generate_readme() if (self.project_path / "README.md").exists() else None
            }
            print(f"✅ Documentation analysis complete: {len(self.documentation_data['docs'])} docs found")
        except Exception as e:
            print(f"⚠️ Documentation analysis failed: {e}")
            self.documentation_data = {"docs": [], "readme": None}
        
        return {
            "repo_analysis": self.repo_analysis,
            "environment_data": self.environment_data,
            "documentation_data": self.documentation_data,
            "project_type": self.project_type
        }

    def _analyze_local_repository(self) -> Dict[str, Any]:
        """Analyze local repository structure"""
        components = []
        
        # Analyze Python files
        for py_file in self.project_path.rglob("*.py"):
            if py_file.is_file() and not any(part.startswith('.') for part in py_file.parts):
                components.append({
                    "name": py_file.name,
                    "path": str(py_file.relative_to(self.project_path)),
                    "type": "python_file",
                    "size": py_file.stat().st_size
                })
        
        # Analyze configuration files
        config_files = ["requirements.txt", "setup.py", "pyproject.toml", "package.json", "pom.xml"]
        for config_file in config_files:
            config_path = self.project_path / config_file
            if config_path.exists():
                components.append({
                    "name": config_file,
                    "path": str(config_path.relative_to(self.project_path)),
                    "type": "config_file",
                    "size": config_path.stat().st_size
                })
        
        return {
            "components": components,
            "structure": {
                "total_files": len(components),
                "python_files": len([c for c in components if c["type"] == "python_file"]),
                "config_files": len([c for c in components if c["type"] == "config_file"])
            }
        }

    # ----------------------------------------------------
    # STEP 3: Generate comprehensive onboarding flow
    # ----------------------------------------------------
    def generate_comprehensive_steps(self) -> List[Dict[str, Any]]:
        """
        Step 2: Generate Onboarding Flow
        Creates custom onboarding flow with detailed steps, commands, and explanations
        """
        if self.project_type == "python":
            self.steps = self._generate_comprehensive_python_steps()
        elif self.project_type == "node":
            self.steps = self._generate_comprehensive_node_steps()
        elif self.project_type == "java":
            self.steps = self._generate_comprehensive_java_steps()
        else:
            self.steps = self._generate_comprehensive_generic_steps()

        return self.steps

    # ----------------------------------------------------
    # STEP 4: Generate onboarding steps dynamically (legacy method)
    # ----------------------------------------------------
    def generate_steps(self) -> List[Dict[str, Any]]:
        """Legacy method for backward compatibility"""
        return self.generate_comprehensive_steps()

    # ----------------------------------------------------
    # STEP 5: Comprehensive Python onboarding flow
    # ----------------------------------------------------
    def _generate_comprehensive_python_steps(self) -> List[Dict[str, Any]]:
        """
        Generate comprehensive Python onboarding steps with detailed explanations,
        related files, and context from all three phases.
        """
        steps = []
        
        # Step 1: Clone Repository
        steps.append({
            "step_no": 1,
            "title": "Clone Repository",
            "description": "Get the project source code locally",
            "command": f"git clone <repository_url> {self.project_path.name}",
            "related_files": ["README.md", ".gitignore"],
            "explanation": "This downloads the complete project source code to your local machine. The repository contains all the code, documentation, and configuration files needed to run the project.",
            "prerequisites": ["Git installed", "Repository access"],
            "success_criteria": "Project directory created with source files",
            "troubleshooting": "If clone fails, check repository URL and access permissions"
        })
        
        # Step 2: Navigate to Project Directory
        steps.append({
            "step_no": 2,
            "title": "Navigate to Project Directory",
            "description": "Move into the project folder",
            "command": f"cd {self.project_path.name}",
            "related_files": ["All project files"],
            "explanation": "Change your current directory to the project folder so you can run commands from the correct location.",
            "prerequisites": ["Project cloned successfully"],
            "success_criteria": "Current directory is the project root",
            "troubleshooting": "Use 'pwd' (Linux/Mac) or 'cd' (Windows) to verify current directory"
        })
        
        # Step 3: Create Virtual Environment
        steps.append({
            "step_no": 3,
            "title": "Create Virtual Environment",
            "description": "Create an isolated Python environment for dependencies",
            "command": "python -m venv venv",
            "related_files": ["requirements.txt", "pyproject.toml", "Pipfile"],
            "explanation": "Virtual environments prevent dependency conflicts by creating an isolated Python environment. This ensures the project's dependencies don't interfere with other projects or your system Python.",
            "prerequisites": ["Python installed", "Project directory"],
            "success_criteria": "venv directory created",
            "troubleshooting": "If 'python' not found, try 'python3' or install Python"
        })
        
        # Step 4: Activate Virtual Environment
        steps.append({
            "step_no": 4,
            "title": "Activate Virtual Environment",
            "description": "Activate the virtual environment to use project dependencies",
            "command": "venv\\Scripts\\activate" if os.name == "nt" else "source venv/bin/activate",
            "related_files": ["venv/"],
            "explanation": "Activation switches your shell to use the virtual environment's Python and packages. You'll see '(venv)' in your prompt when active.",
            "prerequisites": ["Virtual environment created"],
            "success_criteria": "Prompt shows '(venv)' prefix",
            "troubleshooting": "On Windows, use 'venv\\Scripts\\activate.bat' if PowerShell fails"
        })
        
        # Step 5: Install Dependencies
        steps.append({
            "step_no": 5,
            "title": "Install Dependencies",
            "description": "Install all required Python packages",
            "command": "pip install -r requirements.txt",
            "related_files": ["requirements.txt", "setup.py", "pyproject.toml"],
            "explanation": "This installs all the Python packages the project needs to run. Each package is installed in the virtual environment, keeping your system clean.",
            "prerequisites": ["Virtual environment activated", "requirements.txt exists"],
            "success_criteria": "All packages installed without errors",
            "troubleshooting": "If installation fails, check internet connection and package versions"
        })
        
        # Step 6: Set Up Environment Variables
        steps.append({
            "step_no": 6,
            "title": "Configure Environment Variables",
            "description": "Set up required environment variables and configuration",
            "command": "cp .env.example .env" if (self.project_path / ".env.example").exists() else "echo 'No .env.example found'",
            "related_files": [".env.example", ".env", "config.py"],
            "explanation": "Environment variables store configuration like database URLs, API keys, and other settings. Copy the example file and customize it for your setup.",
            "prerequisites": ["Project dependencies installed"],
            "success_criteria": ".env file created and configured",
            "troubleshooting": "Check .env.example for required variables and documentation"
        })
        
        # Step 7: Database Setup (if applicable)
        if self._has_database_requirements():
            steps.append({
                "step_no": 7,
                "title": "Set Up Database",
                "description": "Initialize and configure the database",
                "command": "alembic upgrade head" if (self.project_path / "alembic.ini").exists() else "python manage.py migrate",
                "related_files": ["alembic.ini", "alembic/", "models.py", "migrations/"],
                "explanation": "Database migrations create the necessary tables and schema for the application. This step ensures your database matches the application's requirements.",
                "prerequisites": ["Environment variables configured", "Database server running"],
                "success_criteria": "Database schema created successfully",
                "troubleshooting": "Ensure database server is running and connection details are correct"
            })
        
        # Step 8: Run Tests
        steps.append({
            "step_no": 8 if not self._has_database_requirements() else 8,
            "title": "Run Tests",
            "description": "Execute the test suite to verify everything works",
            "command": "pytest -v" if (self.project_path / "pytest.ini").exists() else "python -m pytest",
            "related_files": ["tests/", "pytest.ini", "conftest.py"],
            "explanation": "Tests verify that the application works correctly. Running tests helps catch issues early and ensures the setup is complete.",
            "prerequisites": ["All dependencies installed", "Database configured"],
            "success_criteria": "All tests pass",
            "troubleshooting": "Fix any failing tests before proceeding"
        })
        
        # Step 9: Start Development Server
        steps.append({
            "step_no": 9 if not self._has_database_requirements() else 9,
            "title": "Start Development Server",
            "description": "Launch the application server",
            "command": self._get_start_command(),
            "related_files": ["main.py", "app.py", "run.py", "manage.py"],
            "explanation": "The development server runs your application locally. You can now access it in your browser and start developing.",
            "prerequisites": ["All tests passing", "Environment configured"],
            "success_criteria": "Server starts without errors",
            "troubleshooting": "Check server logs for error messages and port availability"
        })
        
        # Step 10: Explore Project Structure
        steps.append({
            "step_no": 10 if not self._has_database_requirements() else 10,
            "title": "Explore Project Structure",
            "description": "Understand the codebase organization and key components",
            "command": "tree -I 'venv|__pycache__|*.pyc' ." if os.name != "nt" else "dir /s",
            "related_files": ["All project files"],
            "explanation": "Understanding the project structure helps you navigate the codebase and find relevant files when making changes.",
            "prerequisites": ["Server running successfully"],
            "success_criteria": "Familiar with project layout",
            "troubleshooting": "Use 'ls -la' (Linux/Mac) or 'dir' (Windows) to explore directories"
        })
        
        return steps

    def _has_database_requirements(self) -> bool:
        """Check if project has database requirements"""
        db_files = ["alembic.ini", "models.py", "database.py", "db.py"]
        return any((self.project_path / f).exists() for f in db_files)
    
    def _get_start_command(self) -> str:
        """Get the appropriate start command based on project structure"""
        if (self.project_path / "main.py").exists():
            return "python main.py"
        elif (self.project_path / "app.py").exists():
            return "python app.py"
        elif (self.project_path / "manage.py").exists():
            return "python manage.py runserver"
        else:
            return "uvicorn main:app --reload --port 8000"

    # ----------------------------------------------------
    # STEP 6: Legacy Python onboarding flow
    # ----------------------------------------------------
    def _generate_python_steps(self) -> List[Dict[str, str]]:
        return [
            {
                "step": 1,
                "title": "Clone Repository",
                "command": f"git clone <your_repo_url> {self.project_path.name}",
                "explanation": "Fetch the project source code locally."
            },
            {
                "step": 2,
                "title": "Create Virtual Environment",
                "command": "python -m venv venv",
                "explanation": "Create an isolated Python environment for dependencies."
            },
            {
                "step": 3,
                "title": "Activate Virtual Environment",
                "command": "venv\\Scripts\\activate" if os.name == "nt" else "source venv/bin/activate",
                "explanation": "Activate the environment so Python uses local packages."
            },
            {
                "step": 4,
                "title": "Install Dependencies",
                "command": "pip install -r requirements.txt",
                "explanation": "Install all Python dependencies listed in requirements.txt."
            },
            {
                "step": 5,
                "title": "Run Database Migrations (if any)",
                "command": "alembic upgrade head",
                "explanation": "Apply database schema updates if Alembic is used."
            },
            {
                "step": 6,
                "title": "Start Backend Server",
                "command": "uvicorn main:app --reload --port 8081",
                "explanation": "Launch the FastAPI backend server for development."
            },
            {
                "step": 7,
                "title": "Run Tests",
                "command": "pytest -q",
                "explanation": "Run unit tests to verify installation success."
            }
        ]

    # ----------------------------------------------------
    # STEP 4: Node.js onboarding flow
    # ----------------------------------------------------
    def _generate_node_steps(self) -> List[Dict[str, str]]:
        return [
            {
                "step": 1,
                "title": "Clone Repository",
                "command": f"git clone <your_repo_url> {self.project_path.name}",
                "explanation": "Download the Node.js project locally."
            },
            {
                "step": 2,
                "title": "Install Dependencies",
                "command": "npm install",
                "explanation": "Install all required Node.js packages."
            },
            {
                "step": 3,
                "title": "Set Environment Variables",
                "command": "cp .env.example .env",
                "explanation": "Copy and configure environment variables."
            },
            {
                "step": 4,
                "title": "Start Development Server",
                "command": "npm run dev",
                "explanation": "Run the backend or frontend development server."
            },
            {
                "step": 5,
                "title": "Run Tests",
                "command": "npm test",
                "explanation": "Execute all automated tests."
            }
        ]

    # ----------------------------------------------------
    # STEP 5: Java onboarding flow
    # ----------------------------------------------------
    def _generate_java_steps(self) -> List[Dict[str, str]]:
        return [
            {
                "step": 1,
                "title": "Clone Repository",
                "command": f"git clone <your_repo_url> {self.project_path.name}",
                "explanation": "Fetch the Java project repository locally."
            },
            {
                "step": 2,
                "title": "Build Project",
                "command": "mvn clean install" if (self.project_path / "pom.xml").exists() else "gradle build",
                "explanation": "Compile source files and download dependencies."
            },
            {
                "step": 3,
                "title": "Run Application",
                "command": "java -jar target/<your_app>.jar",
                "explanation": "Start the compiled Java application."
            }
        ]

    # ----------------------------------------------------
    # STEP 6: Fallback generic steps
    # ----------------------------------------------------
    def _generate_generic_steps(self) -> List[Dict[str, str]]:
        return [
            {"step": 1, "title": "Clone Repository", "command": "git clone <repo_url>", "explanation": "Fetch source code."},
            {"step": 2, "title": "Inspect README", "command": "open README.md", "explanation": "Review instructions manually."},
        ]

    # ----------------------------------------------------
    # STEP 7: Export steps in structured format
    # ----------------------------------------------------
    def export_steps(self, output_file: str = "onboarding_steps.json") -> Path:
        import json
        output_path = self.project_path / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.steps, f, indent=4)
        return output_path


# ===========================================
# Example Local Test
# ===========================================
if __name__ == "__main__":
    path = input("Enter project path: ").strip()
    gen = PathGenerator(path)
    print(f"Detected project type: {gen.project_type}")
    steps = gen.generate_steps()
    for step in steps:
        print(f"\n[{step['step']}] {step['title']}")
        print(f"→ Command: {step['command']}")
        print(f"💡 {step['explanation']}")
