# Configuration

Complete reference for configuring Hindsight server through environment variables and configuration files.

## Environment Variables

Hindsight is configured entirely through environment variables, making it easy to deploy across different environments and container orchestration platforms.

### LLM Provider Configuration

Configure the LLM provider used for fact extraction, entity resolution, and reasoning operations.

#### Common LLM Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_LLM_PROVIDER` | LLM provider: `openai`, `groq`, `ollama`, `anthropic` | `groq` | Yes |
| `HINDSIGHT_API_LLM_API_KEY` | API key for LLM provider | - | Yes (except ollama) |
| `HINDSIGHT_API_LLM_MODEL` | Model name | Provider-specific | No |
| `HINDSIGHT_API_LLM_BASE_URL` | Custom LLM endpoint | Provider default | No |
| `HINDSIGHT_API_LLM_MAX_RETRIES` | Maximum retry attempts for LLM calls | `3` | No |
| `HINDSIGHT_API_LLM_TIMEOUT` | Request timeout in seconds | `30` | No |

#### Provider-Specific Examples

**Groq (Recommended for Fast Inference)**

```bash
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=llama-3.1-70b-versatile
```

**OpenAI**

```bash
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_API_KEY=sk-xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=gpt-4o
```

**Anthropic Claude**

```bash
export HINDSIGHT_API_LLM_PROVIDER=anthropic
export HINDSIGHT_API_LLM_API_KEY=sk-ant-xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=claude-3-5-sonnet-20241022
```

**Ollama (Local, No API Key)**

```bash
export HINDSIGHT_API_LLM_PROVIDER=ollama
export HINDSIGHT_API_LLM_BASE_URL=http://localhost:11434/v1
export HINDSIGHT_API_LLM_MODEL=llama3.1
```

**OpenAI-Compatible Endpoints**

```bash
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_BASE_URL=https://your-endpoint.com/v1
export HINDSIGHT_API_LLM_API_KEY=your-api-key
export HINDSIGHT_API_LLM_MODEL=your-model-name
```

### Database Configuration

Configure the PostgreSQL database connection and behavior.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_DATABASE_URL` | PostgreSQL connection string | - | Yes* |
| `HINDSIGHT_API_DB_POOL_SIZE` | Connection pool size | `20` | No |
| `HINDSIGHT_API_DB_MAX_OVERFLOW` | Max overflow connections | `10` | No |
| `HINDSIGHT_API_DB_POOL_TIMEOUT` | Pool checkout timeout (seconds) | `30` | No |
| `HINDSIGHT_API_DB_POOL_RECYCLE` | Connection recycle time (seconds) | `3600` | No |

**\*Note**: If `DATABASE_URL` is not provided and running via `pip install hindsight-all`, the server will use embedded `pg0` (PostgreSQL in a single file).

#### Connection String Format

```bash
# Standard PostgreSQL URL format
postgresql://username:password@hostname:port/database

# With SSL
postgresql://user:pass@host:5432/db?sslmode=require

# With connection pool settings
postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=10
```

#### Examples

**Docker Compose Default**

```bash
export HINDSIGHT_API_DATABASE_URL=postgresql://hindsight:hindsight_dev@postgres:5432/hindsight
```

**AWS RDS**

```bash
export HINDSIGHT_API_DATABASE_URL=postgresql://admin:password@hindsight.xxxx.us-east-1.rds.amazonaws.com:5432/hindsight?sslmode=require
```

**Supabase**

```bash
export HINDSIGHT_API_DATABASE_URL=postgresql://postgres:password@db.xxxxxxxxxxxx.supabase.co:5432/postgres
```

**Embedded pg0 (Default for pip install)**

```bash
# No DATABASE_URL needed - automatically uses pg0
# Data stored in: ~/.hindsight/data/
```

### Server Configuration

Configure the HTTP server behavior.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_HOST` | Server bind address | `0.0.0.0` | No |
| `HINDSIGHT_API_PORT` | Server port | `8888` | No |
| `HINDSIGHT_API_WORKERS` | Number of worker processes | `1` | No |
| `HINDSIGHT_API_RELOAD` | Enable auto-reload (dev mode) | `false` | No |
| `HINDSIGHT_API_LOG_LEVEL` | Logging level: `debug`, `info`, `warning`, `error` | `info` | No |
| `HINDSIGHT_API_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` | No |

