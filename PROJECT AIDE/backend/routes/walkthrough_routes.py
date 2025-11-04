# ===========================================
# walkthrough_routes.py
# FastAPI Routes for Walkthrough Agent
# ===========================================

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from pathlib import Path

try:
    # Try importing as if running from project root
    from agents.walkthrough.interactive_agent import InteractiveAgent
    from agents.walkthrough.path_generator import PathGenerator
    from agents.walkthrough.session_tracker import SessionTracker
except ImportError:
    # Import directly when running from backend directory
    from agents.walkthrough.interactive_agent import InteractiveAgent
    from agents.walkthrough.path_generator import PathGenerator
    from agents.walkthrough.session_tracker import SessionTracker

router = APIRouter(prefix="/walkthrough", tags=["Walkthrough Agent"])

# -------------------------
# Request Models
# -------------------------
class InitializeWalkthroughRequest(BaseModel):
    project_path: str
    user_id: Optional[str] = "default_user"

class ExecuteStepRequest(BaseModel):
    project_path: str
    user_id: Optional[str] = "default_user"
    step_no: int
    interface_type: Optional[str] = "cli"  # cli, web, vscode

class GetHelpRequest(BaseModel):
    project_path: str
    user_id: Optional[str] = "default_user"
    step_no: int
    question: Optional[str] = None

class GetSessionStatusRequest(BaseModel):
    project_path: str
    user_id: Optional[str] = "default_user"

class ResumeSessionRequest(BaseModel):
    project_path: str
    user_id: Optional[str] = "default_user"
    interface_type: Optional[str] = "cli"

# -------------------------
# Agent Cache
# -------------------------
walkthrough_agents_cache = {}

def get_walkthrough_agent(project_path: str, user_id: str = "default_user") -> InteractiveAgent:
    """Get or create a walkthrough agent for the project"""
    path_key = f"{project_path}:{user_id}"
    
    if path_key not in walkthrough_agents_cache:
        try:
            agent = InteractiveAgent(project_path, user_id)
            walkthrough_agents_cache[path_key] = agent
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create walkthrough agent: {str(e)}")
    
    return walkthrough_agents_cache[path_key]

# -------------------------
# API Endpoints
# -------------------------

