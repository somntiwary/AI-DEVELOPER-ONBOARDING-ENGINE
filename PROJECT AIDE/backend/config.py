import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

# Vector Database
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
ENABLE_WEAVIATE = os.getenv("ENABLE_WEAVIATE", "true").lower() == "true"

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional

# Repository Analysis Limits
MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", "100"))  # 100MB default
CLONE_TIMEOUT_SECONDS = int(os.getenv("CLONE_TIMEOUT_SECONDS", "300"))  # 5 minutes default
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "github.com").split(",")

# Embedding Settings
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "10"))
EMBED_TIMEOUT_SECONDS = int(os.getenv("EMBED_TIMEOUT_SECONDS", "30"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
