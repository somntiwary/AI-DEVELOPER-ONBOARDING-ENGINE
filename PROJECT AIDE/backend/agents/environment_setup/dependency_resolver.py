"""
dependency_resolver.py

Detects project languages and parses dependency manifests:
 - requirements.txt (Python)
 - package.json (Node)
 - pom.xml (Maven/Java)

Produces a canonical summary describing:
 - detected languages & suggested runtimes
 - dependency lists (raw + some normalization)
 - simple "install commands" and sanity check commands
"""

from __future__ import annotations
import os
import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any

# Minimal helper: semantic version extraction
_VERSION_RE = re.compile(r"(\d+(?:\.\d+){0,2})")


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def detect_project_types(repo_root: str) -> List[str]:
    """
    Detect which ecosystems are present in the repository.
    Returns list of detected languages/frameworks: e.g. ["python", "node", "java"]
    """
    types = []
    if os.path.exists(os.path.join(repo_root, "requirements.txt")) or any(
        f.endswith(".py") for _, _, files in os.walk(repo_root) for f in files
    ):
        types.append("python")
    if os.path.exists(os.path.join(repo_root, "package.json")):
        types.append("node")
    if os.path.exists(os.path.join(repo_root, "pom.xml")):
        types.append("java")
    # Add heuristics for other ecosystems later (go.mod, Cargo.toml, etc.)
    return types


def parse_requirements_txt(path: str) -> List[str]:
    """
    Read requirements.txt and return cleaned dependency lines.
    Keeps comments that provide hints but strips inline comments by default.
    """
    lines = []
    raw = _read_text(path)
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        # remove inline comments (naive)
        s = s.split("#", 1)[0].strip()
        if s:
            lines.append(s)
    return lines


def parse_package_json(path: str) -> Dict[str, Any]:
    """
    Parse package.json and return dependencies and devDependencies.
    """
    try:
        txt = _read_text(path)
        obj = json.loads(txt)
        deps = obj.get("dependencies", {}) or {}
        dev = obj.get("devDependencies", {}) or {}
        scripts = obj.get("scripts", {}) or {}
        engines = obj.get("engines", {}) or {}
        return {"dependencies": deps, "devDependencies": dev, "scripts": scripts, "engines": engines}
    except Exception:
        return {"dependencies": {}, "devDependencies": {}, "scripts": {}, "engines": {}}


def parse_pom_xml(path: str) -> Dict[str, Any]:
    """
    Very lightweight parsing of pom.xml to extract dependencies and java version.
    Not a full Maven model parser, but enough for environment inference.
    """
    data = {"dependencies": [], "java_version": None}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Helper to find tags ignoring namespace
        def findall_local(elem, name):
            return [c for c in elem.findall(".//") if c.tag.endswith(name)]
        # Extract dependencies: groupId:artifactId:version
        deps = []
        for dep in root.findall(".//dependency"):
            group = dep.find("groupId")
            artifact = dep.find("artifactId")
            version = dep.find("version")
            g = group.text.strip() if group is not None and group.text else ""
            a = artifact.text.strip() if artifact is not None and artifact.text else ""
            v = version.text.strip() if version is not None and version.text else ""
            deps.append({"groupId": g, "artifactId": a, "version": v})
        data["dependencies"] = deps
        # Java version: check maven-compiler-plugin or properties -> maven.compiler.target / java.version
        props = {}
        for prop in root.findall(".//properties/*"):
            tag = prop.tag
            name = tag.split("}")[-1]
            if prop.text:
                props[name] = prop.text.strip()
        jv = props.get("maven.compiler.target") or props.get("java.version") or props.get("maven.compiler.release")
        if jv:
            data["java_version"] = jv
    except Exception:
        # Keep data defaults
        pass
    return data


def suggest_python_runtime(reqs: List[str]) -> Optional[str]:
    """
    Try to infer a reasonable Python runtime version from requirements content.
    This is heuristic-based: looks for 'python_version' markers or package versions hinting at py3.8+ etc.
    """
    # If requirements contains package markers like "python>=3.8" (rare), pick that
    for r in reqs:
        if "python" in r.lower() and (">=" in r or "==" in r or "<=" in r):
            m = _VERSION_RE.search(r)
            if m:
                return m.group(1)
    # Common high-level heuristic: if packages require modern pandas/pydantic versions -> suggest 3.8+
    for r in reqs:
        lower = r.lower()
        if any(x in lower for x in ["pydantic", "pandas", "fastapi", "sqlalchemy"]):
            return "3.9"
    # default
    return "3.8"


