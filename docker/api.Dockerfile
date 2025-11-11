FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY memora /app/memora

# Install Python dependencies
WORKDIR /app/memora
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://memora:memora_dev@postgres:5432/memora

# Run the API server
CMD ["python", "-m", "memora.web.server", "--host", "0.0.0.0", "--port", "8080"]
