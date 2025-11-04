# ===========================================
# session_tracker.py
# Persistent Session Tracker for Onboarding Agent
# ===========================================

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

class SessionTracker:
    """
    Tracks walkthrough / onboarding progress for a specific user and project.
    Saves session data persistently in JSON files.
    """

    def __init__(self, project_path: str, user_id: Optional[str] = "default_user"):
        self.project_path = Path(project_path).resolve()
        self.user_id = user_id
        self.session_file = self.project_path / f".onboarding_session_{user_id}.json"
        self.session_data = self._load_session()

    # ----------------------------------------------------
    # Load existing session from file (if available)
    # ----------------------------------------------------
    def _load_session(self) -> Dict[str, Any]:
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Warning: Corrupted session file detected. Creating new session.")
        return {
            "user_id": self.user_id,
            "project": str(self.project_path),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": None,
            "completed_steps": [],
            "current_step": None,
            "total_steps": 0,
            "status": "not_started"
        }

    # ----------------------------------------------------
    # Save session state to disk
    # ----------------------------------------------------
    def _save_session(self):
        self.session_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(self.session_data, f, indent=4)

    # ----------------------------------------------------
    # Initialize a new onboarding session
    # ----------------------------------------------------
    def initialize(self, steps: List[Dict[str, Any]]):
        self.session_data["total_steps"] = len(steps)
        self.session_data["completed_steps"] = []
        self.session_data["current_step"] = 1 if steps else None
        self.session_data["status"] = "in_progress"
        self._save_session()

    # ----------------------------------------------------
    # Mark a step as completed
    # ----------------------------------------------------
    def complete_step(self, step_number: int):
        if step_number not in self.session_data["completed_steps"]:
            self.session_data["completed_steps"].append(step_number)
            self.session_data["current_step"] = step_number + 1
            if len(self.session_data["completed_steps"]) >= self.session_data["total_steps"]:
                self.session_data["status"] = "completed"
            self._save_session()

    # ----------------------------------------------------
    # Get current session status
    # ----------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        return {
            "project": self.session_data["project"],
            "status": self.session_data["status"],
            "completed_steps": self.session_data["completed_steps"],
            "current_step": self.session_data["current_step"],
            "total_steps": self.session_data["total_steps"],
            "started_at": self.session_data.get("created_at"),
            "last_activity": self.session_data.get("last_updated"),
            "last_updated": self.session_data["last_updated"]
        }

    # ----------------------------------------------------
    # Resume the onboarding session from last step
    # ----------------------------------------------------
    def resume(self) -> Optional[int]:
        if self.session_data["status"] == "completed":
            print("✅ Onboarding already completed.")
            return None
        current = self.session_data.get("current_step", 1)
        print(f"Resuming from step {current}...")
        return current

    # ----------------------------------------------------
    # Reset the session
    # ----------------------------------------------------
    def reset(self):
        if self.session_file.exists():
            self.session_file.unlink()
        self.session_data = self._load_session()
        print("🔁 Session reset successfully.")


# ===========================================
# Example Local Test
# ===========================================
if __name__ == "__main__":
    from path_generator import PathGenerator

    project_path = input("Enter project path: ").strip()
    user = input("Enter user ID (optional): ").strip() or "default_user"

    generator = PathGenerator(project_path)
    steps = generator.generate_steps()

    tracker = SessionTracker(project_path, user)

    # Initialize new session
    tracker.initialize(steps)

    # Simulate user completing steps
    tracker.complete_step(1)
    tracker.complete_step(2)

    print("\n📊 Current Session Status:")
    print(json.dumps(tracker.get_status(), indent=4))

    # Resume
    tracker.resume()
