# Dockerfile for Hindsight API (standalone)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy dependency files and README (required by pyproject.toml)
COPY hindsight-api/pyproject.toml ./
COPY hindsight-api/README.md ./

# Sync dependencies (creates lock file if needed)
RUN uv sync

# Copy source code
COPY hindsight-api/hindsight_api ./hindsight_api

# Expose API port
EXPOSE 8888

# Set environment variables
ENV HINDSIGHT_API_HOST=0.0.0.0
ENV HINDSIGHT_API_PORT=8888
ENV HINDSIGHT_API_LOG_LEVEL=info
ENV PATH="/app/.venv/bin:$PATH"

# Run the API server
CMD ["python", "-m", "hindsight_api.web.server"]
