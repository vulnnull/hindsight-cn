FROM node:20-alpine AS control-plane-builder

# Build control plane
WORKDIR /app/memora-control-plane
COPY memora-control-plane/package*.json ./
RUN npm ci

COPY memora-control-plane/ ./
# Set env to skip font optimization during build
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build || (echo "Build failed, retrying..." && npm run build)

# Python source stage - just copy files, don't build venv yet
FROM python:3.12-slim AS dataplane-source

WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY memora/ ./memora/
COPY memora-dev/ ./memora-dev/

# Final runtime image
FROM python:3.12-slim

# Install system dependencies and PostgreSQL
RUN apt-get update && apt-get install -y \
    gnupg \
    lsb-release \
    wget \
    curl \
    ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/keyrings/pgdg.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/pgdg.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y \
    postgresql-15 \
    postgresql-15-pgvector \
    postgresql-contrib-15 \
    nodejs \
    npm \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy dataplane source from builder
COPY --from=dataplane-source /build /app

# Build venv in the final stage to ensure compatibility
RUN cd /app && uv sync --frozen

# Copy control plane from builder
COPY --from=control-plane-builder /app/memora-control-plane/.next/standalone /app/memora-control-plane
COPY --from=control-plane-builder /app/memora-control-plane/.next/static /app/memora-control-plane/.next/static
COPY memora-control-plane/start-server.sh /app/memora-control-plane/start-server.sh
RUN chmod +x /app/memora-control-plane/start-server.sh

# Copy standalone configuration
COPY standalone/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY standalone/init.sh /app/init.sh
COPY standalone/.env.standalone /app/.env

RUN chmod +x /app/init.sh

# PostgreSQL setup
RUN mkdir -p /var/lib/postgresql/data && \
    chown -R postgres:postgres /var/lib/postgresql && \
    mkdir -p /var/run/postgresql && \
    chown -R postgres:postgres /var/run/postgresql

# Initialize PostgreSQL as postgres user
USER postgres
RUN /usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/data

USER root

# Expose ports
# 5432: PostgreSQL
# 8080: Dataplane API
# 3000: Control Plane
EXPOSE 5432 8080 3000

# Start supervisor
CMD ["/app/init.sh"]
