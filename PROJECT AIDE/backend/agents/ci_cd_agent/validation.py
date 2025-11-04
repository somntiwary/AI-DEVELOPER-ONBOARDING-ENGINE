"""
validation.py
--------------
CI/CD Validation Module for AIDE’s CI/CD Agent.

Responsibilities:
- Validate CI/CD configurations (GitHub Actions, Jenkins, etc.)
- Simulate or test-run pipelines in isolated environments
- Detect common CI/CD misconfigurations or build issues
- Provide AI/RAG-based contextual fix recommendations
"""

import os
import re
import subprocess
import tempfile
import yaml
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Optional integration hook for your LangChain + Weaviate RAG setup
def provide_context_help(text: str) -> str:
    """
    Generates AI-based explanation or fix suggestions.
    Replace this with your real LLM or RAG pipeline call.
    """
    return f"(AI Insight) Suggestion: {text}"


# ---------------------------------------------------------------------
# Validation Utilities
# ---------------------------------------------------------------------
class CIValidator:
    """
    Validates CI/CD configurations for GitHub Actions, Jenkins, and others.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.report: Dict[str, Any] = {"repo": repo_path, "timestamp": datetime.now().isoformat()}

    # -------------------------------
    # 1. Config Detection
    # -------------------------------
    def detect_configs(self) -> Dict[str, str]:
        """Detect known CI/CD configuration files."""
        configs = {}
        possible_files = {
            "github": os.path.join(self.repo_path, ".github", "workflows"),
            "jenkins": os.path.join(self.repo_path, "Jenkinsfile"),
            "gitlab": os.path.join(self.repo_path, ".gitlab-ci.yml"),
            "docker": os.path.join(self.repo_path, "Dockerfile")
        }

        for name, path in possible_files.items():
            if os.path.isdir(path):
                configs[name] = f"Directory: {path}"
            elif os.path.isfile(path):
                configs[name] = path

        self.report["detected_configs"] = configs
        return configs

    # -------------------------------
    # 2. YAML Validation
    # -------------------------------
    def validate_yaml_files(self, workflow_dir: str) -> List[Dict[str, Any]]:
        """Validate all YAML workflow files in .github/workflows."""
        results = []
        if not os.path.isdir(workflow_dir):
            return results

        for file in os.listdir(workflow_dir):
            if not file.endswith((".yml", ".yaml")):
                continue
            file_path = os.path.join(workflow_dir, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
                results.append({"file": file, "status": "valid"})
            except yaml.YAMLError as e:
                results.append({"file": file, "status": "invalid", "error": str(e)})

        self.report["yaml_validation"] = results
        return results

    # -------------------------------
    # 3. Environment Validation
    # -------------------------------
    def run_environment_sanity(self) -> Dict[str, Any]:
        """
        Simulates environment setup (install deps, run tests) in a temp sandbox.
        """
        temp_dir = tempfile.mkdtemp(prefix="ci_validate_")
        requirements = os.path.join(self.repo_path, "requirements.txt")

        env_report = {"temp_dir": temp_dir, "status": "ok", "checks": []}

        if os.path.exists(requirements):
            try:
                result = subprocess.run(
                    ["python", "-m", "pip", "install", "-r", requirements, "--dry-run"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    env_report["status"] = "warning"
                    env_report["checks"].append({
                        "check": "dependency_installation",
                        "status": "failed",
                        "error": result.stderr
                    })
                else:
                    env_report["checks"].append({
                        "check": "dependency_installation",
                        "status": "passed"
                    })
            except Exception as e:
                env_report["status"] = "error"
                env_report["checks"].append({
                    "check": "dependency_installation",
                    "status": "error",
                    "error": str(e)
                })
        else:
            env_report["checks"].append({
                "check": "requirements.txt",
                "status": "missing"
            })

        self.report["environment_validation"] = env_report
        return env_report

    # -------------------------------
    # 4. Common CI/CD Anti-Patterns
    # -------------------------------
    def detect_common_issues(self) -> List[Dict[str, Any]]:
        """Detect common misconfigurations and performance issues with detailed analysis."""
        issues = []
        gitignore = os.path.join(self.repo_path, ".gitignore")

        if not os.path.exists(gitignore):
            issues.append({
                "type": "missing_file",
                "severity": "medium",
                "file": ".gitignore",
                "message": "Missing .gitignore file",
                "description": "May cause unnecessary build context and expose sensitive files",
                "fix": "Create a .gitignore file with appropriate patterns for your project"
            })

        dockerfile = os.path.join(self.repo_path, "Dockerfile")
        if os.path.exists(dockerfile):
            try:
                with open(dockerfile, "r", encoding="utf-8") as f:
                    docker_content = f.read()
                    docker_lower = docker_content.lower()
                    
                    if "latest" in docker_lower:
                        issues.append({
                            "type": "docker_best_practice",
                            "severity": "high",
                            "file": "Dockerfile",
                            "message": "Using 'latest' tag in Dockerfile",
                            "description": "Using 'latest' tag reduces reproducibility and can cause unexpected behavior",
                            "fix": "Use specific version tags (e.g., 'python:3.11-slim' instead of 'python:latest')"
                        })
                    
                    if "apt-get upgrade" in docker_lower:
                        issues.append({
                            "type": "docker_best_practice",
                            "severity": "high",
                            "file": "Dockerfile",
                            "message": "Using 'apt-get upgrade' in Dockerfile",
                            "description": "Can cause instability and unpredictable builds",
                            "fix": "Use specific package versions or pin package lists"
                        })
                    
                    if "root" in docker_lower and "user" not in docker_lower:
                        issues.append({
                            "type": "security",
                            "severity": "medium",
                            "file": "Dockerfile",
                            "message": "Running as root user",
                            "description": "Running containers as root can pose security risks",
                            "fix": "Add 'USER' directive to run as non-root user"
                        })
            except Exception as e:
                issues.append({
                    "type": "file_error",
                    "severity": "low",
                    "file": "Dockerfile",
                    "message": f"Error reading Dockerfile: {str(e)}",
                    "description": "Could not analyze Dockerfile for best practices",
                    "fix": "Check file permissions and encoding"
                })

        workflow_dir = os.path.join(self.repo_path, ".github", "workflows")
        if os.path.isdir(workflow_dir):
            for file in os.listdir(workflow_dir):
                if file.endswith((".yml", ".yaml")):
                    try:
                        file_path = os.path.join(workflow_dir, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            content_lower = content.lower()
                            
                            if "sudo" in content_lower:
                                issues.append({
                                    "type": "github_actions_best_practice",
                                    "severity": "medium",
                                    "file": file,
                                    "message": "Using 'sudo' in GitHub Actions",
                                    "description": "May break sandboxing and is generally not recommended",
                                    "fix": "Remove sudo commands or use appropriate GitHub Actions"
                                })
                            
                            if "runs-on: self-hosted" in content_lower:
                                issues.append({
                                    "type": "security",
                                    "severity": "high",
                                    "file": file,
                                    "message": "Using self-hosted runners",
                                    "description": "Self-hosted runners may introduce security risks",
                                    "fix": "Use GitHub-hosted runners when possible, or ensure proper security measures"
                                })
                            
                            if "secrets" in content_lower and "env:" not in content_lower:
                                issues.append({
                                    "type": "security",
                                    "severity": "high",
                                    "file": file,
                                    "message": "Using secrets without proper environment setup",
                                    "description": "Secrets should be properly mapped to environment variables",
                                    "fix": "Use 'env:' section to map secrets to environment variables"
                                })
                    except Exception as e:
                        issues.append({
                            "type": "file_error",
                            "severity": "low",
                            "file": file,
                            "message": f"Error reading workflow file: {str(e)}",
                            "description": "Could not analyze workflow file for best practices",
                            "fix": "Check file permissions and YAML syntax"
                        })

        # Check for common CI/CD anti-patterns
        package_files = ["package.json", "requirements.txt", "Pipfile", "poetry.lock", "yarn.lock"]
        found_package_files = [f for f in package_files if os.path.exists(os.path.join(self.repo_path, f))]
        
        if not found_package_files:
            issues.append({
                "type": "missing_dependencies",
                "severity": "medium",
                "file": "dependencies",
                "message": "No dependency management files found",
                "description": "Project lacks proper dependency management",
                "fix": "Add appropriate dependency file (requirements.txt, package.json, etc.)"
            })

        self.report["common_issues"] = issues
        return issues

    # -------------------------------
    # 5. AI-Based Diagnosis
    # -------------------------------
    def ai_diagnose(self) -> Dict[str, Any]:
        """
        Generate an AI-based summary or fix recommendations for detected issues.
        """
        issues = self.report.get("common_issues", [])
        if not issues:
            return {
                "status": "clean",
                "message": "No critical CI/CD issues detected.",
                "recommendations": []
            }

        # Categorize issues by severity
        high_severity = [issue for issue in issues if issue.get("severity") == "high"]
        medium_severity = [issue for issue in issues if issue.get("severity") == "medium"]
        low_severity = [issue for issue in issues if issue.get("severity") == "low"]

        # Generate recommendations
        recommendations = []
        for issue in high_severity:
            recommendations.append({
                "priority": "urgent",
                "issue": issue["message"],
                "file": issue["file"],
                "fix": issue["fix"],
                "ai_suggestion": provide_context_help(f"High priority fix for {issue['message']}: {issue['description']}")
            })

        for issue in medium_severity:
            recommendations.append({
                "priority": "important",
                "issue": issue["message"],
                "file": issue["file"],
                "fix": issue["fix"],
                "ai_suggestion": provide_context_help(f"Medium priority improvement for {issue['message']}: {issue['description']}")
            })

        for issue in low_severity:
            recommendations.append({
                "priority": "optional",
                "issue": issue["message"],
                "file": issue["file"],
                "fix": issue["fix"],
                "ai_suggestion": provide_context_help(f"Optional enhancement for {issue['message']}: {issue['description']}")
            })

        return {
            "status": "issues_found",
            "message": f"Found {len(issues)} issues: {len(high_severity)} high, {len(medium_severity)} medium, {len(low_severity)} low priority",
            "summary": {
                "total_issues": len(issues),
                "high_severity": len(high_severity),
                "medium_severity": len(medium_severity),
                "low_severity": len(low_severity)
            },
            "recommendations": recommendations
        }

    # -------------------------------
    # 6. Run Full Validation
    # -------------------------------
    def run_full_validation(self) -> Dict[str, Any]:
        """Run all checks sequentially and return final report."""
        print("Starting CI/CD validation...")
        self.detect_configs()
        workflow_dir = os.path.join(self.repo_path, ".github", "workflows")
        self.validate_yaml_files(workflow_dir)
        self.run_environment_sanity()
        self.detect_common_issues()
        self.report["ai_analysis"] = self.ai_diagnose()
        self.report["status"] = "completed"
        print("Validation complete.")
        return self.report


# ---------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------
if __name__ == "__main__":
    repo_path = os.getcwd()  # or provide a path to your project
    validator = CIValidator(repo_path)
    result = validator.run_full_validation()
    print(json.dumps(result, indent=2))
