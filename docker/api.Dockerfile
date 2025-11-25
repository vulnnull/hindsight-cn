FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only dependency files first for better caching
COPY hindsight-api/pyproject.toml hindsight-api/README.md /app/hindsight-api/
COPY hindsight-api/hindsight_api /app/hindsight-api/hindsight_api
COPY hindsight-api/alembic /app/hindsight-api/alembic

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Install Python dependencies to a virtual environment
WORKDIR /app/hindsight-api
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache -e .

# Production stage
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/hindsight-api /app/hindsight-api

# Set working directory
WORKDIR /app/hindsight-api

# Expose API port
EXPOSE 8888

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://hindsight:hindsight_dev@postgres:5432/hindsight
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/hindsight-api

# Run the API server
CMD ["python", "-m", "hindsight_api.web.server", "--host", "0.0.0.0", "--port", "8888"]