def suggest_node_runtime(engines_field: Dict[str, Any]) -> str:
    """
    If package.json contains "engines.node", return it; otherwise default to recent LTS.
    """
    node_spec = engines_field.get("node")
    if node_spec:
        # extract first version token
        m = _VERSION_RE.search(node_spec)
        if m:
            return m.group(1)
    return "18"  # conservative LTS


def build_dependency_summary(repo_root: str) -> Dict[str, Any]:
    """
    Scans the repository root for known manifests and returns a structured summary:
    {
      "types": ["python", "node"],
      "python": {"requirements": [...], "suggested_runtime": "3.9", "install_cmd": "..."},
      "node": {...},
      "java": {...}
    }
    """
    summary: Dict[str, Any] = {"types": []}
    types = detect_project_types(repo_root)
    summary["types"] = types

    if "python" in types:
        req_path = os.path.join(repo_root, "requirements.txt")
        reqs = parse_requirements_txt(req_path) if os.path.exists(req_path) else []
        summary["python"] = {
            "requirements_file": req_path if os.path.exists(req_path) else None,
            "requirements": reqs,
            "suggested_runtime": suggest_python_runtime(reqs),
            "install_command": "python -m pip install -r requirements.txt" if reqs else "python -m pip install -r requirements.txt (no requirements found)"
        }

    if "node" in types:
        pkg_path = os.path.join(repo_root, "package.json")
        pkg = parse_package_json(pkg_path) if os.path.exists(pkg_path) else {}
        suggested_node = suggest_node_runtime(pkg.get("engines", {}))
        summary["node"] = {
            "package_json": pkg_path if os.path.exists(pkg_path) else None,
            "dependencies": pkg.get("dependencies", {}),
            "devDependencies": pkg.get("devDependencies", {}),
            "scripts": pkg.get("scripts", {}),
            "suggested_runtime": suggested_node,
            "install_command": "npm install"
        }

    if "java" in types:
        pom_path = os.path.join(repo_root, "pom.xml")
        pom = parse_pom_xml(pom_path) if os.path.exists(pom_path) else {}
        summary["java"] = {
            "pom_xml": pom_path if os.path.exists(pom_path) else None,
            "dependencies": pom.get("dependencies", []),
            "suggested_runtime": pom.get("java_version") or "11",
            "install_command": "mvn -B dependency:resolve"
        }

    return summary


def get_sanity_checks(summary: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Produce basic "sanity check" commands for each detected ecosystem.
    These are suggestions to validate the environment after provisioning.
    """
    checks: Dict[str, List[str]] = {}
    if "python" in summary.get("types", []):
        checks["python"] = [
            "python -V",
            "python -m pip --version",
            # If tests present in repo, we might want to run pytest -q (ignore failures in runner)
            "python -m pytest -q"
        ]
    if "node" in summary.get("types", []):
        checks["node"] = [
            "node -v",
            "npm -v",
            "npm test --silent"
        ]
    if "java" in summary.get("types", []):
        checks["java"] = [
            "java -version",
            "mvn -v",
            "mvn -DskipTests=false test"
        ]
    return checks


# Convenient top-level function to use in the pipeline
def resolve_repo_dependencies(repo_root: str) -> Dict[str, Any]:
    """
    Main entry: build dependency summary and include recommended sanity checks.
    """
    summary = build_dependency_summary(repo_root)
    summary["sanity_checks"] = get_sanity_checks(summary)
    return summary


# If run as script, print a summary for local debugging
if __name__ == "__main__":
    import argparse, pprint
    p = argparse.ArgumentParser()
    p.add_argument("repo_root", help="Path to repository root")
    args = p.parse_args()
    res = resolve_repo_dependencies(args.repo_root)
    pprint.pprint(res, compact=True, width=120)
