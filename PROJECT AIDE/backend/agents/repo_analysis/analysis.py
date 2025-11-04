import os
import time
from typing import Dict, Any, List, Tuple
try:
    # Try importing as if running from project root
    from backend.utils.embeddings import embed_text, store_embedding
    from backend.agents.repo_analysis.parser import parse_python_file_safe
    from backend.agents.repo_analysis.repo_loader import clone_repo
    from backend.models import AnalysisStats, RepoStructure, ComponentSummary, DependencyInfo, FrameworkInfo, CiInfo, ChunkSummary
    from config import ENABLE_WEAVIATE
except ImportError:
    # Import directly when running from backend directory
    from utils.embeddings import embed_text, store_embedding
    from agents.repo_analysis.parser import parse_python_file_safe
    from agents.repo_analysis.repo_loader import clone_repo
    from models import AnalysisStats, RepoStructure, ComponentSummary, DependencyInfo, FrameworkInfo, CiInfo, ChunkSummary
    from config import ENABLE_WEAVIATE

def analyze_repository(repo_url: str) -> Dict[str, Any]:
    """
    Analyze a repository and return structured results.
    
    Args:
        repo_url: Git repository URL to analyze
        
    Returns:
        Dictionary with analysis results and statistics
    """
    start_time = time.time()
    
    # Initialize stats and containers
    stats = AnalysisStats()
    structure = RepoStructure(root="", folders=[], files=[], main_modules=[])
    components = ComponentSummary()
    dependencies = DependencyInfo()
    frameworks = FrameworkInfo()
    ci = CiInfo()
    chunks_index: List[ChunkSummary] = []

    def is_entry_point(path: str) -> bool:
        base = os.path.basename(path).lower()
        return base in {"main.py", "app.py", "wsgi.py", "asgi.py", "manage.py"}

    def detect_components_for_file(path: str, code: str) -> None:
        lower = code.lower()
        # APIs
        if ("fastapi" in lower) or ("flask" in lower) or ("@app.route" in lower) or ("apirouter(" in lower):
            components.apis.append(path)
        # DB Models
        if ("sqlalchemy" in lower) or ("models.Model" in code) or ("django.db" in lower):
            components.database_models.append(path)
        # Backend/Frontend heuristic by path
        if any(seg in path.replace("\\", "/").split("/") for seg in ["backend", "server", "api"]):
            components.backend_modules.append(path)
        if any(seg in path.replace("\\", "/").split("/") for seg in ["frontend", "client", "web", "ui"]):
            components.frontend_modules.append(path)
        # Entry points
        if is_entry_point(path):
            components.entry_points.append(path)

    def add_chunk(file_path: str, kind: str, start: int = None, end: int = None, engine: str = None, text: str = "") -> None:
        emb, ok = embed_text(text)
        if ok and emb:
            if ENABLE_WEAVIATE:
                store_embedding(text, {"file_path": file_path, "kind": kind, "start": start, "end": end, "engine": engine}, vector=emb)
            stats.files_embedded += 1
        chunks_index.append(ChunkSummary(file_path=file_path, kind=kind, start_line=start, end_line=end, engine=engine))

    def extract_dependencies(repo_root: str) -> None:
        # requirements.txt
        req = os.path.join(repo_root, "requirements.txt")
        if os.path.exists(req):
            try:
                with open(req, "r", encoding="utf-8", errors="ignore") as f:
                    dependencies.requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                frameworks.python_frameworks.extend([dep for dep in dependencies.requirements if any(x in dep.lower() for x in ["fastapi", "flask", "django", "sqlalchemy"])])
            except Exception:
                pass
        # package.json
        pkg = os.path.join(repo_root, "package.json")
        if os.path.exists(pkg):
            try:
                import json
                with open(pkg, "r", encoding="utf-8", errors="ignore") as f:
                    dependencies.package_json = json.load(f)
                deps = {**dependencies.package_json.get("dependencies", {}), **dependencies.package_json.get("devDependencies", {})}
                fw = [k for k in deps.keys() if k in ["react", "vue", "next", "nuxt", "angular", "express", "koa", "hapi"]]
                frameworks.js_frameworks.extend(fw)
            except Exception:
                pass
        # pom.xml (very light parse)
        pom = os.path.join(repo_root, "pom.xml")
        if os.path.exists(pom):
            try:
                with open(pom, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                if "spring-boot" in content:
                    frameworks.java_frameworks.append("spring-boot")
                dependencies.pom_xml = {"present": True}
            except Exception:
                pass

    def detect_ci(repo_root: str) -> None:
        # tests
        test_paths: List[str] = []
        for candidate in ["tests", "test", "__tests__"]:
            p = os.path.join(repo_root, candidate)
            if os.path.exists(p):
                ci.has_tests = True
                test_paths.append(p)
        ci.test_paths = test_paths
        # CI files
        ci_files: List[str] = []
        gh = os.path.join(repo_root, ".github", "workflows")
        if os.path.isdir(gh):
            for f in os.listdir(gh):
                if f.endswith((".yml", ".yaml")):
                    ci_files.append(os.path.join(gh, f))
        for fname in [".circleci/config.yml", "Jenkinsfile", "azure-pipelines.yml", ".gitlab-ci.yml"]:
            p = os.path.join(repo_root, fname)
            if os.path.exists(p):
                ci_files.append(p)
        ci.ci_files = ci_files
    
    try:
        # Clone repository
        repo_path = clone_repo(repo_url)
        structure.root = repo_path
        
        # Process Python files
        for root, dirs, files in os.walk(repo_path):
            # Collect structure
            for d in dirs:
                structure.folders.append(os.path.join(root, d))
            for fn in files:
                full = os.path.join(root, fn)
                structure.files.append(full)
                if is_entry_point(full):
                    structure.main_modules.append(full)
            for f in files:
                if f.endswith(".py"):  # extend later for other languages
                    file_path = os.path.join(root, f)
                    stats.files_scanned += 1
                    
                    try:
                        # Parse file with fallback
                        code, tree_or_ast, engine = parse_python_file_safe(file_path)
                        stats.parse_engines_used[engine] = stats.parse_engines_used.get(engine, 0) + 1
                        stats.files_parsed += 1
                        # Detect components
                        detect_components_for_file(file_path, code)
                        # Chunking: naive function/class markers by lines (fallback when no detailed CST)
                        # For now, store full file as a chunk to ensure coverage
                        add_chunk(file_path, kind="code_file", start=1, end=code.count("\n") + 1, engine=engine, text=code)
                        
                    except Exception as e:
                        stats.errors.append({
                            "file": file_path,
                            "error": str(e),
                            "type": "processing_error"
                        })
            # Docs chunking for README and docs/*.md
            for fdoc in files:
                if fdoc.lower() in ["readme.md", "readme.txt"] or fdoc.lower().endswith(".md"):
                    doc_path = os.path.join(root, fdoc)
                    try:
                        with open(doc_path, "r", encoding="utf-8", errors="ignore") as df:
                            text = df.read()
                        # Simple paragraph chunking
                        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                        for p in paragraphs:
                            add_chunk(doc_path, kind="doc_paragraph", text=p)
                    except Exception as e:
                        stats.errors.append({
                            "file": doc_path,
                            "error": str(e),
                            "type": "doc_chunk_error"
                        })
                            
        # Extract dependencies and CI metadata after traversal
        extract_dependencies(repo_path)
        detect_ci(repo_path)
        
        processing_time = time.time() - start_time
        
        return {
            "repo_path": repo_path,
            "stats": stats.dict(),
            "structure": structure.dict(),
            "components": components.dict(),
            "dependencies": dependencies.dict(),
            "frameworks": frameworks.dict(),
            "ci": ci.dict(),
            "chunks_index": [c.dict() for c in chunks_index],
            "weaviate_enabled": ENABLE_WEAVIATE,
            "processing_time_seconds": processing_time
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        stats.errors.append({
            "error": str(e),
            "type": "fatal_error"
        })
        
        return {
            "repo_path": None,
            "stats": stats.dict(),
            "weaviate_enabled": ENABLE_WEAVIATE,
            "processing_time_seconds": processing_time,
            "error": str(e)
        }
