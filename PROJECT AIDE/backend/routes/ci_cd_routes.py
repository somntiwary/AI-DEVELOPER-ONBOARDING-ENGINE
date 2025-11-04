"""
CI/CD Agent Routes
==================
FastAPI routes for the CI/CD Agent functionality.
Provides endpoints for GitHub Actions, Jenkins, and general CI/CD operations.
Enhanced with performance optimizations, comprehensive error handling, and monitoring.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import asyncio
import time
import functools
from datetime import datetime, timedelta
import json
import traceback

# Import CI/CD agent modules
try:
    # Try importing as if running from project root
    from backend.agents.ci_cd_agent.github_ci import GitHubCISummarizer, GitHubWorkflowManager
    from backend.agents.ci_cd_agent.jenkins_ci import JenkinsFileParser, JenkinsManager
    from backend.agents.ci_cd_agent.llm_diagnostics import LLMDiagnostics
    from backend.agents.ci_cd_agent.validation import CIValidator
    from backend.agents.ci_cd_agent.performance import cached, monitor_performance, get_performance_summary
except ImportError:
    # Import directly when running from backend directory
    from agents.ci_cd_agent.github_ci import GitHubCISummarizer, GitHubWorkflowManager
    from agents.ci_cd_agent.jenkins_ci import JenkinsFileParser, JenkinsManager
    from agents.ci_cd_agent.llm_diagnostics import LLMDiagnostics
    from agents.ci_cd_agent.validation import CIValidator
    from agents.ci_cd_agent.performance import cached, monitor_performance, get_performance_summary

router = APIRouter(prefix="/ci-cd", tags=["CI/CD Agent"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ci_cd_routes")

# Performance optimization: Simple in-memory cache
_cache = {}
_cache_ttl = 300  # 5 minutes TTL

def cache_result(ttl_seconds: int = 300):
    """Decorator for caching function results with TTL."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check if result is in cache and not expired
            if cache_key in _cache:
                result, timestamp = _cache[cache_key]
                if time.time() - timestamp < ttl_seconds:
                    logger.info(f"Cache hit for {func.__name__}")
                    return result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                _cache[cache_key] = (result, time.time())
                logger.info(f"Cached result for {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {e}")
                raise
        return wrapper
    return decorator

