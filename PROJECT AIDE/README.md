## Project AIDE

An AI-assisted Developer Enablement platform that analyzes repositories, generates documentation, assists with Q&A over your codebase, automates environment setup, and integrates CI/CD diagnostics — all exposed via a FastAPI backend.

### Key Capabilities
- **Repository Analysis**: Parse and index code with Tree-sitter, summarize structure, and build embeddings for RAG.
- **Documentation Agent**: Auto-generate README/API docs, query docs, and ingest into a vector DB (Weaviate) for semantic search.
- **QnA Agent**: Ask questions about your project; integrates repo analysis, docs, and environment knowledge.
- **Environment Setup**: Detect runtimes, resolve dependencies, and build dev containers programmatically.
- **Walkthroughs**: Guided onboarding steps with progress tracking and context-aware help.
- **CI/CD Agent**: Inspect GitHub Actions/Jenkins, explain pipelines, validate configs, and diagnose failures.
- **Feedback & Learning**: Collect feedback, analyze trends, and support model retraining workflows.

---

## Repository Structure

```text
PROJECT AIDE/
  backend/                  # FastAPI service and all agents
    agents/                 # Modular agents (repo_analysis, docs, qna, env_setup, ci_cd, feedback, walkthrough)
    routes/                 # FastAPI routers exposing agent APIs
    utils/                  # Shared utilities (embeddings, logging, yaml, docker helpers)
    docs/auto_generated/    # Outputs from documentation generator (README_AUTO.md, API_DOCS.md)
    backend/feedback_data/  # Local JSON store for feedback/analytics, models
    weaviate_data/          # Optional local Weaviate data (if configured)
    requirements.txt        # Python dependencies
    Dockerfile              # Backend Docker build
    docker-compose.yml      # (Present; if empty, prefer Dockerfile usage below)
    main.py                 # FastAPI app entry
    config.py               # Environment variables and feature flags
    models.py               # Pydantic models for API I/O
    tests*                  # test_* files for agents
  docs/                     # Project-level documentation (plus auto_generated in backend)
  logs/                     # Service logs (e.g., aide.log)
  tree-sitter-python/       # Embedded Tree-sitter Python grammar (vendored)
  ../REACT DEMO/reactaide/  # React frontend (Create React App)
```

---

## Tech Stack
- **Backend**: FastAPI, Uvicorn
- **Parsing/Analysis**: Tree-sitter
- **RAG/LLM**: Weaviate (optional), LangChain, LlamaIndex, OpenAI, Transformers, FAISS
- **Docs Processing**: markdown2, PyYAML, python-docx, PyMuPDF, pdfminer.six, Tesseract OCR
- **Env Automation**: Docker SDK
- **CI/CD**: Jenkins API, GitHub integrations
- **Telemetry/UX**: loguru, rich, Streamlit (optional dashboards), W&B/MLflow/DVC for learning

See `backend/requirements.txt` for exact versions.

---

## Prerequisites
- Python 3.11
- Git
- (Optional) Docker (for containerized runs)
- (Optional) Weaviate running locally or remotely for RAG features
- (Optional) Tesseract OCR binary if using OCR features (`pytesseract`)

Windows users: Recommended to run in a dedicated virtual environment and install wheels for heavy dependencies where needed. The repo includes a vendored `tree-sitter-python` to ease parsing support.

---

## Quick Start (Local)

1) Create and activate a virtual environment
```bash
python -m venv .venv
".venv\\Scripts\\activate"   # PowerShell: . .venv/Scripts/Activate.ps1
```

2) Install dependencies
```bash
pip install --upgrade pip wheel setuptools
pip install -r backend/requirements.txt
```

3) Configure environment variables (create `.env` in `backend/`)
```env
# Vector DB (optional)
WEAVIATE_URL=http://localhost:8080
ENABLE_WEAVIATE=true

# GitHub (optional)
GITHUB_TOKEN=

# Limits and logging (optional)
MAX_REPO_SIZE_MB=100
CLONE_TIMEOUT_SECONDS=300
ALLOWED_HOSTS=github.com
EMBED_BATCH_SIZE=10
EMBED_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
```