@router.post("/initialize")
def initialize_walkthrough(request: InitializeWalkthroughRequest):
    """
    Step 1: Initialize comprehensive onboarding walkthrough
    Integrates Phase 1 (Repo Analysis), Phase 2 (Environment Setup), Phase 3 (Documentation)
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        agent = get_walkthrough_agent(request.project_path, request.user_id)
        result = agent.initialize_comprehensive_onboarding()
        
        return {
            "status": "success",
            "message": "Walkthrough initialized successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize walkthrough: {str(e)}")

@router.post("/steps")
def get_walkthrough_steps(request: InitializeWalkthroughRequest):
    """
    Get the comprehensive onboarding steps for a project
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        agent = get_walkthrough_agent(request.project_path, request.user_id)
        steps = agent.path_generator.generate_comprehensive_steps()
        
        return {
            "status": "success",
            "steps": steps,
            "total_steps": len(steps)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get walkthrough steps: {str(e)}")

@router.post("/execute-step")
def execute_step(request: ExecuteStepRequest):
    """
    Step 3: Execute a specific onboarding step
    Supports CLI, Web interface, and VS Code extension
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        agent = get_walkthrough_agent(request.project_path, request.user_id)
        
        # Get the specific step
        steps = agent.path_generator.generate_comprehensive_steps()
        step = next((s for s in steps if s['step_no'] == request.step_no), None)
        
        if not step:
            raise HTTPException(status_code=404, detail=f"Step {request.step_no} not found")
        
        # Execute the step
        success = agent.execute_step(step)
        
        # Mark the step as completed in the session tracker if execution was successful
        if success:
            agent.session_tracker.complete_step(request.step_no)
        
        return {
            "status": "success" if success else "failed",
            "step_no": request.step_no,
            "step_title": step['title'],
            "success": success,
            "message": "Step executed successfully" if success else "Step execution failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute step: {str(e)}")

@router.post("/get-help")
def get_context_help(request: GetHelpRequest):
    """
    Step 5: Get context-aware assistance for a step
    Uses RAG pipeline for dynamic help
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        agent = get_walkthrough_agent(request.project_path, request.user_id)
        
        # Get the specific step
        steps = agent.path_generator.generate_comprehensive_steps()
        step = next((s for s in steps if s['step_no'] == request.step_no), None)
        
        if not step:
            raise HTTPException(status_code=404, detail=f"Step {request.step_no} not found")
        
        # Get context-aware help
        if request.question:
            # Custom question
            if agent.qna_agent:
                result = agent.qna_agent.ask_question(request.question)
                help_content = result.get('answer', 'No help available')
                sources = result.get('sources', [])
            else:
                help_content = "RAG pipeline not available. Using basic help."
                sources = []
        else:
            # Standard step help
            help_content = f"Help for step {request.step_no}: {step['title']}"
            sources = []
        
        return {
            "status": "success",
            "step_no": request.step_no,
            "step_title": step['title'],
            "help_content": help_content,
            "sources": sources,
            "related_files": step.get('related_files', []),
            "prerequisites": step.get('prerequisites', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get help: {str(e)}")

@router.post("/session-status")
def get_session_status(request: GetSessionStatusRequest):
    """
    Step 5: Get current session status and progress
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        agent = get_walkthrough_agent(request.project_path, request.user_id)
        session_status = agent.session_tracker.get_status()
        
        return {
            "status": "success",
            "session_info": session_status,
            "project_path": str(project_path),
            "user_id": request.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.post("/resume")
def resume_session(request: ResumeSessionRequest):
    """
    Resume a walkthrough session from where it left off
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        agent = get_walkthrough_agent(request.project_path, request.user_id)
        
        # Get current session status
        session_status = agent.session_tracker.get_status()
        
        if session_status["status"] == "completed":
            return {
                "status": "success",
                "message": "Walkthrough already completed",
                "session_info": session_status
            }
        
        # Get pending steps
        steps = agent.path_generator.generate_comprehensive_steps()
        completed_steps = session_status.get("completed_steps", [])
        pending_steps = [s for s in steps if s['step_no'] not in completed_steps]
        
        return {
            "status": "success",
            "message": "Session resumed successfully",
            "session_info": session_status,
            "pending_steps": pending_steps,
            "next_step": pending_steps[0] if pending_steps else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume session: {str(e)}")

@router.post("/reset")
def reset_session(request: GetSessionStatusRequest):
    """
    Reset a walkthrough session (clear progress)
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        agent = get_walkthrough_agent(request.project_path, request.user_id)
        agent.session_tracker.reset()
        
        return {
            "status": "success",
            "message": "Session reset successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset session: {str(e)}")

@router.get("/")
def root():
    """Root endpoint for Walkthrough Agent"""
    return {
        "message": "Walkthrough Agent API - Comprehensive Onboarding Assistant",
        "description": "Provides intelligent, step-by-step onboarding walkthroughs with RAG-based assistance",
        "endpoints": {
            "initialize": "POST /walkthrough/initialize - Initialize comprehensive onboarding",
            "steps": "POST /walkthrough/steps - Get onboarding steps",
            "execute-step": "POST /walkthrough/execute-step - Execute a specific step",
            "get-help": "POST /walkthrough/get-help - Get context-aware help",
            "session-status": "POST /walkthrough/session-status - Get session progress",
            "resume": "POST /walkthrough/resume - Resume from where you left off",
            "reset": "POST /walkthrough/reset - Reset session progress"
        },
        "workflow": [
            "1. Initialize walkthrough with /walkthrough/initialize",
            "2. Get steps with /walkthrough/steps",
            "3. Execute steps with /walkthrough/execute-step",
            "4. Get help with /walkthrough/get-help when needed",
            "5. Check progress with /walkthrough/session-status",
            "6. Resume anytime with /walkthrough/resume"
        ],
        "features": [
            "Integrates Phase 1 (Repo Analysis), Phase 2 (Environment Setup), Phase 3 (Documentation)",
            "Context-aware assistance using RAG pipeline",
            "Progress memory with resume functionality",
            "Support for CLI, Web, and VS Code interfaces",
            "Comprehensive error handling and troubleshooting",
            "Prerequisite checking and validation"
        ]
    }
