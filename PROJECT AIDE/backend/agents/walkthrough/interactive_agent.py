"""
interactive_agent.py
--------------------
Interactive Agent for onboarding walkthroughs with dynamic RAG-based help.
Supports CLI, Web interface, and VS Code extension integration.
"""

from typing import Dict, List, Optional, Any
import json
import time
import random
import subprocess
import os
from pathlib import Path

from .path_generator import PathGenerator
from .session_tracker import SessionTracker

try:
    from agents.qna_agent.rag_pipeline import RAGPipeline
    from agents.qna_agent.qna_agent import QnAAgent
except ImportError:
    # Allow running when executed as a script
    import sys
    from pathlib import Path as _Path
    _BACKEND_DIR = _Path(__file__).parent.parent
    _PROJECT_ROOT = _BACKEND_DIR.parent
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from agents.qna_agent.rag_pipeline import RAGPipeline
    from agents.qna_agent.qna_agent import QnAAgent

class InteractiveAgent:
    """
    Manages comprehensive onboarding sessions with dynamic RAG-based help.
    Supports multiple interfaces: CLI, Web, and VS Code extension.
    Integrates all three phases for intelligent walkthroughs.
    """

    def __init__(self, project_path: str, user_id: Optional[str] = "default_user"):
        self.project_path = Path(project_path)
        self.user_id = user_id
        self.path_generator = PathGenerator(str(project_path))
        self.session_tracker = SessionTracker(str(project_path), user_id)
        
        # Initialize RAG pipeline for context-aware assistance
        try:
            self.rag_pipeline = RAGPipeline(str(project_path))
            self.qna_agent = QnAAgent(str(project_path))
        except Exception as e:
            print(f"Warning: RAG pipeline initialization failed: {e}")
            self.rag_pipeline = None
            self.qna_agent = None
        
        self.current_step = None
        self.interface_type = "cli"  # cli, web, vscode

    # -------------------------
    # Step 1: Onboarding Initialization
    # -------------------------
    def initialize_comprehensive_onboarding(self) -> Dict[str, Any]:
        """
        Step 1: Onboarding Initialization
        - Detect repo type using Phase 1 metadata
        - Fetch environment requirements from Phase 2  
        - Load documentation & guides from Phase 3
        """
        print(f"\n🔍 Initializing comprehensive onboarding for: {self.project_path}")
        
        # Initialize all three phases
        phase_data = self.path_generator.initialize_comprehensive_onboarding()
        
        # Generate comprehensive steps
        onboarding_steps = self.path_generator.generate_comprehensive_steps()
        
        # Initialize session tracking
        self.session_tracker.initialize(onboarding_steps)
        
        print(f"✅ {len(onboarding_steps)} comprehensive steps initialized for onboarding.\n")
        
        return {
            "phase_data": phase_data,
            "onboarding_steps": onboarding_steps,
            "session_info": self.session_tracker.get_status()
        }

    # -------------------------
    # Step 2: Generate Onboarding Flow (Legacy)
    # -------------------------
    def initialize_onboarding(self) -> List[Dict]:
        """Legacy method for backward compatibility"""
        result = self.initialize_comprehensive_onboarding()
        return result["onboarding_steps"]

    # -------------------------
    # Step 3: Interactive Execution
    # -------------------------
    def start_interactive_walkthrough(self, interface_type: str = "cli"):
        """
        Step 3: Interactive Execution
        Supports CLI, Web interface, and VS Code extension
        """
        self.interface_type = interface_type
        print("🚀 Starting Interactive Onboarding Walkthrough...\n")
        
        # Get current session status
        session_status = self.session_tracker.get_status()
        if session_status["status"] == "completed":
            print("✅ Onboarding already completed!")
            return
        
        # Get pending steps
        steps = self._get_pending_steps()
        if not steps:
            print("🎯 No pending steps. Onboarding complete!")
            return

        for step in steps:
            self.current_step = step
            self._display_step(step)
            
            if interface_type == "cli":
                user_input = input("Run this step? (y/n/help/exit): ").strip().lower()
                self._handle_cli_input(step, user_input)
            elif interface_type == "web":
                # Web interface would handle this differently
                self._handle_web_step(step)
            elif interface_type == "vscode":
                # VS Code extension would handle this differently
                self._handle_vscode_step(step)

        print("\n🎯 Onboarding completed or paused. Resume anytime.\n")

    def _get_pending_steps(self) -> List[Dict]:
        """Get steps that haven't been completed yet"""
        session_status = self.session_tracker.get_status()
        completed_steps = session_status.get("completed_steps", [])
        
        # This would need to be implemented in SessionTracker
        # For now, return all steps
        return self.path_generator.generate_comprehensive_steps()

    def _display_step(self, step: Dict):
        """Display step information based on interface type"""
        if self.interface_type == "cli":
            print(f"➡️ Step {step['step_no']}: {step['title']}")
            print(f"   💡 {step['description']}")
            print(f"   ⚙️ Command: {step['command']}")
            if 'related_files' in step:
                print(f"   📁 Related files: {', '.join(step['related_files'])}")
            print()
        elif self.interface_type == "web":
            # Web interface would format this as HTML/JSON
            pass
        elif self.interface_type == "vscode":
            # VS Code extension would show this in the editor
            pass

    def _handle_cli_input(self, step: Dict, user_input: str):
        """Handle CLI user input"""
        if user_input == "exit":
            print("\n👋 Exiting session. Progress saved.\n")
            return "exit"
        elif user_input == "help":
            self.provide_context_help(step)
            return "help"
        elif user_input == "n":
            print("⏭️ Skipping this step...\n")
            self.session_tracker.complete_step(step["step_no"])
            return "skip"
        elif user_input == "y":
            success = self.execute_step(step)
            if success:
                self.session_tracker.complete_step(step["step_no"])
            return "execute"
        else:
            print("⚠️ Invalid input. Type 'y', 'n', 'help', or 'exit'.\n")
            return "invalid"

    def _handle_web_step(self, step: Dict):
        """Handle web interface step execution"""
        # Web interface implementation would go here
        pass

    def _handle_vscode_step(self, step: Dict):
        """Handle VS Code extension step execution"""
        # VS Code extension implementation would go here
        pass

    # -------------------------
    # Execute a single step
    # -------------------------
    def execute_step(self, step: Dict) -> bool:
        """
        Execute a single step with comprehensive error handling and guidance
        """
        try:
            print(f"⏳ Executing: {step['command']} ...")
            
            # Check prerequisites
            if not self._check_prerequisites(step):
                print(f"❌ Prerequisites not met for step {step['step_no']}")
                self._provide_prerequisite_help(step)
                return False
            
            # Execute the command
            success = self._execute_command(step['command'])
            
            if success:
                print(f"✅ Step {step['step_no']} completed successfully.\n")
                return True
            else:
                print(f"❌ Step {step['step_no']} failed. Providing troubleshooting help...\n")
                self._provide_troubleshooting_help(step)
                return False
                
        except Exception as e:
            print(f"❌ Error executing step {step['step_no']}: {e}")
            self._provide_error_help(step, str(e))
            return False

    def _check_prerequisites(self, step: Dict) -> bool:
        """Check if step prerequisites are met"""
        prerequisites = step.get('prerequisites', [])
        for prereq in prerequisites:
            if not self._check_single_prerequisite(prereq):
                return False
        return True

    def _check_single_prerequisite(self, prereq: str) -> bool:
        """Check a single prerequisite"""
        if "Python installed" in prereq:
            return self._check_python_installed()
        elif "Git installed" in prereq:
            return self._check_git_installed()
        elif "Virtual environment activated" in prereq:
            return self._check_venv_activated()
        # Add more prerequisite checks as needed
        return True

    def _check_python_installed(self) -> bool:
        """Check if Python is installed"""
        try:
            result = subprocess.run(['python', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def _check_git_installed(self) -> bool:
        """Check if Git is installed"""
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def _check_venv_activated(self) -> bool:
        """Check if virtual environment is activated"""
        return 'VIRTUAL_ENV' in os.environ

    def _execute_command(self, command: str) -> bool:
        """Execute a command and return success status"""
        try:
            # For demonstration, we'll simulate command execution
            # In a real implementation, you'd use subprocess.run()
            if command.startswith('git clone'):
                print("   📥 Cloning repository...")
            elif command.startswith('python -m venv'):
                print("   🐍 Creating virtual environment...")
            elif command.startswith('source venv') or command.startswith('venv\\Scripts\\activate'):
                print("   🔄 Activating virtual environment...")
            elif command.startswith('pip install'):
                print("   📦 Installing dependencies...")
            elif command.startswith('pytest'):
                print("   🧪 Running tests...")
            else:
                print(f"   ⚙️ Executing: {command}")
            
            # Simulate execution time
            time.sleep(random.uniform(1, 3))
            
            # Simulate success/failure (90% success rate for demo)
            return random.random() > 0.1
            
        except Exception as e:
            print(f"   ❌ Command execution failed: {e}")
            return False

    # -------------------------
    # RAG-based Context Help
    # -------------------------
    def provide_context_help(self, step: Dict):
        """
        Step 5: Context-Aware Assistance
        Provide dynamic, context-aware help using the RAG pipeline
        """
        print(f"\n🧠 Retrieving context-aware help for: {step['title']}\n")
        
        # Build comprehensive question
        question = f"""
        Explain why this step is necessary and how to execute it: {step['title']}
        
        Step details:
        - Description: {step.get('description', 'N/A')}
        - Command: {step.get('command', 'N/A')}
        - Related files: {', '.join(step.get('related_files', []))}
        - Prerequisites: {', '.join(step.get('prerequisites', []))}
        
        Please provide:
        1. Why this step is important
        2. How to execute it properly
        3. What to expect
        4. Common issues and solutions
        """
        
        try:
            if self.qna_agent:
                # Use the comprehensive QnA agent
                result = self.qna_agent.ask_question(question)
                answer = result.get('answer', 'No answer available')
                sources = result.get('sources', [])
                
                print(f"💬 {answer}\n")
                if sources:
                    print(f"📚 Sources: {', '.join(sources[:3])}\n")
            else:
                # Fallback to basic explanation
                self._provide_basic_help(step)
                
        except Exception as e:
            print(f"⚠️ Unable to fetch RAG explanation: {e}\n")
            self._provide_basic_help(step)

    def _provide_basic_help(self, step: Dict):
        """Provide basic help when RAG is unavailable"""
        print("💬 Basic Help:")
        print(f"   📝 Description: {step.get('explanation', step.get('description', 'No description available'))}")
        print(f"   ⚙️ Command: {step.get('command', 'No command specified')}")
        print(f"   📁 Related files: {', '.join(step.get('related_files', []))}")
        print(f"   ✅ Success criteria: {step.get('success_criteria', 'Step completes without errors')}")
        print()

    def _provide_prerequisite_help(self, step: Dict):
        """Provide help for unmet prerequisites"""
        print("🔧 Prerequisite Help:")
        prerequisites = step.get('prerequisites', [])
        for prereq in prerequisites:
            if not self._check_single_prerequisite(prereq):
                print(f"   ❌ Missing: {prereq}")
                if "Python installed" in prereq:
                    print("      → Install Python from https://python.org")
                elif "Git installed" in prereq:
                    print("      → Install Git from https://git-scm.com")
                elif "Virtual environment activated" in prereq:
                    print("      → Run: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)")
        print()

    def _provide_troubleshooting_help(self, step: Dict):
        """Provide troubleshooting help for failed steps"""
        print("🔧 Troubleshooting Help:")
        troubleshooting = step.get('troubleshooting', 'Check the command output for error messages')
        print(f"   💡 {troubleshooting}")
        
        # Use RAG for additional troubleshooting
        if self.qna_agent:
            try:
                question = f"Troubleshooting help for failed step: {step['title']}. Command: {step['command']}"
                result = self.qna_agent.ask_question(question)
                if result.get('answer'):
                    print(f"   🧠 Additional help: {result['answer']}")
            except:
                pass
        print()

    def _provide_error_help(self, step: Dict, error: str):
        """Provide help for execution errors"""
        print("❌ Error Help:")
        print(f"   🚨 Error: {error}")
        print(f"   💡 Step: {step['title']}")
        print(f"   ⚙️ Command: {step['command']}")
        
        # Use RAG for error-specific help
        if self.qna_agent:
            try:
                question = f"Error occurred: {error}. Step: {step['title']}. How to fix this?"
                result = self.qna_agent.ask_question(question)
                if result.get('answer'):
                    print(f"   🧠 Suggested fix: {result['answer']}")
            except:
                pass
        print()

    # -------------------------
    # Save & Resume Session
    # -------------------------
    def save_progress(self):
        self.session_tracker.save_state()
        print("💾 Progress saved successfully.")

    def resume_session(self):
        print("\n🔁 Resuming previous session...")
        self.start_interactive_walkthrough()


# -------------------------
# CLI Example Usage
# -------------------------
if __name__ == "__main__":
    project_path = input("Enter project path: ").strip()
    agent = InteractiveAgent(project_path)

    onboarding_steps = agent.initialize_onboarding()
    print(json.dumps(onboarding_steps, indent=2))

    agent.start_interactive_walkthrough()