4) Run the API
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

5) Open the docs: `http://localhost:8000/docs`

---

## Running with Docker

Build:
```bash
cd backend
docker build -t project-aide-backend:latest .
```

Run:
```bash
docker run --rm -p 8000:8000 \
  --env-file .env \
  -v "%cd%":/workspace \
  project-aide-backend:latest \
  bash -lc "uvicorn backend.main:app --host 0.0.0.0 --port 8000"
```

Notes:
- A `docker-compose.yml` exists but may be a placeholder. Prefer the Dockerfile flow above or extend compose to include Weaviate and the backend.
- Mounting the workspace lets agents analyze local repos by path.

---

## Core Configuration
`backend/config.py` reads from environment and `.env`:
- **WEAVIATE_URL**: Weaviate endpoint (e.g., `http://localhost:8080`)
- **ENABLE_WEAVIATE**: `true|false` to enable RAG-backed features
- **GITHUB_TOKEN**: Optional token for GitHub API calls
- **MAX_REPO_SIZE_MB**, **CLONE_TIMEOUT_SECONDS**, **ALLOWED_HOSTS**: Repo analysis limits
- **EMBED_* settings**: Embedding batching/timeouts
- **LOG_LEVEL**: Logging verbosity

---

## API Overview

Base service endpoints:
- `GET /` → basic service info
- `GET /healthz` → health
- `GET /readyz` → readiness (checks Weaviate if enabled)

Agents (prefixes from `backend/main.py`):

- **Repository Analysis** (`/api/repo`)
  - `POST /analyze` → Analyze a GitHub repo URL and return structure, stats, embeddings info

- **Environment Setup** (`/api/env` with router prefix `/environment`)
  - `POST /environment/analyze` → Detect runtimes and dependencies for a local project path
  - `POST /environment/build` → Build a dev container (Docker/DevContainer)
  - `POST /environment/validate` → Validate container or local environment
  - `GET  /environment/status/{container_id}` → Check container status

- **Documentation** (`/api/documentation`)
  - `POST /generate` → Generate README and API docs into `docs/auto_generated`
  - `POST /query` → Ask questions about docs; uses Weaviate if enabled, else LLM
  - `POST /ingest` → Ingest docs into Weaviate
  - `POST /reset` → Reset Weaviate schema for docs
  - `GET  /download/{file_type}?project_path=...` → Download generated docs

- **QnA** (`/api/qna`)
  - `POST /initialize` → Build a knowledge base for a project path
  - `POST /ask` → Ask a question about the project
  - `POST /analyze-intent`, `POST /suggest-followups`, `POST /history`, `POST /summary`, `POST /reset`, `GET /capabilities`

- **Walkthrough** (`/api/walkthrough`)
  - `POST /initialize` → Initialize onboarding flow
  - `POST /steps` → Get step list; `POST /execute-step` → Execute; `POST /get-help` → Context help
  - `POST /session-status`, `POST /resume`, `POST /reset`

- **CI/CD** (`/api/ci-cd`)
  - GitHub: `POST /github/workflows`, `POST /github/workflow/explain`, `POST /github/trigger`, `POST /github/status`
  - Jenkins: `POST /jenkins/analyze`, `POST /jenkins/trigger`, `POST /jenkins/status`
  - Diagnostics/Validation: `POST /diagnose`, `POST /diagnose/context`, `POST /validate`, `POST /validate/quick`

- **Feedback & Learning** (`/api/feedback`)
  - Collect: `POST /collect`, `POST /survey/satisfaction`, `POST /analyze/failure`
  - Analytics: `POST /analytics/satisfaction`, `POST /analytics/performance`, `POST /analytics/improvements`, `POST /analytics/insights`, `POST /analytics/dashboard`
  - Retraining: `POST /retrain/prepare`, `POST /retrain/execute`, `GET /retrain/status`
  - Knowledge updates: `POST /knowledge/update`