#### Examples

**Production Server**

```bash
export HINDSIGHT_API_HOST=0.0.0.0
export HINDSIGHT_API_PORT=8888
export HINDSIGHT_API_WORKERS=4
export HINDSIGHT_API_LOG_LEVEL=warning
export HINDSIGHT_API_CORS_ORIGINS="https://app.example.com,https://admin.example.com"
```

**Development Server**

```bash
export HINDSIGHT_API_HOST=127.0.0.1
export HINDSIGHT_API_PORT=8888
export HINDSIGHT_API_RELOAD=true
export HINDSIGHT_API_LOG_LEVEL=debug
```

### MCP Server Configuration

Configure the Model Context Protocol (MCP) server for AI assistant integrations.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_MCP_ENABLED` | Enable MCP server | `true` | No |
| `HINDSIGHT_API_MCP_TRANSPORT` | Transport: `stdio`, `sse` | `stdio` | No |

```bash
# Enable MCP server (default)
export HINDSIGHT_API_MCP_ENABLED=true

# Disable MCP server
export HINDSIGHT_API_MCP_ENABLED=false
```

### Search and Retrieval Configuration

Configure search behavior and performance.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_DEFAULT_THINKING_BUDGET` | Default thinking budget (tokens) | `500` | No |
| `HINDSIGHT_API_MAX_SEARCH_RESULTS` | Maximum search results to return | `100` | No |
| `HINDSIGHT_API_RERANK_ENABLED` | Enable cross-encoder reranking | `true` | No |
| `HINDSIGHT_API_RERANK_TOP_K` | Number of results to rerank | `50` | No |

```bash
# High-performance search
export HINDSIGHT_API_DEFAULT_THINKING_BUDGET=1000
export HINDSIGHT_API_MAX_SEARCH_RESULTS=200
export HINDSIGHT_API_RERANK_ENABLED=true
export HINDSIGHT_API_RERANK_TOP_K=100

# Fast, resource-efficient search
export HINDSIGHT_API_DEFAULT_THINKING_BUDGET=200
export HINDSIGHT_API_MAX_SEARCH_RESULTS=50
export HINDSIGHT_API_RERANK_ENABLED=false
```

### Embedding Model Configuration

Configure the embedding model for vector search.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_EMBEDDING_MODEL` | HuggingFace model name | `all-MiniLM-L6-v2` | No |
| `HINDSIGHT_API_EMBEDDING_DEVICE` | Device: `cpu`, `cuda`, `mps` | `cpu` | No |
| `HINDSIGHT_API_EMBEDDING_BATCH_SIZE` | Batch size for embedding generation | `32` | No |

```bash
# Use GPU for embeddings (if available)
export HINDSIGHT_API_EMBEDDING_DEVICE=cuda

# Use Apple Silicon GPU
export HINDSIGHT_API_EMBEDDING_DEVICE=mps

# Larger batch size for better throughput
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=64
```

### Control Plane Configuration

Configure the optional web UI control plane.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_CP_API_URL` | API server URL | `http://localhost:8888` | No |
| `HINDSIGHT_CP_HOSTNAME` | Server bind address | `0.0.0.0` | No |
| `HINDSIGHT_CP_PORT` | Server port | `3000` | No |

```bash
export HINDSIGHT_CP_API_URL=http://api.example.com:8888
export HINDSIGHT_CP_HOSTNAME=0.0.0.0
export HINDSIGHT_CP_PORT=3000
```

## Configuration Files

### .env File

For local development and Docker Compose deployments, use a `.env` file:

```bash
# .env

# Database
HINDSIGHT_API_DATABASE_URL=postgresql://hindsight:hindsight_dev@localhost:5432/hindsight

# LLM Provider
HINDSIGHT_API_LLM_PROVIDER=groq
HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
HINDSIGHT_API_LLM_MODEL=llama-3.1-70b-versatile

# Server
HINDSIGHT_API_HOST=0.0.0.0
HINDSIGHT_API_PORT=8888
HINDSIGHT_API_LOG_LEVEL=info

# Search
HINDSIGHT_API_DEFAULT_THINKING_BUDGET=500
HINDSIGHT_API_MAX_SEARCH_RESULTS=100

# Control Plane
HINDSIGHT_CP_API_URL=http://localhost:8888
HINDSIGHT_CP_PORT=3000
```

