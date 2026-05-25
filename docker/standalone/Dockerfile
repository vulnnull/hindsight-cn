# Hindsight-CN Docker 镜像（中文优化版）
# 支持：仅 API、仅控制面板、或两者兼有
#
# 构建参数：
#   INCLUDE_API=true/false         - 包含 API（默认：true）
#   INCLUDE_CP=true/false          - 包含控制面板（默认：true）
#   INCLUDE_LOCAL_MODELS=true/false - 包含本地 ML 模型用于 Embedding/Reranker（默认：true）
#                                     使用外部提供商（TEI、OpenAI、Cohere）时设为 false
#   PRELOAD_ML_MODELS=true/false   - 构建时预下载 ML 模型（默认：true）
#                                     仅在 INCLUDE_LOCAL_MODELS=true 时生效
#                                     注意：tiktoken 编码始终预加载（离线部署必需）
#   EMBEDDING_MODEL=<模型>         - Embedding 模型（默认：BAAI/bge-small-zh-v1.5）
#                                     英文推荐：BAAI/bge-small-en-v1.5
#                                     高质量中文：BAAI/bge-m3（需要更多资源）
#   RERANKER_MODEL=<模型>          - 交叉编码器 Reranker 模型（默认：cross-encoder/mmarco-mMiniLMv2-L12-H384-v1）
#                                     英文推荐：cross-encoder/ms-marco-MiniLM-L-6-v2
#                                     高质量中文：BAAI/bge-reranker-v2-m3（需要更多资源）
#
# 示例：
#   docker build -t hindsight .                                          # 完整版（API + 控制面板）
#   docker build -t hindsight-api --build-arg INCLUDE_CP=false .         # 仅 API
#   docker build -t hindsight-cp --build-arg INCLUDE_API=false .         # 仅控制面板
#   docker build -t hindsight --build-arg PRELOAD_ML_MODELS=false .      # 跳过模型预下载
#   docker build -t hindsight --build-arg INCLUDE_LOCAL_MODELS=false .   # 跳过本地 ML 依赖（使用外部提供商时）
#   docker build --build-arg EMBEDDING_MODEL=BAAI/bge-small-en-v1.5 \
#                --build-arg RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2 .  # 英文版
#   docker build --build-arg EMBEDDING_MODEL=BAAI/bge-m3 \
#                --build-arg RERANKER_MODEL=BAAI/bge-reranker-v2-m3 .              # 高质量中文版（需要更多资源）

ARG INCLUDE_API=true
ARG INCLUDE_CP=true
ARG PRELOAD_ML_MODELS=true
ARG INCLUDE_LOCAL_MODELS=true
ARG EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
ARG RERANKER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1

# =============================================================================
# Stage: API Builder
# =============================================================================
FROM python:3.11-slim AS api-builder

ARG INCLUDE_API
ARG INCLUDE_LOCAL_MODELS
RUN if [ "$INCLUDE_API" != "true" ]; then echo "Skipping API build" && exit 0; fi

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy dependency files and README (required by pyproject.toml)
COPY hindsight-api-slim/pyproject.toml ./api/
COPY hindsight-api-slim/README.md ./api/

WORKDIR /app/api

# Sync dependencies using appropriate extras based on INCLUDE_LOCAL_MODELS
# local-ml: torch, sentence-transformers, transformers, einops, flashrank, mlx (optional)
# embedded-db: pg0-embedded (always included for embedded PostgreSQL support)
RUN if [ "$INCLUDE_LOCAL_MODELS" = "true" ]; then \
        uv sync --extra local-ml --extra embedded-db; \
    else \
        uv sync --extra embedded-db; \
    fi

# Copy source code (alembic migrations are inside hindsight_api/)
COPY hindsight-api-slim/hindsight_api ./hindsight_api

# Install the local package (uv sync only installed dependencies, not the package itself)
RUN uv pip install -e .

# =============================================================================
# Stage: SDK Builder (needed for Control Plane)
# =============================================================================
FROM node:20-slim AS sdk-builder

