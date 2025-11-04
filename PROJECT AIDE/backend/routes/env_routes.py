from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

try:
    # Try importing as if running from project root
    from agents.environment_setup.dependency_resolver import resolve_repo_dependencies
    from agents.environment_setup.container_builder import run_environment_setup
    from agents.environment_setup.runtime_detector import detect_runtimes
    from agents.environment_setup.environment_validator import EnvironmentValidator
except ImportError:
    # Import directly when running from backend directory
    from agents.environment_setup.dependency_resolver import resolve_repo_dependencies
    from agents.environment_setup.container_builder import run_environment_setup
    from agents.environment_setup.runtime_detector import detect_runtimes
    from agents.environment_setup.environment_validator import EnvironmentValidator

import logging

router = APIRouter(prefix="/environment", tags=["Environment Setup Agent"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("env_routes")

# -------------------------
# Request Models
# -------------------------
class EnvSetupRequest(BaseModel):
    project_path: str
    dockerize: bool = True
    runtime_hint: Optional[str] = None  # e.g., "python", "node", "java"


class EnvValidationRequest(BaseModel):
    container_id: Optional[str] = None
    project_path: Optional[str] = None


# -------------------------
# Routes
# -------------------------
@router.post("/analyze")
def analyze_environment(request: EnvSetupRequest):
    """
    Step 1: Analyze project dependencies and detect runtimes.
    """
    try:
        logger.info(f"Analyzing environment at {request.project_path}")

        runtime_info = detect_runtimes(request.project_path)
        dependencies = resolve_repo_dependencies(request.project_path)

        response = {
            "status": "success",
            "runtime": runtime_info,
            "dependencies": dependencies,
        }
        return response

    except Exception as e:
        logger.exception("Error analyzing environment")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
def build_environment(request: EnvSetupRequest):
    """
    Step 2: Build environment container (Docker/DevContainer).
    """
    try:
        logger.info(f"Building container for {request.project_path}")
        result = run_environment_setup(request.project_path, image_name="project-env:dev", build=request.dockerize)
        return {
            "status": "success" if result.success else "failed",
            "result": result.to_dict(),
        }

    except Exception as e:
        logger.exception("Error building environment container")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
def validate_environment(request: EnvValidationRequest):
    """
    Step 3: Validate the built environment.
    """
    try:
        validator = EnvironmentValidator()

        if request.container_id:
            validation_results = validator.validate_container(request.container_id)
        elif request.project_path:
            validation_results = validator.validate_local_environment(request.project_path)
        else:
            raise HTTPException(status_code=400, detail="Either container_id or project_path is required")

        return {
            "status": "success",
            "validation_results": validation_results
        }

    except Exception as e:
        logger.exception("Environment validation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{container_id}")
def get_container_status(container_id: str):
    """
    Step 4: Check running status of container.
    """
    try:
        # Minimal placeholder: could query `docker inspect` for status
        return {"container_id": container_id, "status": "unknown"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
