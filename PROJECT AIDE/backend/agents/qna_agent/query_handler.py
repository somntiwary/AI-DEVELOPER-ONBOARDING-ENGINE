# ==============================
# query_handler.py
# Legacy Query Handler - Now Integrated into Main QnA Agent
# This file is kept for backward compatibility but functionality is now in qna_routes.py
# ==============================

import warnings
from pathlib import Path
from typing import Dict, Any

try:
    from backend.agents.qna_agent.qna_agent import QnAAgent
except ImportError:
    # Allow running when executed as a script
    import os as _os, sys as _sys
    _BACKEND_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
    _PROJECT_ROOT = _os.path.dirname(_BACKEND_DIR)
    if _PROJECT_ROOT not in _sys.path:
        _sys.path.insert(0, _PROJECT_ROOT)
    from backend.agents.qna_agent.qna_agent import QnAAgent  # type: ignore


class LegacyQueryHandler:
    """
    Legacy query handler for backward compatibility.
    
    ⚠️  DEPRECATED: This class is kept for backward compatibility.
    Use the new QnAAgent and qna_routes.py for full functionality.
    """

    def __init__(self, project_path: str):
        warnings.warn(
            "LegacyQueryHandler is deprecated. Use QnAAgent instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.project_path = Path(project_path)
        self.qna_agent = QnAAgent(str(self.project_path))

    def query_docs(self, question: str) -> Dict[str, Any]:
        """
        Legacy method for querying documentation.
        
        ⚠️  DEPRECATED: Use QnAAgent.ask_question() instead.
        """
        warnings.warn(
            "query_docs() is deprecated. Use QnAAgent.ask_question() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            # Initialize knowledge base if not already done
            if not self.qna_agent.knowledge_indexed:
                init_result = self.qna_agent.initialize_knowledge_base()
                if init_result["status"] != "success":
                    return {
                        "answer": f"Failed to initialize knowledge base: {init_result.get('message', 'Unknown error')}",
                        "error": True
                    }
            
            # Get answer using the comprehensive QnA agent
            result = self.qna_agent.ask_question(question, include_sources=False)
            return {
                "answer": result["answer"],
                "error": False
            }
            
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "error": True
            }

    def get_project_info(self) -> Dict[str, Any]:
        """Get basic project information."""
        try:
            summary = self.qna_agent.get_project_summary()
            return {
                "project_path": str(self.project_path),
                "knowledge_base_ready": summary.get("knowledge_indexed", False),
                "conversation_count": summary.get("conversation_count", 0)
            }
        except Exception as e:
            return {
                "project_path": str(self.project_path),
                "error": str(e)
            }


# ==============================
# Legacy FastAPI App (Deprecated)
# ==============================

def create_legacy_app():
    """
    Create legacy FastAPI app for backward compatibility.
    
    ⚠️  DEPRECATED: Use the main FastAPI app with qna_routes.py instead.
    """
    warnings.warn(
        "create_legacy_app() is deprecated. Use the main FastAPI app with qna_routes.py instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    app = FastAPI(
        title="Legacy Documentation Q&A API",
        description="⚠️ DEPRECATED: Use /api/qna endpoints instead",
        version="1.0.0"
    )
    
    class QueryRequest(BaseModel):
        project_path: str
        question: str
    
    # Cache for legacy handlers
    legacy_handlers = {}
    
    def get_legacy_handler(project_path: str) -> LegacyQueryHandler:
        """Get or create legacy handler for project path."""
        path_key = str(Path(project_path).resolve())
        
        if path_key not in legacy_handlers:
            if not Path(project_path).exists():
                raise HTTPException(status_code=400, detail=f"Project path does not exist: {project_path}")
            legacy_handlers[path_key] = LegacyQueryHandler(project_path)
        
        return legacy_handlers[path_key]
    
    @app.post("/api/documentation/query")
    def legacy_query_docs(request: QueryRequest):
        """
        ⚠️ DEPRECATED: Legacy endpoint for querying documentation.
        Use POST /api/qna/ask instead.
        """
        try:
            handler = get_legacy_handler(request.project_path)
            result = handler.query_docs(request.question)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok", "message": "Legacy API running (deprecated)"}
    
    @app.get("/")
    def root():
        """Root endpoint with deprecation notice."""
        return {
            "message": "⚠️ This is a legacy API. Please use the main FastAPI app with /api/qna endpoints.",
            "deprecated": True,
            "recommended_endpoints": {
                "initialize": "POST /api/qna/initialize",
                "ask": "POST /api/qna/ask",
                "capabilities": "GET /api/qna/capabilities"
            }
        }
    
    return app


# ==============================
# 🚀 CLI / Example usage
# ==============================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python query_handler.py <project_path>")
        print("⚠️  Note: This is a legacy handler. Use qna_agent.py for full functionality.")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    print("⚠️  Using legacy query handler. Consider using qna_agent.py for full functionality.")
    
    # Create legacy handler
    handler = LegacyQueryHandler(project_path)
    
    # Interactive session
    print("\n💬 Legacy Q&A Session (type 'quit' to exit):")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ['quit', 'exit']:
            break
        
        if not question:
            continue
        
        result = handler.query_docs(question)
        if result.get("error"):
            print(f"❌ Error: {result['answer']}")
        else:
            print(f"💡 Answer: {result['answer']}")