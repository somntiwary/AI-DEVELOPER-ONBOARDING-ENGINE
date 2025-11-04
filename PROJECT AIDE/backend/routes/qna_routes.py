# ==============================
# qna_routes.py
# FastAPI Routes for QnA Agent
# Professional conversational interface for project understanding
# ==============================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    # Try importing as if running from project root
    from agents.qna_agent.qna_agent import QnAAgent
    from config import ENABLE_WEAVIATE
except ImportError:
    # Import directly when running from backend directory
    from agents.qna_agent.qna_agent import QnAAgent
    from config import ENABLE_WEAVIATE

router = APIRouter(prefix="/qna", tags=["QnA Agent"])

# ==============================
# Request/Response Models
# ==============================

class InitializeKnowledgeRequest(BaseModel):
    project_path: str

class AskQuestionRequest(BaseModel):
    project_path: str
    question: str
    include_sources: Optional[bool] = True

class AnalyzeIntentRequest(BaseModel):
    project_path: str
    question: str

class GetHistoryRequest(BaseModel):
    project_path: str
    limit: Optional[int] = 10

# ==============================
# Global QnA Agent Cache
# ==============================

# Cache QnA agents per project path to avoid re-initialization
qna_agents_cache: Dict[str, QnAAgent] = {}

def get_qna_agent(project_path: str) -> QnAAgent:
    """Get or create QnA agent for project path."""
    path_key = str(Path(project_path).resolve())
    
    if path_key not in qna_agents_cache:
        if not Path(project_path).exists():
            raise HTTPException(status_code=400, detail=f"Project path does not exist: {project_path}")
        
        qna_agents_cache[path_key] = QnAAgent(project_path)
    
    return qna_agents_cache[path_key]

# ==============================
# API Endpoints
# ==============================

@router.post("/initialize")
def initialize_knowledge_base(request: InitializeKnowledgeRequest):
    """
    Initialize the comprehensive knowledge base for a project.
    This integrates Repository Analysis, Environment Setup, and Documentation agents.
    """
    try:
        agent = get_qna_agent(request.project_path)
        result = agent.initialize_knowledge_base()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize knowledge base: {str(e)}")

@router.post("/ask")
def ask_question(request: AskQuestionRequest):
    """
    Ask a question about the project using the comprehensive QnA agent.
    
    The agent integrates:
    - Repository Analysis (code structure, dependencies, components)
    - Environment Setup (Docker, DevContainer, configuration)
    - Documentation (APIs, usage, examples)
    
    Example questions:
    - "What is the overall architecture of this project?"
    - "How do I set up the development environment?"
    - "What API endpoints are available?"
    - "How do I run the tests?"
    - "What are the main dependencies?"
    """
    try:
        agent = get_qna_agent(request.project_path)
        
        # Check if knowledge base is initialized
        if not agent.knowledge_indexed:
            return {
                "error": "Knowledge base not initialized",
                "message": "Please call /qna/initialize first to set up the knowledge base",
                "question": request.question
            }
        
        result = agent.ask_question(request.question, request.include_sources)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@router.post("/analyze-intent")
def analyze_question_intent(request: AnalyzeIntentRequest):
    """
    Analyze the intent of a question to understand what type of information is being requested.
    """
    try:
        agent = get_qna_agent(request.project_path)
        intent = agent.analyze_question_intent(request.question)
        return {
            "question": request.question,
            "intent_analysis": intent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze intent: {str(e)}")

@router.post("/suggest-followups")
def suggest_follow_up_questions(request: AskQuestionRequest):
    """
    Generate intelligent follow-up question suggestions based on a question and answer.
    """
    try:
        agent = get_qna_agent(request.project_path)
        
        # Get recent conversation to find the last Q&A
        history = agent.get_conversation_history(limit=1)
        if not history:
            return {
                "error": "No conversation history found",
                "message": "Ask a question first to get follow-up suggestions"
            }
        
        last_conv = history[-1]
        suggestions = agent.suggest_follow_up_questions(
            last_conv["question"], 
            last_conv["answer"]
        )
        
        return {
            "original_question": last_conv["question"],
            "suggested_followups": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")

@router.post("/history")
def get_conversation_history(request: GetHistoryRequest):
    """
    Get conversation history for a project.
    """
    try:
        agent = get_qna_agent(request.project_path)
        history = agent.get_conversation_history(request.limit)
        return {
            "project_path": request.project_path,
            "conversation_history": history,
            "total_exchanges": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.post("/summary")
def get_project_summary(request: InitializeKnowledgeRequest):
    """
    Get comprehensive project summary including knowledge base status.
    """
    try:
        agent = get_qna_agent(request.project_path)
        summary = agent.get_project_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project summary: {str(e)}")

@router.post("/reset-history")
def reset_conversation_history(request: InitializeKnowledgeRequest):
    """
    Reset/clear all conversation history for a project.
    """
    try:
        agent = get_qna_agent(request.project_path)
        agent.memory_manager.clear_memory()
        return {
            "status": "success",
            "message": "Conversation history cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset history: {str(e)}")

@router.post("/reset")
def reset_knowledge_base(request: InitializeKnowledgeRequest):
    """
    Reset the knowledge base by clearing existing schema and data.
    Use this if you encounter schema conflicts or want to start fresh.
    """
    try:
        agent = get_qna_agent(request.project_path)
        agent.rag_pipeline.reset_knowledge_base()
        return {
            "status": "success",
            "message": "Knowledge base reset successfully. Call /qna/initialize to rebuild."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset knowledge base: {str(e)}")

@router.get("/capabilities")
def get_agent_capabilities():
    """
    Get information about what the QnA agent can do.
    """
    try:
        # Create a temporary agent to get capabilities
        temp_agent = QnAAgent(".")
        capabilities = temp_agent.get_agent_capabilities()
        return capabilities
    except Exception as e:
        return {
            "capabilities": [
                "Repository structure analysis",
                "Environment setup guidance", 
                "Documentation queries",
                "Code explanation",
                "API endpoint discovery",
                "Dependency analysis",
                "Development workflow guidance",
                "Troubleshooting assistance"
            ],
            "integrated_agents": [
                "Repository Analysis Agent (Phase 1)",
                "Environment Setup Agent (Phase 2)", 
                "Documentation Agent (Phase 3)"
            ],
            "features": [
                "Conversational memory",
                "Context-aware responses",
                "RAG-based knowledge retrieval",
                "Follow-up question suggestions",
                "Intent analysis",
                "Source attribution"
            ],
            "weaviate_enabled": ENABLE_WEAVIATE,
            "error": str(e)
        }

@router.get("/")
def root():
    """Root endpoint for QnA Agent."""
    return {
        "message": "QnA Agent API - Comprehensive Project Understanding",
        "description": "Integrates Repository Analysis, Environment Setup, and Documentation agents",
        "endpoints": {
            "initialize": "POST /qna/initialize - Initialize knowledge base",
            "ask": "POST /qna/ask - Ask questions about the project",
            "analyze_intent": "POST /qna/analyze-intent - Analyze question intent",
            "suggest_followups": "POST /qna/suggest-followups - Get follow-up suggestions",
            "history": "POST /qna/history - Get conversation history",
            "summary": "POST /qna/summary - Get project summary",
            "reset": "POST /qna/reset - Reset knowledge base (clear schema)",
            "capabilities": "GET /qna/capabilities - Get agent capabilities"
        },
        "workflow": [
            "1. Initialize knowledge base with /qna/initialize",
            "2. Ask questions with /qna/ask",
            "3. Get follow-up suggestions with /qna/suggest-followups",
            "4. View conversation history with /qna/history"
        ]
    }