ARG INCLUDE_CP
RUN if [ "$INCLUDE_CP" != "true" ]; then echo "Skipping SDK build" && exit 0; fi

WORKDIR /app

# Copy root package files for npm workspaces
COPY package.json package-lock.json ./
COPY hindsight-clients/typescript/ ./hindsight-clients/typescript/

# Install and build SDK using workspace (--ignore-scripts skips git hooks setup)
RUN npm ci --ignore-scripts -w @vectorize-io/hindsight-client
RUN npm run build -w @vectorize-io/hindsight-client

# =============================================================================
# Stage: Control Plane Builder
# =============================================================================
FROM node:20-slim AS cp-builder

ARG INCLUDE_CP
RUN if [ "$INCLUDE_CP" != "true" ]; then echo "Skipping CP build" && exit 0; fi

# Create directory structure matching the monorepo layout
# This is required because build:standalone script expects .next/standalone/memory-poc/hindsight-control-plane
WORKDIR /app/memory-poc/hindsight-control-plane

# Install Control Plane dependencies
# Only copy package.json (not package-lock.json) to ensure npm installs
# correct platform-specific native bindings for lightningcss/tailwindcss
COPY hindsight-control-plane/package.json ./
# Remove the file: dependency on SDK (we'll copy it directly later)
RUN sed -i '/"@vectorize-io\/hindsight-client":/d' package.json
RUN npm install

# Copy Control Plane source (excluding node_modules via .dockerignore)
COPY hindsight-control-plane/ ./
# Remove package-lock.json to avoid conflicts with installed native bindings
# Also remove the file: dependency from package.json (restored by COPY above)
RUN rm -f package-lock.json && sed -i '/"@vectorize-io\/hindsight-client":/d' package.json

# Copy built SDK directly into node_modules (more reliable than npm link in Docker)
COPY --from=sdk-builder /app/hindsight-clients/typescript ./node_modules/@vectorize-io/hindsight-client

# Accept base path as build argument for reverse proxy deployments
# Usage: docker build --build-arg NEXT_PUBLIC_BASE_PATH=/hindsight ...
ARG NEXT_PUBLIC_BASE_PATH=""

# Build Control Plane - run next build first, then custom standalone copy
# (The build:standalone script expects a specific path structure that differs in Docker)
RUN npm exec -- next build

