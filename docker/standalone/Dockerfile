# Standalone All-in-One Hindsight Image
# API with embedded pg0 + Control Plane
FROM python:3.11-slim AS api-base

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy dependency files and README (required by pyproject.toml)
COPY hindsight-api/pyproject.toml ./api/
COPY hindsight-api/README.md ./api/

WORKDIR /app/api

# Sync dependencies (will create lock file if needed)
RUN uv sync

# Copy source code
COPY hindsight-api/hindsight_api ./hindsight_api

# Build TypeScript SDK
FROM node:20-alpine AS sdk-builder

WORKDIR /app/sdk

COPY hindsight-clients/typescript/package*.json ./
RUN npm ci

COPY hindsight-clients/typescript/ ./
RUN npm run build

# Build Control Plane
FROM node:20-alpine AS cp-builder

WORKDIR /app

# Copy built SDK
COPY --from=sdk-builder /app/sdk /app/sdk

# Install Control Plane dependencies
COPY hindsight-control-plane/package*.json ./
RUN npm ci

# Copy Control Plane source
COPY hindsight-control-plane/ ./

# Link SDK (temporary for build)
RUN cd /app/sdk && npm link && cd /app && npm link @hindsight/client

# Build Control Plane
RUN npm run build

# Create public directory if it doesn't exist
RUN mkdir -p public

# Final standalone image
FROM python:3.11-slim

WORKDIR /app

# Install Node.js, curl, uv, and pg0 dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libxml2 \
    libssl3 \
    libgssapi-krb5-2 \
    && apt-get install -y libicu72 || apt-get install -y libicu74 || apt-get install -y libicu* \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Create non-root user (PostgreSQL cannot run as root)
RUN useradd -m -s /bin/bash hindsight

# Copy API with virtual environment from builder
COPY --from=api-base /app/api /app/api

# Copy built SDK
COPY --from=sdk-builder /app/sdk /app/sdk

# Copy Control Plane
WORKDIR /app/control-plane
COPY --from=cp-builder /app/package*.json ./
RUN npm ci --omit=dev

# Link SDK for runtime
RUN cd /app/sdk && npm link && cd /app/control-plane && npm link @hindsight/client

COPY --from=cp-builder /app/.next ./.next
COPY --from=cp-builder /app/public ./public
COPY --from=cp-builder /app/next.config.ts ./next.config.ts

WORKDIR /app

# Copy startup script
COPY docker/standalone/start-all.sh /app/start-all.sh
RUN chmod +x /app/start-all.sh

# Create data directory for pg0 and set ownership
RUN mkdir -p /app/data && chown -R hindsight:hindsight /app

# Switch to non-root user
USER hindsight

# Install pg0
RUN curl -fsSL https://raw.githubusercontent.com/vectorize-io/pg0/main/install.sh | bash

# Start pg0 once to verify it works and pre-download PostgreSQL libraries
RUN pg0 --help && \
    pg0 start --wait && \
    pg0 stop

# Expose ports
EXPOSE 8888 3000

# Environment variables
ENV HINDSIGHT_API_HOST=0.0.0.0
ENV HINDSIGHT_API_PORT=8888
ENV HINDSIGHT_API_LOG_LEVEL=info
ENV NODE_ENV=production
ENV HINDSIGHT_CP_DATAPLANE_API_URL=http://localhost:8888
ENV PATH="/home/hindsight/.local/bin:/app/api/.venv/bin:${PATH}"

# Run startup script
CMD ["/app/start-all.sh"]
