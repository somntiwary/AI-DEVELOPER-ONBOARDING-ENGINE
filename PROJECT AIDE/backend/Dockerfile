FROM python:3.11-slim AS base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements.txt* ./
RUN python3 -m pip install --upgrade pip setuptools wheel \
    && if [ -f requirements.txt ]; then \
        python3 -m pip install --no-cache-dir --default-timeout=60 -r requirements.txt; \
    fi
COPY . .
CMD ["bash"]