# Create standalone directory structure manually
# Note: Must exclude node_modules from find to avoid wrong server.js from next/dist/experimental/testmode/
# Note: Must explicitly copy .next since glob * doesn't match hidden directories
RUN STANDALONE_ROOT=$(find .next/standalone -path '*/node_modules' -prune -o -name 'server.js' -print | head -1 | xargs dirname) && \
    mkdir -p standalone && \
    cp -r "$STANDALONE_ROOT"/* standalone/ && \
    cp -r "$STANDALONE_ROOT"/.next standalone/.next && \
    # Copy node_modules if separate from app dir (monorepo structure)
    if [ -d ".next/standalone/node_modules" ] && [ "$STANDALONE_ROOT" != ".next/standalone" ]; then \
      cp -r .next/standalone/node_modules standalone/node_modules; \
    fi && \
    cp -r .next/static standalone/.next/static && \
    mkdir -p standalone/public && \
    cp -r public/* standalone/public/ 2>/dev/null || true && \
    # Verify required files exist
    test -f standalone/server.js || (echo "ERROR: server.js missing!" && exit 1) && \
    test -f standalone/.next/BUILD_ID || (echo "ERROR: BUILD_ID missing!" && exit 1)

# =============================================================================
# Stage: Final Image - API Only
# =============================================================================
FROM python:3.11-slim AS api-only

WORKDIR /app

# Note: libicu version varies by Debian version - try common versions in order
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    libxml2 \
    libssl3 \
    libgssapi-krb5-2 \
    libossp-uuid16 \
    && (apt-get install -y libicu72 2>/dev/null || apt-get install -y libicu74 2>/dev/null || apt-get install -y libicu76 2>/dev/null || true) \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

RUN useradd -m -s /bin/bash hindsight

# Copy API with virtual environment from builder
COPY --from=api-builder /app/api /app/api

# Copy startup script
COPY docker/standalone/start-all.sh /app/start-all.sh
RUN chmod +x /app/start-all.sh

RUN chown -R hindsight:hindsight /app

USER hindsight

# Create pg0 data directory as hindsight user so that Docker seeds new named
# volumes with correct ownership (UID 1000) on first use, avoiding the
# "Permission denied" error when mounting a fresh root-owned volume.
RUN mkdir -p /home/hindsight/.pg0

# Make /home/hindsight traversable when running with --user UID:GID overrides
# (default 0700 blocks traversal by non-owner UIDs needed for bind-mount ownership matching)
RUN chmod 755 /home/hindsight

ENV PATH="/app/api/.venv/bin:${PATH}"

# Pre-download tiktoken encoding (ALWAYS - required for token counting even in air-gapped envs)
# Tiktoken is a core runtime dependency, not an optional ML model
RUN MAX_RETRIES=3; \
    RETRY_DELAY=5; \
    for i in $(seq 1 $MAX_RETRIES); do \
      echo "Attempt $i/$MAX_RETRIES: Downloading tiktoken encoding..."; \
      /app/api/.venv/bin/python -c "\
import tiktoken; \
print('Downloading cl100k_base encoding...'); \
tiktoken.get_encoding('cl100k_base'); \
print('Tiktoken encoding cached successfully')" && break; \
      if [ $i -lt $MAX_RETRIES ]; then \
        echo "Attempt $i failed, retrying in ${RETRY_DELAY}s..."; \
        sleep $RETRY_DELAY; \
        RETRY_DELAY=$((RETRY_DELAY * 2)); \
      fi; \
    done; \
    if [ $i -eq $MAX_RETRIES ]; then \
      echo "ERROR: Failed to download tiktoken encoding after $MAX_RETRIES attempts"; \
      exit 1; \
    fi

# Pre-download ML models to avoid runtime download (conditional)
# Only runs if both PRELOAD_ML_MODELS=true AND INCLUDE_LOCAL_MODELS=true
# Includes retry logic with exponential backoff for transient network failures
ARG PRELOAD_ML_MODELS
ARG INCLUDE_LOCAL_MODELS
ARG EMBEDDING_MODEL
ARG RERANKER_MODEL
ENV HF_HUB_DOWNLOAD_TIMEOUT=600
RUN if [ "$PRELOAD_ML_MODELS" = "true" ] && [ "$INCLUDE_LOCAL_MODELS" = "true" ]; then \
    MAX_RETRIES=3; \
    RETRY_DELAY=10; \
    for i in $(seq 1 $MAX_RETRIES); do \
      echo "Attempt $i/$MAX_RETRIES: Downloading ML models..."; \
      /app/api/.venv/bin/python -c "\
import os; os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '600'; \
from sentence_transformers import SentenceTransformer, CrossEncoder; \
print('Downloading embedding model...'); \
SentenceTransformer('$EMBEDDING_MODEL', trust_remote_code=True); \
print('Downloading cross-encoder model...'); \
CrossEncoder('$RERANKER_MODEL', trust_remote_code=True); \
print('Models cached successfully')" && break; \
      if [ $i -lt $MAX_RETRIES ]; then \
        echo "Attempt $i failed, retrying in ${RETRY_DELAY}s..."; \
        sleep $RETRY_DELAY; \
        RETRY_DELAY=$((RETRY_DELAY * 2)); \
      fi; \
    done; \
    if [ $i -eq $MAX_RETRIES ] && ! /app/api/.venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('$EMBEDDING_MODEL', trust_remote_code=True)" 2>/dev/null; then \
      echo "ERROR: Failed to download models after $MAX_RETRIES attempts"; \
      exit 1; \
    fi; \
    elif [ "$INCLUDE_LOCAL_MODELS" != "true" ]; then echo "Skipping ML model preload (local-models not included)"; \
    else echo "Skipping ML model preload"; fi

EXPOSE 8888

ENV HINDSIGHT_API_HOST=0.0.0.0
ENV HINDSIGHT_API_PORT=8888
ENV HINDSIGHT_API_LOG_LEVEL=info
ENV HINDSIGHT_ENABLE_API=true
ENV HINDSIGHT_ENABLE_CP=false
ENV PYTHONUNBUFFERED=1
# Suppress verbose transformers/HuggingFace model loading warnings
ENV TRANSFORMERS_VERBOSITY=error
ENV HF_HUB_VERBOSITY=error
ENV TOKENIZERS_PARALLELISM=false

CMD ["/app/start-all.sh"]

# =============================================================================
# Stage: Final Image - Control Plane Only
# =============================================================================
FROM node:20-alpine AS cp-only

WORKDIR /app

# Copy built SDK
COPY --from=sdk-builder /app/hindsight-clients/typescript /app/sdk

# Copy Control Plane standalone build
WORKDIR /app/control-plane
COPY --from=cp-builder /app/memory-poc/hindsight-control-plane/standalone ./
COPY --from=cp-builder /app/memory-poc/hindsight-control-plane/.next/static ./.next/static
COPY --from=cp-builder /app/memory-poc/hindsight-control-plane/public ./public

WORKDIR /app

# Copy startup script
COPY docker/standalone/start-all.sh /app/start-all.sh
RUN chmod +x /app/start-all.sh

# Install curl for health checks
RUN apk add --no-cache curl bash

EXPOSE 9999

ENV NODE_ENV=production
ENV HINDSIGHT_CP_DATAPLANE_API_URL=http://localhost:8888
ENV HINDSIGHT_ENABLE_API=false
ENV HINDSIGHT_ENABLE_CP=true

CMD ["/app/start-all.sh"]

# =============================================================================
# Stage: Final Image - Standalone (both API and Control Plane)
# =============================================================================
FROM python:3.11-slim AS standalone

WORKDIR /app

# Install Node.js, curl, uv, and system dependencies
# Note: libicu version varies by Debian version - try common versions in order
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    libxml2 \
    libssl3 \
    libgssapi-krb5-2 \
    libossp-uuid16 \
    && (apt-get install -y libicu72 2>/dev/null || apt-get install -y libicu74 2>/dev/null || apt-get install -y libicu76 2>/dev/null || true) \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

RUN useradd -m -s /bin/bash hindsight

# Copy API with virtual environment from builder
COPY --from=api-builder /app/api /app/api

# Copy built SDK
COPY --from=sdk-builder /app/hindsight-clients/typescript /app/sdk

# Copy Control Plane standalone build
WORKDIR /app/control-plane
COPY --from=cp-builder /app/memory-poc/hindsight-control-plane/standalone ./
COPY --from=cp-builder /app/memory-poc/hindsight-control-plane/.next/static ./.next/static
COPY --from=cp-builder /app/memory-poc/hindsight-control-plane/public ./public

WORKDIR /app

# Copy startup script
COPY docker/standalone/start-all.sh /app/start-all.sh
RUN chmod +x /app/start-all.sh

RUN chown -R hindsight:hindsight /app

USER hindsight

# Create pg0 data directory as hindsight user so that Docker seeds new named
# volumes with correct ownership (UID 1000) on first use, avoiding the
# "Permission denied" error when mounting a fresh root-owned volume.
RUN mkdir -p /home/hindsight/.pg0

# Make /home/hindsight traversable when running with --user UID:GID overrides
# (default 0700 blocks traversal by non-owner UIDs needed for bind-mount ownership matching)
RUN chmod 755 /home/hindsight

ENV PATH="/app/api/.venv/bin:${PATH}"

# Pre-download tiktoken encoding (ALWAYS - required for token counting even in air-gapped envs)
# Tiktoken is a core runtime dependency, not an optional ML model
RUN MAX_RETRIES=3; \
    RETRY_DELAY=5; \
    for i in $(seq 1 $MAX_RETRIES); do \
      echo "Attempt $i/$MAX_RETRIES: Downloading tiktoken encoding..."; \
      /app/api/.venv/bin/python -c "\
import tiktoken; \
print('Downloading cl100k_base encoding...'); \
tiktoken.get_encoding('cl100k_base'); \
print('Tiktoken encoding cached successfully')" && break; \
      if [ $i -lt $MAX_RETRIES ]; then \
        echo "Attempt $i failed, retrying in ${RETRY_DELAY}s..."; \
        sleep $RETRY_DELAY; \
        RETRY_DELAY=$((RETRY_DELAY * 2)); \
      fi; \
    done; \
    if [ $i -eq $MAX_RETRIES ]; then \
      echo "ERROR: Failed to download tiktoken encoding after $MAX_RETRIES attempts"; \
      exit 1; \
    fi

# Pre-download ML models to avoid runtime download (conditional)
# Only runs if both PRELOAD_ML_MODELS=true AND INCLUDE_LOCAL_MODELS=true
# Includes retry logic with exponential backoff for transient network failures
ARG PRELOAD_ML_MODELS
ARG INCLUDE_LOCAL_MODELS
ARG EMBEDDING_MODEL
ARG RERANKER_MODEL
ENV HF_HUB_DOWNLOAD_TIMEOUT=600
RUN if [ "$PRELOAD_ML_MODELS" = "true" ] && [ "$INCLUDE_LOCAL_MODELS" = "true" ]; then \
    MAX_RETRIES=3; \
    RETRY_DELAY=10; \
    for i in $(seq 1 $MAX_RETRIES); do \
      echo "Attempt $i/$MAX_RETRIES: Downloading ML models..."; \
      /app/api/.venv/bin/python -c "\
import os; os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '600'; \
from sentence_transformers import SentenceTransformer, CrossEncoder; \
print('Downloading embedding model...'); \
SentenceTransformer('$EMBEDDING_MODEL', trust_remote_code=True); \
print('Downloading cross-encoder model...'); \
CrossEncoder('$RERANKER_MODEL', trust_remote_code=True); \
print('Models cached successfully')" && break; \
      if [ $i -lt $MAX_RETRIES ]; then \
        echo "Attempt $i failed, retrying in ${RETRY_DELAY}s..."; \
        sleep $RETRY_DELAY; \
        RETRY_DELAY=$((RETRY_DELAY * 2)); \
      fi; \
    done; \
    if [ $i -eq $MAX_RETRIES ] && ! /app/api/.venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('$EMBEDDING_MODEL', trust_remote_code=True)" 2>/dev/null; then \
      echo "ERROR: Failed to download models after $MAX_RETRIES attempts"; \
      exit 1; \
    fi; \
    elif [ "$INCLUDE_LOCAL_MODELS" != "true" ]; then echo "Skipping ML model preload (local-models not included)"; \
    else echo "Skipping ML model preload"; fi

EXPOSE 8888 9999

ENV HINDSIGHT_API_HOST=0.0.0.0
ENV HINDSIGHT_API_PORT=8888
ENV HINDSIGHT_API_LOG_LEVEL=info
ENV NODE_ENV=production
ENV HINDSIGHT_CP_DATAPLANE_API_URL=http://localhost:8888
ENV HINDSIGHT_ENABLE_API=true
ENV HINDSIGHT_ENABLE_CP=true
ENV PYTHONUNBUFFERED=1
# Suppress verbose transformers/HuggingFace model loading warnings
ENV TRANSFORMERS_VERBOSITY=error
ENV HF_HUB_VERBOSITY=error
ENV TOKENIZERS_PARALLELISM=false

CMD ["/app/start-all.sh"]

# =============================================================================
# Default target selection based on build args
# =============================================================================
FROM standalone AS default-both
FROM api-only AS default-api
FROM cp-only AS default-cp

# This selects the final stage based on INCLUDE_API and INCLUDE_CP
# Use --target to override: docker build --target api-only .
FROM standalone
