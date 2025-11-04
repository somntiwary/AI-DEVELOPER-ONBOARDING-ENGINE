from fastapi import APIRouter, HTTPException
from typing import Dict, Any
try:
    # Try importing as if running from project root
    from agents.repo_analysis.analysis import analyze_repository
    from models import AnalyzeRepoRequest, AnalyzeRepoResponse, AnalysisStats
    from utils.logging import logger
except ImportError:
    # Import directly when running from backend directory
    from agents.repo_analysis.analysis import analyze_repository
    from models import AnalyzeRepoRequest, AnalyzeRepoResponse, AnalysisStats
    from utils.logging import logger

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeRepoResponse)
def analyze_repo(request: AnalyzeRepoRequest) -> AnalyzeRepoResponse:
    """
    Analyze a Git repository for code patterns and generate embeddings.
    
    Args:
        request: Repository analysis request with validated URL
        
    Returns:
        Analysis results with statistics and processing details
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    try:
        logger.info(f"Starting analysis for repository: {request.repo_url}")
        
        # Run analysis
        result = analyze_repository(request.repo_url)
        
        # Check for fatal errors
        if "error" in result:
            logger.error(f"Analysis failed for {request.repo_url}: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {result['error']}"
            )
        
        # Create response
        stats = AnalysisStats(**result["stats"])
        
        response = AnalyzeRepoResponse(
            success=True,
            message="Repository analyzed successfully",
            repo_url=request.repo_url,
            repo_path=result.get("repo_path"),
            stats=stats,
            weaviate_enabled=result.get("weaviate_enabled", False),
            processing_time_seconds=result.get("processing_time_seconds"),
            structure=result.get("structure"),
            components=result.get("components"),
            dependencies=result.get("dependencies"),
            frameworks=result.get("frameworks"),
            ci=result.get("ci"),
            chunks_index=result.get("chunks_index", [])
        )
        
        logger.info(
            f"Analysis completed for {request.repo_url}: "
            f"{stats.files_scanned} files scanned, "
            f"{stats.files_parsed} parsed, "
            f"{stats.files_embedded} embedded"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error for {request.repo_url}: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error analyzing {request.repo_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")