Explore full OpenAPI at `http://localhost:8000/docs`.

---

## Frontend (React)

Location: `REACT DEMO/reactaide`

### Stack
- React 18 (Create React App 5)
- React Router DOM 6
- Tailwind CSS (+ forms plugin), PostCSS, Autoprefixer
- Axios, Framer Motion, React Hot Toast, React Markdown, React Syntax Highlighter, Recharts, Lucide icons

### Scripts
```bash
npm start   # dev server at http://localhost:3000
npm run build
npm test
```

### Setup
```bash
cd "REACT DEMO/reactaide"
npm install
npm start
```

Backend URL configuration (optional `.env` in `reactaide`):
```env
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_WEAVIATE_URL=http://localhost:8080
REACT_APP_ENABLE_WEAVIATE=true
```

Build artifacts are output to `reactaide/build/`. You can serve them behind any static host or proxy through the backend if desired.

Key folders:
```text
reactaide/
  src/
    pages/                 # CICD, Dashboard, Documentation, EnvironmentSetup, Feedback, QnA, RepositoryAnalysis, Settings, Walkthrough
    components/            # Layout and shared UI
    context/               # AppContext for global state
    hooks/                 # Custom hooks (e.g., useAgentState)
  public/                  # CRA public assets
  tailwind.config.js       # Tailwind setup
  postcss.config.js        # PostCSS pipeline
  package.json             # Dependencies and scripts
```

To integrate with the backend during development:
- Start backend at `http://localhost:8000`.
- Start frontend at `http://localhost:3000`.
- Ensure CORS in `backend/main.py` allows the frontend origin (lock down for production).

---

## Typical Workflows

1) Analyze a Repo (by URL)
```bash
POST /api/repo/analyze
{ "repo_url": "https://github.com/owner/repo" }
```

2) Build Knowledge and Ask Questions (local project path)
```bash
POST /api/qna/initialize
{ "project_path": "C:/path/to/your/project" }

POST /api/qna/ask
{ "project_path": "C:/path/to/your/project", "question": "What endpoints are available?" }
```

3) Generate Docs
```bash
POST /api/documentation/generate
{ "project_path": "C:/path/to/your/project" }
```

4) Environment Setup
```bash
POST /api/env/environment/analyze
{ "project_path": "C:/path/to/your/project" }
```

---

## Testing

- Unit-style tests are present in `backend/test_*`. You can run with:
```bash
pytest -q
```

Some tests may rely on local fixtures or optional services. Ensure environment variables are configured and optional services (e.g., Weaviate) are reachable when testing related features.

---

## Troubleshooting

- "Weaviate client not available" or readiness failing:
  - Set `ENABLE_WEAVIATE=false` to bypass RAG, or start Weaviate and set `WEAVIATE_URL`.
- Tree-sitter install issues on Windows:
  - Prefer prebuilt wheels; the repo vendors `tree-sitter-python` to reduce friction. Ensure `build-essential`-like tools are available if building from source.
- PDF/Doc parsing errors:
  - `PyMuPDF`/`pdfminer.six`/`pytesseract` may need system dependencies. Install Tesseract and ensure it’s on PATH for OCR.
- Docker build slowness/timeouts:
  - Use `--network host` in constrained environments or pre-install heavy wheels. Pin compatible versions from `requirements.txt`.

Logs: check `backend/logs/aide.log` or `logs/aide.log` for runtime traces.

---

## Security & Secrets
- Do not commit `.env` files or tokens. Use environment variables or secret stores.
- Limit CORS in production by configuring `allow_origins` in `backend/main.py`.

---

## Roadmap Ideas
- Docker Compose stack wiring backend + Weaviate
- Authn/z for admin endpoints
- Production observability (APM/metrics)
- Frontend UX for walkthroughs and dashboards (Streamlit or React)

---

## License
This repository includes vendored `tree-sitter-python` which is licensed under its own license (see `tree-sitter-python/LICENSE`). Ensure compatibility with your usage.