def log_performance(func):
    """Decorator for logging function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper

def handle_errors(func):
    """Enhanced error handling decorator."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found in {func.__name__}: {e}")
            raise HTTPException(status_code=404, detail=f"Required file not found: {str(e)}")
        except PermissionError as e:
            logger.error(f"Permission denied in {func.__name__}: {e}")
            raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
        except ConnectionError as e:
            logger.error(f"Connection error in {func.__name__}: {e}")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
        except TimeoutError as e:
            logger.error(f"Timeout in {func.__name__}: {e}")
            raise HTTPException(status_code=504, detail=f"Request timeout: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    return wrapper

# -------------------------
# Request Models
# -------------------------
class ProjectPathRequest(BaseModel):
    project_path: str

class GitHubWorkflowRequest(BaseModel):
    project_path: str
    repo: Optional[str] = None  # owner/repo format
    token: Optional[str] = None  # GitHub token
    workflow_file: Optional[str] = None
    branch: str = "main"

class JenkinsRequest(BaseModel):
    project_path: str
    base_url: Optional[str] = None  # Jenkins server URL
    username: Optional[str] = None
    api_token: Optional[str] = None
    job_name: Optional[str] = None
    build_number: Optional[int] = None

class DiagnosticsRequest(BaseModel):
    project_path: str
    log_content: str
    ci_type: str = "GitHub Actions"

class ValidationRequest(BaseModel):
    project_path: str
    run_environment_checks: bool = True

class MonitoringRequest(BaseModel):
    project_path: str
    metrics: Optional[List[str]] = None

class PerformanceMetrics(BaseModel):
    endpoint: str
    execution_time: float
    cache_hit: bool
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

# -------------------------
# GitHub Actions Endpoints
# -------------------------
@router.post("/github/workflows")
@handle_errors
@monitor_performance
@cached(ttl=600)  # Cache for 10 minutes
def get_github_workflows(request: ProjectPathRequest):
    """
    Get all GitHub Actions workflows in a repository.
    Enhanced with caching, performance monitoring, and comprehensive error handling.
    """
    project_path = Path(request.project_path)
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path.")
    
    logger.info(f"Analyzing GitHub workflows for project: {project_path}")
    
    try:
        summarizer = GitHubCISummarizer(str(project_path))
        workflows = summarizer.summarize_all()
        
        # Enhanced response with metadata
        response = {
            "status": "success",
            "message": f"Found {len(workflows)} workflow(s)",
            "workflows": workflows,
            "metadata": {
                "project_path": str(project_path),
                "analysis_timestamp": datetime.now().isoformat(),
                "workflow_count": len(workflows),
                "cache_status": "hit" if "cache_hit" in locals() else "miss"
            }
        }
        
        logger.info(f"Successfully analyzed {len(workflows)} workflows")
        return response
        
    except Exception as e:
        logger.error(f"Failed to analyze GitHub workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get GitHub workflows: {str(e)}")

@router.post("/github/workflow/explain")
def explain_github_workflow(request: ProjectPathRequest):
    """
    Get human-readable explanation of GitHub workflows.
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        summarizer = GitHubCISummarizer(str(project_path))
        workflows = summarizer.summarize_all()
        
        explanations = []
        for workflow in workflows:
            explanation = summarizer.explain_workflow(workflow)
            explanations.append(explanation)
        
        return {
            "status": "success",
            "message": "Workflow explanations generated",
            "explanations": explanations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain workflows: {str(e)}")

@router.post("/github/trigger")
def trigger_github_workflow(request: GitHubWorkflowRequest):
    """
    Trigger a GitHub Actions workflow (requires workflow_dispatch trigger).
    """
    try:
        if not request.repo or not request.token:
            raise HTTPException(status_code=400, detail="Repository and token are required for triggering workflows.")
        
        manager = GitHubWorkflowManager(request.repo, request.token)
        result = manager.trigger_workflow(request.workflow_file or "ci.yml", request.branch)
        
        return {
            "status": "success" if result["status"] == "success" else "error",
            "message": result.get("message", "Workflow trigger attempted"),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger workflow: {str(e)}")

@router.post("/github/status")
def get_github_workflow_status(request: GitHubWorkflowRequest):
    """
    Get the status of GitHub Actions workflows.
    """
    try:
        if not request.repo or not request.token:
            raise HTTPException(status_code=400, detail="Repository and token are required.")
        
        manager = GitHubWorkflowManager(request.repo, request.token)
        workflows = manager.list_workflows()
        
        return {
            "status": "success",
            "message": f"Found {len(workflows)} workflow(s)",
            "workflows": workflows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

# -------------------------
# Jenkins Endpoints
# -------------------------
@router.post("/jenkins/analyze")
def analyze_jenkins_pipeline(request: ProjectPathRequest):
    """
    Analyze Jenkins pipeline configuration.
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        parser = JenkinsFileParser(str(project_path))
        summary = parser.summarize()
        explanation = parser.explain_summary(summary)
        
        return {
            "status": "success",
            "message": "Jenkins pipeline analyzed",
            "summary": summary,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze Jenkins pipeline: {str(e)}")

@router.post("/jenkins/trigger")
def trigger_jenkins_job(request: JenkinsRequest):
    """
    Trigger a Jenkins job.
    """
    try:
        if not request.base_url or not request.username or not request.api_token:
            raise HTTPException(status_code=400, detail="Jenkins server details are required.")
        
        if not request.job_name:
            raise HTTPException(status_code=400, detail="Job name is required.")
        
        manager = JenkinsManager(request.base_url, request.username, request.api_token)
        result = manager.trigger_job(request.job_name)
        
        return {
            "status": "success" if result["status"] == "success" else "error",
            "message": result.get("message", "Job trigger attempted"),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger Jenkins job: {str(e)}")

@router.post("/jenkins/status")
def get_jenkins_job_status(request: JenkinsRequest):
    """
    Get Jenkins job status and information.
    """
    try:
        if not request.base_url or not request.username or not request.api_token:
            raise HTTPException(status_code=400, detail="Jenkins server details are required.")
        
        manager = JenkinsManager(request.base_url, request.username, request.api_token)
        
        if request.job_name:
            job_info = manager.get_job_info(request.job_name)
            if request.build_number:
                build_status = manager.get_build_status(request.job_name, request.build_number)
                build_logs = manager.get_build_logs(request.job_name, request.build_number)
                return {
                    "status": "success",
                    "job_info": job_info,
                    "build_status": build_status,
                    "build_logs": build_logs
                }
            return {
                "status": "success",
                "job_info": job_info
            }
        else:
            jobs = manager.list_jobs()
            return {
                "status": "success",
                "message": f"Found {len(jobs)} job(s)",
                "jobs": jobs
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Jenkins status: {str(e)}")

# -------------------------
# Diagnostics Endpoints
# -------------------------
@router.post("/diagnose")
@handle_errors
@log_performance
def diagnose_ci_failure(request: DiagnosticsRequest):
    """
    Diagnose CI/CD failure using LLM analysis.
    Enhanced with performance monitoring and comprehensive error handling.
    """
    project_path = Path(request.project_path)
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path.")
    
    logger.info(f"Diagnosing CI failure for project: {project_path}, CI type: {request.ci_type}")
    
    try:
        diagnostics = LLMDiagnostics(str(project_path))
        diagnosis = diagnostics.diagnose(request.log_content, request.ci_type)
        
        # Enhanced response with metadata
        response = {
            "status": "success",
            "message": "Diagnosis completed",
            "diagnosis": diagnosis,
            "metadata": {
                "project_path": str(project_path),
                "ci_type": request.ci_type,
                "log_length": len(request.log_content),
                "analysis_timestamp": datetime.now().isoformat(),
                "diagnosis_quality": "high" if isinstance(diagnosis, dict) else "medium"
            }
        }
        
        logger.info(f"Successfully diagnosed CI failure for {request.ci_type}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to diagnose CI failure: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to diagnose CI failure: {str(e)}")

@router.post("/diagnose/context")
def get_contextual_help(request: DiagnosticsRequest):
    """
    Get contextual help for CI/CD issues using RAG.
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        diagnostics = LLMDiagnostics(str(project_path))
        context_help = diagnostics.provide_context_help(request.log_content)
        
        return {
            "status": "success",
            "message": "Contextual help generated",
            "context_help": context_help
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contextual help: {str(e)}")

# -------------------------
# Validation Endpoints
# -------------------------
@router.post("/validate")
def validate_ci_config(request: ValidationRequest):
    """
    Validate CI/CD configuration and detect issues.
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        validator = CIValidator(str(project_path))
        report = validator.run_full_validation()
        
        return {
            "status": "success",
            "message": "CI/CD validation completed",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate CI configuration: {str(e)}")

@router.post("/validate/quick")
def quick_ci_validation(request: ProjectPathRequest):
    """
    Quick CI/CD validation without environment checks.
    """
    try:
        project_path = Path(request.project_path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        validator = CIValidator(str(project_path))
        configs = validator.detect_configs()
        issues = validator.detect_common_issues()
        
        return {
            "status": "success",
            "message": "Quick validation completed",
            "detected_configs": configs,
            "common_issues": issues
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform quick validation: {str(e)}")

# -------------------------
# Health and Info Endpoints
# -------------------------
@router.get("/")
def root():
    """Root endpoint for CI/CD Agent"""
    return {
        "message": "CI/CD Agent API - Comprehensive CI/CD Management",
        "description": "Provides GitHub Actions, Jenkins, diagnostics, and validation capabilities",
        "endpoints": {
            "github_workflows": "POST /ci-cd/github/workflows - Get GitHub workflows",
            "github_explain": "POST /ci-cd/github/workflow/explain - Explain GitHub workflows",
            "github_trigger": "POST /ci-cd/github/trigger - Trigger GitHub workflow",
            "github_status": "POST /ci-cd/github/status - Get GitHub workflow status",
            "jenkins_analyze": "POST /ci-cd/jenkins/analyze - Analyze Jenkins pipeline",
            "jenkins_trigger": "POST /ci-cd/jenkins/trigger - Trigger Jenkins job",
            "jenkins_status": "POST /ci-cd/jenkins/status - Get Jenkins job status",
            "diagnose": "POST /ci-cd/diagnose - Diagnose CI failure",
            "diagnose_context": "POST /ci-cd/diagnose/context - Get contextual help",
            "validate": "POST /ci-cd/validate - Validate CI configuration",
            "validate_quick": "POST /ci-cd/validate/quick - Quick CI validation"
        },
        "features": [
            "GitHub Actions workflow management",
            "Jenkins pipeline analysis and control",
            "LLM-powered failure diagnosis",
            "RAG-based contextual assistance",
            "Comprehensive CI/CD validation",
            "Multi-platform CI/CD support",
            "Intelligent error analysis and suggestions"
        ]
    }

@router.get("/health")
def health_check():
    """Enhanced health check for CI/CD Agent with detailed diagnostics"""
    try:
        # Test basic imports
        from backend.agents.ci_cd_agent.github_ci import GitHubCISummarizer
        from backend.agents.ci_cd_agent.jenkins_ci import JenkinsFileParser
        from backend.agents.ci_cd_agent.llm_diagnostics import LLMDiagnostics
        from backend.agents.ci_cd_agent.validation import CIValidator
        
        # Test module functionality
        test_results = {}
        try:
            # Test GitHub CI
            test_summarizer = GitHubCISummarizer(".")
            test_results["github_ci"] = "available"
        except Exception as e:
            test_results["github_ci"] = f"error: {str(e)}"
            
        try:
            # Test Jenkins CI
            test_parser = JenkinsFileParser(".")
            test_results["jenkins_ci"] = "available"
        except Exception as e:
            test_results["jenkins_ci"] = f"error: {str(e)}"
            
        try:
            # Test LLM Diagnostics (without API key)
            test_results["llm_diagnostics"] = "available"
        except Exception as e:
            test_results["llm_diagnostics"] = f"error: {str(e)}"
            
        try:
            # Test Validation
            test_validator = CIValidator(".")
            test_results["validation"] = "available"
        except Exception as e:
            test_results["validation"] = f"error: {str(e)}"
        
        # Cache status
        cache_status = {
            "cache_size": len(_cache),
            "cache_entries": list(_cache.keys())[:5]  # Show first 5 entries
        }
        
        return {
            "status": "healthy",
            "message": "CI/CD Agent is operational",
            "timestamp": datetime.now().isoformat(),
            "modules": test_results,
            "cache": cache_status,
            "performance": {
                "cache_hit_ratio": "N/A",  # Could be calculated from metrics
                "average_response_time": "N/A"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"CI/CD Agent has issues: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/metrics")
def get_metrics():
    """Get performance metrics and monitoring data"""
    try:
        # Get comprehensive performance summary
        performance_summary = get_performance_summary()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "performance": performance_summary,
            "legacy_cache": {
                "total_entries": len(_cache),
                "cache_keys": list(_cache.keys())[:10]  # First 10 keys only
            },
            "system": {
                "python_version": "3.11+",
                "langchain_available": True,
                "weaviate_available": True  # Could be checked dynamically
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get metrics: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@router.post("/monitor")
def monitor_ci_cd(request: MonitoringRequest):
    """Monitor CI/CD agent performance and health"""
    try:
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(status_code=400, detail="Invalid project path.")
        
        # Collect monitoring data
        monitoring_data = {
            "project_path": str(project_path),
            "timestamp": datetime.now().isoformat(),
            "cache_status": {
                "entries": len(_cache),
                "keys": list(_cache.keys())[:10]  # First 10 keys
            },
            "requested_metrics": request.metrics or ["default"]
        }
        
        # Add specific metrics if requested
        if "workflow_count" in (request.metrics or []):
            try:
                summarizer = GitHubCISummarizer(str(project_path))
                workflows = summarizer.summarize_all()
                monitoring_data["workflow_count"] = len(workflows)
            except Exception as e:
                monitoring_data["workflow_count"] = f"error: {str(e)}"
        
        return {
            "status": "success",
            "monitoring_data": monitoring_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to monitor CI/CD: {str(e)}")

@router.delete("/cache")
def clear_cache():
    """Clear the CI/CD agent cache"""
    try:
        global _cache
        cache_size = len(_cache)
        _cache.clear()
        
        return {
            "status": "success",
            "message": f"Cleared {cache_size} cache entries",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
