"""
github_ci.py
------------
CI/CD Agent module for parsing, summarizing, validating, and triggering
GitHub Actions workflows (.github/workflows/*.yml).
"""

import os
import yaml
import requests
from typing import Dict, Any, List, Optional


class GitHubCISummarizer:
    """
    Parses and summarizes GitHub Actions YAML workflows.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.workflows_dir = os.path.join(repo_path, ".github", "workflows")

    def list_workflow_files(self) -> List[str]:
        """Return all workflow YAML files in the repo."""
        if not os.path.exists(self.workflows_dir):
            return []
        return [
            os.path.join(self.workflows_dir, f)
            for f in os.listdir(self.workflows_dir)
            if f.endswith((".yml", ".yaml"))
        ]

    def parse_workflow(self, path: str) -> Optional[Dict[str, Any]]:
        """Parse a single GitHub Actions workflow YAML file."""
        try:
            with open(path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"ERROR: Failed to parse {path}: {e}")
            return None

    def summarize_workflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize workflow into a human-readable structure.
        Example:
        {
          'name': 'CI Pipeline',
          'triggers': ['push', 'pull_request'],
          'jobs': [{'name': 'build', 'steps': [...]}, ...]
        }
        """
        name = data.get("name", "Unnamed Workflow")
        
        # Handle different trigger formats
        on_data = data.get("on", {})
        if isinstance(on_data, dict):
            triggers = list(on_data.keys())
        elif isinstance(on_data, str):
            triggers = [on_data]
        else:
            triggers = []
        
        jobs = []

        for job_name, job_content in data.get("jobs", {}).items():
            steps_summary = []
            for step in job_content.get("steps", []):
                # Ensure step is a dictionary
                if not isinstance(step, dict):
                    continue
                    
                desc = step.get("name", step.get("run", "Unnamed Step"))
                command = step.get("run", None)
                uses = step.get("uses", None)
                steps_summary.append({
                    "step_name": desc,
                    "command": command,
                    "uses": uses
                })

            jobs.append({
                "job_name": job_name,
                "runs_on": job_content.get("runs-on", "unknown"),
                "steps": steps_summary
            })

        return {
            "name": name,
            "triggers": triggers,
            "jobs": jobs
        }

    def explain_workflow(self, summary: Dict[str, Any]) -> str:
        """Generate a plain-English explanation of the workflow."""
        explanation = [f"**Workflow Name:** {summary['name']}"]

        if summary.get("triggers"):
            explanation.append(f"Triggered by: {', '.join(summary['triggers'])}")

        for job in summary.get("jobs", []):
            explanation.append(f"\n**Job:** {job['job_name']} (runs on {job['runs_on']})")
            for step in job["steps"]:
                if step["uses"]:
                    explanation.append(f"   - Uses: {step['uses']}")
                if step["command"]:
                    explanation.append(f"   - Runs command: `{step['command']}`")

        return "\n".join(explanation)

    def summarize_all(self) -> List[Dict[str, Any]]:
        """Parse and summarize all workflow files."""
        all_summaries = []
        for wf in self.list_workflow_files():
            data = self.parse_workflow(wf)
            if data:
                summary = self.summarize_workflow(data)
                all_summaries.append(summary)
        return all_summaries


# ------------------------------------------------------------------------
# GitHub API Integration for triggering / monitoring workflows
# ------------------------------------------------------------------------

class GitHubWorkflowManager:
    """
    Handles interaction with GitHub REST API to trigger and monitor workflows.
    """

    def __init__(self, repo: str, token: str):
        """
        :param repo: 'owner/repo_name'
        :param token: GitHub Personal Access Token
        """
        self.repo = repo
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        self.base_url = f"https://api.github.com/repos/{repo}"

    def list_workflows(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/actions/workflows"
        response = requests.get(url, headers=self.headers)
        return response.json().get("workflows", [])

    def trigger_workflow(self, workflow_file: str, branch: str = "main") -> Dict[str, Any]:
        """
        Dispatch a GitHub Actions workflow (requires `workflow_dispatch` trigger).
        """
        url = f"{self.base_url}/actions/workflows/{workflow_file}/dispatches"
        payload = {"ref": branch}
        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 204:
            return {"status": "success", "message": f"Triggered {workflow_file} on branch {branch}"}
        else:
            return {"status": "error", "code": response.status_code, "details": response.text}

    def get_latest_run(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest run details for a workflow."""
        url = f"{self.base_url}/actions/workflows/{workflow_id}/runs"
        response = requests.get(url, headers=self.headers)
        runs = response.json().get("workflow_runs", [])
        return runs[0] if runs else None

    def get_run_logs(self, run_id: int) -> Optional[str]:
        """Fetch logs for a workflow run."""
        url = f"{self.base_url}/actions/runs/{run_id}/logs"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.text
        return None


# ------------------------------------------------------------------------
# Example standalone test
# ------------------------------------------------------------------------

if __name__ == "__main__":
    # Example local parsing
    parser = GitHubCISummarizer(repo_path=".")
    summaries = parser.summarize_all()

    for s in summaries:
        print(parser.explain_workflow(s))

    # Example GitHub API usage (mock)
    # manager = GitHubWorkflowManager(repo="yourname/yourrepo", token="ghp_XXX")
    # print(manager.list_workflows())
    # print(manager.trigger_workflow("ci.yml", "main"))
