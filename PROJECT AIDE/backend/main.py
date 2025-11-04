from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
from datetime import datetime
try:
    # Try importing as if running from project root
    from routes import repo_routes, env_routes, doc_routes, qna_routes, walkthrough_routes, ci_cd_routes, feedback_routes
    from utils.logging import logger
    from models import HealthResponse, ReadyResponse
    from config import ENABLE_WEAVIATE
except ImportError:
    # Import directly when running from backend directory
    from routes import repo_routes, env_routes, doc_routes, qna_routes, walkthrough_routes, ci_cd_routes, feedback_routes
    from utils.logging import logger
    from models import HealthResponse, ReadyResponse
    from config import ENABLE_WEAVIATE

app = FastAPI(title="AIDE Backend", version="1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response

app.include_router(repo_routes.router, prefix="/api/repo", tags=["Repository Analysis"])
app.include_router(env_routes.router, prefix="/api/env", tags=["Environment Setup Agent"])
app.include_router(doc_routes.router, prefix="/api", tags=["Documentation Agent"])
app.include_router(qna_routes.router, prefix="/api", tags=["QnA Agent"])
app.include_router(walkthrough_routes.router, prefix="/api", tags=["Walkthrough Agent"])
app.include_router(ci_cd_routes.router, prefix="/api", tags=["CI/CD Agent"])
app.include_router(feedback_routes.router, prefix="/api", tags=["Feedback & Learning Agent"])

@app.get("/", response_model=dict)
def root():
    """Root endpoint with basic service info."""
    logger.info("AIDE backend running")
    return {"message": "AIDE Backend Live", "status": "ok"}

@app.get("/healthz", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )

@app.get("/readyz", response_model=ReadyResponse)
def readiness_check():
    """Readiness check endpoint."""
    checks = {
        "app_imports": True,
        "weaviate_enabled": ENABLE_WEAVIATE,
    }
    
    # Check if Weaviate is reachable if enabled
    if ENABLE_WEAVIATE:
        try:
            try:
                from utils.embeddings import get_weaviate_client
            except ImportError:
                from utils.embeddings import get_weaviate_client
            client = get_weaviate_client()
            checks["weaviate_reachable"] = client is not None
        except Exception:
            checks["weaviate_reachable"] = False
    else:
        checks["weaviate_reachable"] = True  # Not required
    
    ready = all(checks.values())
    
    return ReadyResponse(
        ready=ready,
        checks=checks,
        timestamp=datetime.utcnow().isoformat()
    )

if __name__ == "__main__":
    import uvicorn  # dev convenience when running directly
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
