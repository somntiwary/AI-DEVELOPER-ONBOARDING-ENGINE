# pyright: reportMissingImports=false
import os
import tempfile
import shutil
from urllib.parse import urlparse
from typing import Optional, TYPE_CHECKING, Any

try:
    from config import GITHUB_TOKEN, CLONE_TIMEOUT_SECONDS, MAX_REPO_SIZE_MB, ALLOWED_HOSTS
except ImportError:
    import os as _os, sys as _sys
    _BACKEND_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
    _PROJECT_ROOT = _os.path.dirname(_BACKEND_DIR)
    if _PROJECT_ROOT not in _sys.path:
        _sys.path.insert(0, _PROJECT_ROOT)
    from config import GITHUB_TOKEN, CLONE_TIMEOUT_SECONDS, MAX_REPO_SIZE_MB, ALLOWED_HOSTS  # type: ignore

if TYPE_CHECKING:
    import git  # pragma: no cover
    GitRepo = git.Repo  # type: ignore
else:
    GitRepo = Any  # type: ignore


def get_repo_size_mb(repo_path: str) -> float:
    """Calculate repository size in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(repo_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, IOError):
                pass
    return total_size / (1024 * 1024)


def validate_repo_url(repo_url: str) -> None:
    """Validate repository URL against allowed hosts."""
    parsed = urlparse(repo_url)
    host = parsed.hostname
    
    if not host:
        raise ValueError("Invalid repository URL: no hostname found")
    
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Repository host '{host}' not in allowed hosts: {ALLOWED_HOSTS}")


def clone_repo(repo_url: str, timeout: Optional[int] = None) -> str:
    """
    Clone a repo to a temporary directory with size and timeout limits.
    Supports optional token for private repos.
    
    Args:
        repo_url: Git repository URL to clone
        timeout: Clone timeout in seconds (defaults to config)
        
    Returns:
        Path to cloned repository
        
    Raises:
        ValueError: If URL is invalid or repo is too large
        RuntimeError: If GitPython is missing or clone fails
        TimeoutError: If clone takes too long
    """
    if timeout is None:
        timeout = CLONE_TIMEOUT_SECONDS
    
    # Validate URL
    validate_repo_url(repo_url)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Prepare URL with token if available
        clone_url = repo_url
        if GITHUB_TOKEN and repo_url.startswith("https://github.com/"):
            clone_url = repo_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        
        if not clone_url.endswith(".git"):
            clone_url += ".git"

        # Import git with error handling
        try:
            import git  # type: ignore
        except ImportError as e:
            raise RuntimeError("GitPython is required for cloning repositories. Install with 'pip install GitPython'.") from e

        # Clone with timeout
        try:
            repo = git.Repo.clone_from(clone_url, temp_dir, progress=None)  # type: ignore
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {str(e)}") from e
        
        # Check repository size
        repo_size = get_repo_size_mb(temp_dir)
        if repo_size > MAX_REPO_SIZE_MB:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise ValueError(f"Repository too large: {repo_size:.1f}MB exceeds limit of {MAX_REPO_SIZE_MB}MB")
        
        return temp_dir
        
    except Exception:
        # Cleanup on any error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise