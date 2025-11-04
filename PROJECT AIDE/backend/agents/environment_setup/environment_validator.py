"""
environment_validator.py

Runs basic validation either inside a running container (if supported) or on the local environment.
"""

from __future__ import annotations
from typing import Dict, List
import os
import subprocess


def _run(cmd: List[str], cwd: str | None = None) -> Dict[str, str | int]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        return {"rc": proc.returncode, "out": proc.stdout or "", "err": proc.stderr or ""}
    except Exception as e:
        return {"rc": 1, "out": "", "err": str(e)}


class EnvironmentValidator:
    def validate_container(self, container_id: str) -> Dict[str, List[Dict[str, str | int]]]:
        """Best-effort validation by executing simple commands inside container via docker exec."""
        checks = [
            ["docker", "exec", container_id, "python", "-V"],
            ["docker", "exec", container_id, "node", "-v"],
            ["docker", "exec", container_id, "java", "-version"],
        ]
        results: List[Dict[str, str | int]] = []
        for c in checks:
            results.append(_run(c))
        return {"checks": results}

    def validate_local_environment(self, project_path: str) -> Dict[str, List[Dict[str, str | int]]]:
        """Run simple version checks locally as a quick smoke test."""
        checks = [
            ["python", "-V"],
            ["pip", "--version"],
            ["node", "-v"],
            ["npm", "-v"],
            ["java", "-version"],
        ]
        results: List[Dict[str, str | int]] = []
        for c in checks:
            results.append(_run(c, cwd=project_path))
        return {"checks": results}

# environment_validator.py
# Validates runtime and dependency consistency, ensuring environment setup works.

import os
import subprocess
from typing import Dict, List, Tuple


def run_command(cmd: List[str], cwd: str = None) -> Tuple[bool, str]:
    """Run a shell command safely and capture output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output.strip()
    except Exception as e:
        return False, str(e)


def validate_python_env(repo_path: str) -> Dict[str, str]:
    """Run sanity checks for Python environment."""
    checks = {}
    for cmd in [["python", "--version"], ["pip", "--version"], ["pytest", "--version"]]:
        ok, output = run_command(cmd, cwd=repo_path)
        checks[" ".join(cmd)] = "OK" if ok else f"FAIL: {output[:80]}"
    return checks


def validate_node_env(repo_path: str) -> Dict[str, str]:
    """Run sanity checks for Node.js environment."""
    checks = {}
    for cmd in [["node", "--version"], ["npm", "--version"], ["npm", "install", "--dry-run"]]:
        ok, output = run_command(cmd, cwd=repo_path)
        checks[" ".join(cmd)] = "OK" if ok else f"FAIL: {output[:80]}"
    return checks


def validate_java_env(repo_path: str) -> Dict[str, str]:
    """Run sanity checks for Java environment."""
    checks = {}
    for cmd in [["java", "-version"], ["javac", "-version"]]:
        ok, output = run_command(cmd, cwd=repo_path)
        checks[" ".join(cmd)] = "OK" if ok else f"FAIL: {output[:80]}"
    return checks


def validate_all_environments(repo_path: str, runtimes: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    Validate all detected environments.
    Args:
        repo_path: Path to project root
        runtimes: Detected runtimes from runtime_detector
    Returns:
        Dictionary with validation results.
    """
    results = {}
    if runtimes.get("python"):
        results["python"] = validate_python_env(repo_path)
    if runtimes.get("node"):
        results["node"] = validate_node_env(repo_path)
    if runtimes.get("java"):
        results["java"] = validate_java_env(repo_path)

    return results
