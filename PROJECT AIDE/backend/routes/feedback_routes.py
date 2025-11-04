"""
Feedback Agent Routes
====================
FastAPI routes for the Feedback & Continuous Learning Agent functionality.
Provides endpoints for feedback collection, analytics, and model retraining.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import asyncio
import time
import json
from datetime import datetime

# Import feedback agent modules
try:
    # Try importing as if running from project root
    from backend.agents.feedback import FeedbackCollector, FeedbackAnalytics, ModelRetrainer, FeedbackType, FeedbackSeverity
except ImportError:
    # Import directly when running from backend directory
    from agents.feedback import FeedbackCollector, FeedbackAnalytics, ModelRetrainer, FeedbackType, FeedbackSeverity

router = APIRouter(prefix="/feedback", tags=["Feedback & Learning Agent"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("feedback_routes")

# -------------------------
# Request Models
# -------------------------
class FeedbackRequest(BaseModel):
    user_id: str
    session_id: str
    feedback_type: str  # Will be converted to FeedbackType enum
    description: str
    rating: Optional[int] = None
    title: str = ""
    severity: str = "medium"  # Will be converted to FeedbackSeverity enum
    agent_involved: Optional[str] = None
    step_failed: Optional[str] = None
    suggested_fix: Optional[str] = None
    user_experience: Optional[str] = None
    tags: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None

class SatisfactionSurveyRequest(BaseModel):
    user_id: str
    session_id: str
    overall_rating: int
    onboarding_time_minutes: int
    agents_used: List[str]
    most_helpful_agent: Optional[str] = None
    least_helpful_agent: Optional[str] = None
    would_recommend: bool = True
    additional_comments: str = ""

class FailureAnalysisRequest(BaseModel):
    user_id: str
    session_id: str
    agent_involved: str
    step_failed: str
    error_message: str
    user_actions: List[str]
    suggested_fix: Optional[str] = None
    severity: str = "high"

class ProjectPathRequest(BaseModel):
    project_path: str

class RetrainingRequest(BaseModel):
    agent_name: str
    force_retrain: bool = False

# -------------------------
# Feedback Collection Endpoints
# -------------------------
@router.post("/collect")
def collect_feedback(request: FeedbackRequest):
    """
    Collect user feedback from onboarding experiences.
    """
    try:
        # Convert string enums to actual enums
        feedback_type = FeedbackType(request.feedback_type)
        severity = FeedbackSeverity(request.severity)
        
        # Initialize feedback collector
        collector = FeedbackCollector(request.project_path if hasattr(request, 'project_path') else ".")
        
        # Collect feedback
        feedback_id = collector.collect_feedback(
            user_id=request.user_id,
            session_id=request.session_id,
            feedback_type=feedback_type,
            description=request.description,
            rating=request.rating,
            title=request.title,
            severity=severity,
            agent_involved=request.agent_involved,
            step_failed=request.step_failed,
            suggested_fix=request.suggested_fix,
            user_experience=request.user_experience,
            tags=request.tags,
            context=request.context
        )
        
        return {
            "status": "success",
            "message": "Feedback collected successfully",
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to collect feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to collect feedback: {str(e)}")

@router.post("/survey/satisfaction")
def collect_satisfaction_survey(request: SatisfactionSurveyRequest):
    """
    Collect structured satisfaction survey data.
    """
    try:
        collector = FeedbackCollector(".")
        
        feedback_id = collector.collect_satisfaction_survey(
            user_id=request.user_id,
            session_id=request.session_id,
            overall_rating=request.overall_rating,
            onboarding_time_minutes=request.onboarding_time_minutes,
            agents_used=request.agents_used,
            most_helpful_agent=request.most_helpful_agent,
            least_helpful_agent=request.least_helpful_agent,
            would_recommend=request.would_recommend,
            additional_comments=request.additional_comments
        )
        
        return {
            "status": "success",
            "message": "Satisfaction survey collected successfully",
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to collect satisfaction survey: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to collect satisfaction survey: {str(e)}")

@router.post("/analyze/failure")
def collect_failure_analysis(request: FailureAnalysisRequest):
    """
    Collect detailed failure analysis data.
    """
    try:
        collector = FeedbackCollector(".")
        
        feedback_id = collector.collect_failure_analysis(
            user_id=request.user_id,
            session_id=request.session_id,
            agent_involved=request.agent_involved,
            step_failed=request.step_failed,
            error_message=request.error_message,
            user_actions=request.user_actions,
            suggested_fix=request.suggested_fix,
            severity=FeedbackSeverity(request.severity)
        )
        
        return {
            "status": "success",
            "message": "Failure analysis collected successfully",
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to collect failure analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to collect failure analysis: {str(e)}")

# -------------------------
# Analytics Endpoints
# -------------------------
@router.post("/analytics/satisfaction")
def analyze_satisfaction_trends(request: ProjectPathRequest, days: int = 30):
    """
    Analyze satisfaction trends over time.
    """
    try:
        analytics = FeedbackAnalytics(request.project_path)
        trends = analytics.analyze_satisfaction_trends(days)
        
        return {
            "status": "success",
            "message": "Satisfaction trends analyzed",
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze satisfaction trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze satisfaction trends: {str(e)}")

@router.post("/analytics/performance")
def analyze_agent_performance(request: ProjectPathRequest):
    """
    Analyze performance of individual agents.
    """
    try:
        analytics = FeedbackAnalytics(request.project_path)
        performance = analytics.analyze_agent_performance()
        
        return {
            "status": "success",
            "message": "Agent performance analyzed",
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze agent performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze agent performance: {str(e)}")

@router.post("/analytics/improvements")
def identify_improvement_areas(request: ProjectPathRequest):
    """
    Identify specific areas that need improvement.
    """
    try:
        analytics = FeedbackAnalytics(request.project_path)
        improvements = analytics.identify_improvement_areas()
        
        return {
            "status": "success",
            "message": "Improvement areas identified",
            "improvements": improvements,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to identify improvement areas: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to identify improvement areas: {str(e)}")

@router.post("/analytics/insights")
def generate_learning_insights(request: ProjectPathRequest):
    """
    Generate insights for continuous learning and improvement.
    """
    try:
        analytics = FeedbackAnalytics(request.project_path)
        insights = analytics.generate_learning_insights()
        
        return {
            "status": "success",
            "message": "Learning insights generated",
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate learning insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate learning insights: {str(e)}")

@router.post("/analytics/dashboard")
def get_performance_dashboard(request: ProjectPathRequest):
    """
    Get data for performance dashboard visualization.
    """
    try:
        analytics = FeedbackAnalytics(request.project_path)
        dashboard_data = analytics.get_performance_dashboard_data()
        
        return {
            "status": "success",
            "message": "Dashboard data retrieved",
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

# -------------------------
# Model Retraining Endpoints
# -------------------------
@router.post("/retrain/prepare")
def prepare_retraining_data(request: RetrainingRequest):
    """
    Prepare retraining data for a specific agent.
    """
    try:
        retrainer = ModelRetrainer(".")
        retraining_data = retrainer.prepare_retraining_data(request.agent_name)
        
        return {
            "status": "success",
            "message": "Retraining data prepared",
            "retraining_data": retraining_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to prepare retraining data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to prepare retraining data: {str(e)}")

@router.post("/retrain/execute")
def execute_retraining(request: RetrainingRequest):
    """
    Execute model retraining for a specific agent.
    """
    try:
        retrainer = ModelRetrainer(".")
        
        if request.force_retrain:
            # Force retraining regardless of schedule
            retraining_data = retrainer.prepare_retraining_data(request.agent_name)
            if retraining_data["status"] == "ready":
                result = retrainer.retrain_agent_model(request.agent_name, retraining_data)
            else:
                result = retraining_data
        else:
            # Scheduled retraining
            result = retrainer.schedule_retraining(request.agent_name)
        
        return {
            "status": "success",
            "message": "Retraining executed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to execute retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute retraining: {str(e)}")

@router.get("/retrain/status")
def get_retraining_status():
    """
    Get status of all agents' retraining needs.
    """
    try:
        retrainer = ModelRetrainer(".")
        status = retrainer.get_retraining_status()
        
        return {
            "status": "success",
            "message": "Retraining status retrieved",
            "retraining_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get retraining status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get retraining status: {str(e)}")

# -------------------------
# Knowledge Base Updates
# -------------------------
@router.post("/knowledge/update")
def update_knowledge_base(request: ProjectPathRequest):
    """
    Update knowledge base based on feedback patterns.
    """
    try:
        retrainer = ModelRetrainer(request.project_path)
        
        # Load feedback data
        feedback_file = Path(request.project_path) / "backend" / "feedback_data" / "feedback.json"
        if not feedback_file.exists():
            return {
                "status": "no_data",
                "message": "No feedback data available for knowledge base update"
            }
        
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedback_data = json.load(f)
        
        # Update knowledge base
        updates = retrainer.update_knowledge_base(feedback_data)
        
        return {
            "status": "success",
            "message": "Knowledge base updated",
            "updates": updates,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update knowledge base: {str(e)}")

# -------------------------
# Health and Info Endpoints
# -------------------------
@router.get("/")
def root():
    """Root endpoint for Feedback Agent"""
    return {
        "message": "Feedback & Continuous Learning Agent API",
        "description": "Enables AIDE to continuously learn and improve from user feedback",
        "endpoints": {
            "collect_feedback": "POST /feedback/collect - Collect user feedback",
            "satisfaction_survey": "POST /feedback/survey/satisfaction - Collect satisfaction survey",
            "failure_analysis": "POST /feedback/analyze/failure - Collect failure analysis",
            "satisfaction_trends": "POST /feedback/analytics/satisfaction - Analyze satisfaction trends",
            "agent_performance": "POST /feedback/analytics/performance - Analyze agent performance",
            "improvement_areas": "POST /feedback/analytics/improvements - Identify improvement areas",
            "learning_insights": "POST /feedback/analytics/insights - Generate learning insights",
            "dashboard_data": "POST /feedback/analytics/dashboard - Get dashboard data",
            "prepare_retraining": "POST /feedback/retrain/prepare - Prepare retraining data",
            "execute_retraining": "POST /feedback/retrain/execute - Execute model retraining",
            "retraining_status": "GET /feedback/retrain/status - Get retraining status",
            "update_knowledge": "POST /feedback/knowledge/update - Update knowledge base"
        },
        "features": [
            "Comprehensive feedback collection",
            "Advanced analytics and insights",
            "Automated model retraining",
            "Knowledge base updates",
            "Performance monitoring",
            "Continuous learning pipeline"
        ]
    }

@router.get("/health")
def health_check():
    """Health check for Feedback Agent"""
    try:
        # Test basic functionality
        collector = FeedbackCollector(".")
        analytics = FeedbackAnalytics(".")
        retrainer = ModelRetrainer(".")
        
        return {
            "status": "healthy",
            "message": "Feedback Agent is operational",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "feedback_collector": "available",
                "analytics_engine": "available",
                "model_retrainer": "available"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Feedback Agent has issues: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
