"""Pydantic models for API requests and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field, validator
import re


class AnalyzeRepoRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str = Field(..., description="Git repository URL to analyze")
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        """Validate and normalize repository URL."""
        if not v:
            raise ValueError('repo_url cannot be empty')
        
        # Remove .git suffix if present for validation
        normalized = v.rstrip('.git')
        
        # Check if it's a valid GitHub URL format
        github_pattern = r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
        if not re.match(github_pattern, normalized):
            raise ValueError('Only GitHub repositories are currently supported. URL must match: https://github.com/owner/repo')
        
        return normalized


class AnalysisStats(BaseModel):
    """Statistics from repository analysis."""
    files_scanned: int = Field(0, description="Total files processed")
    files_parsed: int = Field(0, description="Files successfully parsed")
    files_embedded: int = Field(0, description="Files successfully embedded")
    parse_engines_used: Dict[str, int] = Field(default_factory=dict, description="Parse engine usage count")
    skipped_files: List[Dict[str, Any]] = Field(default_factory=list, description="Files skipped with reasons")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors encountered")


class RepoStructure(BaseModel):
    """High-level repository structure mapping."""
    root: str
    folders: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    main_modules: List[str] = Field(default_factory=list)


class ComponentSummary(BaseModel):
    """Detected key components in the repository."""
    apis: List[str] = Field(default_factory=list)
    database_models: List[str] = Field(default_factory=list)
    frontend_modules: List[str] = Field(default_factory=list)
    backend_modules: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)


class DependencyInfo(BaseModel):
    """Dependencies extracted from manifest files."""
    requirements: List[str] = Field(default_factory=list)
    package_json: Dict[str, Any] = Field(default_factory=dict)
    pom_xml: Dict[str, Any] = Field(default_factory=dict)


class FrameworkInfo(BaseModel):
    """Detected frameworks and versions where available."""
    python_frameworks: List[str] = Field(default_factory=list)
    js_frameworks: List[str] = Field(default_factory=list)
    java_frameworks: List[str] = Field(default_factory=list)


class CiInfo(BaseModel):
    """CI/CD and tests metadata."""
    has_tests: bool = False
    test_paths: List[str] = Field(default_factory=list)
    ci_files: List[str] = Field(default_factory=list)


class ChunkSummary(BaseModel):
    """Summary of a code/doc chunk used for embeddings."""
    file_path: str
    kind: str  # code_function, code_class, code_file, doc_paragraph
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    engine: Optional[str] = None


class AnalyzeRepoResponse(BaseModel):
    """Response model for repository analysis."""
    success: bool = Field(..., description="Whether analysis completed successfully")
    message: str = Field(..., description="Human-readable status message")
    repo_url: str = Field(..., description="Repository URL that was analyzed")
    repo_path: Optional[str] = Field(None, description="Local path where repo was cloned")
    stats: AnalysisStats = Field(..., description="Analysis statistics")
    weaviate_enabled: bool = Field(..., description="Whether embeddings were stored in Weaviate")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")
    structure: Optional[RepoStructure] = None
    components: Optional[ComponentSummary] = None
    dependencies: Optional[DependencyInfo] = None
    frameworks: Optional[FrameworkInfo] = None
    ci: Optional[CiInfo] = None
    chunks_index: List[ChunkSummary] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field("1.0.0", description="API version")


class ReadyResponse(BaseModel):
    """Readiness check response model."""
    ready: bool = Field(..., description="Whether service is ready to accept requests")
    checks: Dict[str, bool] = Field(..., description="Individual component readiness")
    timestamp: str = Field(..., description="Current timestamp")