### Docker Compose

Example `docker-compose.yml` configuration:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: hindsight
      POSTGRES_PASSWORD: hindsight_dev
      POSTGRES_DB: hindsight
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    image: hindsight/api:latest
    environment:
      HINDSIGHT_API_DATABASE_URL: postgresql://hindsight:hindsight_dev@postgres:5432/hindsight
      HINDSIGHT_API_LLM_PROVIDER: groq
      HINDSIGHT_API_LLM_API_KEY: ${GROQ_API_KEY}
      HINDSIGHT_API_LLM_MODEL: llama-3.1-70b-versatile
      HINDSIGHT_API_PORT: 8888
      HINDSIGHT_API_LOG_LEVEL: info
    ports:
      - "8888:8888"
    depends_on:
      - postgres

  control-plane:
    image: hindsight/control-plane:latest
    environment:
      HINDSIGHT_CP_API_URL: http://api:8888
      HINDSIGHT_CP_PORT: 3000
    ports:
      - "3000:3000"
    depends_on:
      - api

volumes:
  postgres_data:
```

### Kubernetes ConfigMap

Example Kubernetes configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hindsight-config
data:
  HINDSIGHT_API_LLM_PROVIDER: "groq"
  HINDSIGHT_API_LLM_MODEL: "llama-3.1-70b-versatile"
  HINDSIGHT_API_PORT: "8888"
  HINDSIGHT_API_LOG_LEVEL: "info"
  HINDSIGHT_API_DEFAULT_THINKING_BUDGET: "500"
  HINDSIGHT_API_MAX_SEARCH_RESULTS: "100"

---
apiVersion: v1
kind: Secret
metadata:
  name: hindsight-secrets
type: Opaque
stringData:
  HINDSIGHT_API_DATABASE_URL: "postgresql://user:pass@postgres:5432/hindsight"
  HINDSIGHT_API_LLM_API_KEY: "gsk_xxxxxxxxxxxx"
```

## Configuration Precedence

Configuration values are resolved in this order (highest to lowest priority):

1. **Environment variables** - Direct environment variables
2. **`.env` file** - Local `.env` file in current directory
3. **Default values** - Built-in defaults

## Configuration Validation

Hindsight validates configuration on startup and will fail fast with clear error messages:

```bash
# Missing required configuration
ERROR: HINDSIGHT_API_LLM_API_KEY is required when using provider 'openai'

# Invalid value
ERROR: HINDSIGHT_API_LOG_LEVEL must be one of: debug, info, warning, error

# Invalid connection
ERROR: Failed to connect to database at postgresql://localhost:5432/hindsight
```

## Best Practices

1. **Use secrets management** for production deployments (AWS Secrets Manager, Vault, etc.)
2. **Never commit** `.env` files with real credentials to version control
3. **Use different configs** for dev, staging, and production environments
4. **Set appropriate log levels**: `debug` for dev, `info` for staging, `warning` for production
5. **Configure connection pooling** based on expected load
6. **Use managed databases** in production with proper backups
7. **Enable SSL/TLS** for database connections in production
8. **Set CORS origins** explicitly in production (don't use `*`)

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
psql "$HINDSIGHT_API_DATABASE_URL"

# Check PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres
```

### LLM Provider Issues

```bash
# Test API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $HINDSIGHT_API_LLM_API_KEY"

# Enable debug logging
export HINDSIGHT_API_LOG_LEVEL=debug
hindsight-api
```

### Port Already in Use

```bash
# Find process using port 8888
lsof -i :8888

# Kill process
kill -9 <PID>

# Or use a different port
export HINDSIGHT_API_PORT=9000
```

## Advanced Configuration

### Custom Embedding Models

Use custom embedding models from HuggingFace:

```bash
export HINDSIGHT_API_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
export HINDSIGHT_API_EMBEDDING_DEVICE=cuda
```

### Custom Temporal Parser

Use custom T5 model for temporal parsing:

```bash
export HINDSIGHT_API_TEMPORAL_MODEL=google/t5-v1_1-base
```

### Multi-GPU Configuration

For distributed embedding generation:

```bash
export HINDSIGHT_API_EMBEDDING_DEVICE=cuda:0,cuda:1
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=128
```

---

For configuration issues not covered here, please [open an issue](https://github.com/your-repo/hindsight/issues) on GitHub.
