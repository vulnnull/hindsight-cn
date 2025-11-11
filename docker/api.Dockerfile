FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only dependency files first for better caching
COPY memora/pyproject.toml memora/README.md /app/memora/
COPY memora/memora /app/memora/memora

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Install Python dependencies to a virtual environment
WORKDIR /app/memora
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
COPY --from=builder /app/memora /app/memora

# Set working directory
WORKDIR /app/memora

# Expose API port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://memora:memora_dev@postgres:5432/memora
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/memora

# Run the API server
CMD ["python", "-m", "memora.web.server", "--host", "0.0.0.0", "--port", "8080"]
