"""
jenkins_ci.py
-------------
Jenkins CI/CD integration for AIDE’s CI/CD Agent.
Provides:
  - Jenkinsfile parsing
  - Pipeline summary generation
  - Build trigger, status, and log retrieval
  - Optional LLM-based error explanations (integrates with RAG)
"""

import os
import re
import yaml
import json
import requests
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------
# Optional: LLM or RAG-based helper for context-aware explanations
# ---------------------------------------------------------------------
def provide_context_help(text: str) -> str:
    """
    Placeholder for integration with your existing LangChain + Weaviate setup.
    Use it to explain build steps or failure causes in plain English.
    """
    return f"(Contextual help) This step ensures: {text}"


# ---------------------------------------------------------------------
# Jenkins File Parser
# ---------------------------------------------------------------------
class JenkinsFileParser:
    """
    Parses Jenkinsfiles to extract stages, steps, and environment variables.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.jenkinsfile_path = os.path.join(repo_path, "Jenkinsfile")

    def load_file(self) -> Optional[str]:
        """Load Jenkinsfile content."""
        if not os.path.exists(self.jenkinsfile_path):
            print("ERROR: Jenkinsfile not found in repository.")
            return None
        with open(self.jenkinsfile_path, "r", encoding="utf-8") as f:
            return f.read()

    def parse_stages(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract pipeline stages and steps from Jenkinsfile.
        Supports both scripted and declarative syntax.
        """
        stages = []
        pattern = r"stage\s*\(['\"](.*?)['\"]\)\s*\{(.*?)\}"
        matches = re.findall(pattern, content, re.DOTALL)

        for stage_name, body in matches:
            steps = re.findall(r"sh\s+['\"](.*?)['\"]", body)
            env_vars = re.findall(r"environment\s*\{(.*?)\}", body, re.DOTALL)
            env_dict = {}
            if env_vars:
                for env_line in env_vars[0].split("\n"):
                    env_match = re.match(r"\s*(\w+)\s*=\s*['\"](.*?)['\"]", env_line.strip())
                    if env_match:
                        env_dict[env_match.group(1)] = env_match.group(2)

            stages.append({
                "stage": stage_name,
                "steps": steps,
                "environment": env_dict
            })
        return stages

    def summarize(self) -> Dict[str, Any]:
        """Return structured summary of Jenkinsfile."""
        content = self.load_file()
        if not content:
            return {"error": "No Jenkinsfile found"}

        stages = self.parse_stages(content)
        summary = {
            "pipeline_type": "Jenkins",
            "total_stages": len(stages),
            "stages": stages
        }
        return summary

    def explain_summary(self, summary: Dict[str, Any]) -> str:
        """Return a plain-English explanation of the Jenkins pipeline."""
        if "error" in summary:
            return summary["error"]

        explanation = [f"**Jenkins Pipeline Summary**"]
        explanation.append(f"Total stages: {summary['total_stages']}")

        for stage in summary["stages"]:
            explanation.append(f"\n**Stage:** {stage['stage']}")
            if stage["environment"]:
                explanation.append(f"   - Environment vars: {json.dumps(stage['environment'], indent=2)}")
            for cmd in stage["steps"]:
                explanation.append(f"   - Runs command: `{cmd}`")
                explanation.append(f"     -> {provide_context_help(cmd)}")

        return "\n".join(explanation)


# ---------------------------------------------------------------------
# Jenkins Server API Integration
# ---------------------------------------------------------------------
class JenkinsManager:
    """
    Manages Jenkins server interaction via REST API.
    """

    def __init__(self, base_url: str, username: str, api_token: str):
        """
        :param base_url: Jenkins server URL (e.g., http://localhost:8080)
        :param username: Jenkins username
        :param api_token: Jenkins API token (generate from Jenkins user settings)
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (username, api_token)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs in Jenkins."""
        url = f"{self.base_url}/api/json?tree=jobs[name,url,color]"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json().get("jobs", [])
        return []

    def trigger_job(self, job_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Trigger a Jenkins job (supports parameterized builds).
        """
        if params:
            url = f"{self.base_url}/job/{job_name}/buildWithParameters"
        else:
            url = f"{self.base_url}/job/{job_name}/build"

        response = self.session.post(url, params=params)
        if response.status_code in (200, 201):
            return {"status": "success", "message": f"Triggered job '{job_name}'"}
        return {"status": "error", "code": response.status_code, "details": response.text}

    def get_job_info(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Get job details."""
        url = f"{self.base_url}/job/{job_name}/api/json"
        response = self.session.get(url)
        return response.json() if response.status_code == 200 else None

    def get_build_status(self, job_name: str, build_number: int) -> Optional[str]:
        """Fetch build status."""
        url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json().get("result", "UNKNOWN")
        return None

    def get_build_logs(self, job_name: str, build_number: int) -> Optional[str]:
        """Fetch logs for a Jenkins build."""
        url = f"{self.base_url}/job/{job_name}/{build_number}/consoleText"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.text
        return None

    def diagnose_failure(self, logs: str) -> str:
        """
        Use heuristics + LLM to suggest fixes for failed builds.
        """
        error_lines = [line for line in logs.split("\n") if "error" in line.lower()]
        if not error_lines:
            return "No errors detected in logs."
        combined = "\n".join(error_lines[:10])
        return provide_context_help(f"Detected potential failure cause:\n{combined}")


# ---------------------------------------------------------------------
# Example standalone test
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Example: Parse local Jenkinsfile
    parser = JenkinsFileParser(repo_path=".")
    summary = parser.summarize()
    print(parser.explain_summary(summary))

    # Example: Connect to Jenkins server (optional)
    # manager = JenkinsManager(base_url="http://localhost:8080", username="admin", api_token="your_api_token_here")
    # print(manager.list_jobs())
    # print(manager.trigger_job("example-job"))
    # logs = manager.get_build_logs("example-job", 15)
    # print(manager.diagnose_failure(logs))
