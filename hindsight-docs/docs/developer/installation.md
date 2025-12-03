# Installation

Hindsight can be deployed in three ways depending on your infrastructure and requirements.

## Prerequisites

### PostgreSQL with pgvector

Hindsight requires PostgreSQL with the **pgvector** extension for vector similarity search:

- PostgreSQL 14+ (recommended: 16+)
- pgvector extension installed
- ~2GB+ RAM for small deployments

### LLM Provider

You need an LLM API key for fact extraction, entity resolution, and answer generation:

- **Groq** (recommended): Fast inference, high throughput
- **OpenAI**: GPT-4, GPT-4o, GPT-4 Mini
- **Anthropic**: Claude 3.5 Sonnet, Haiku
- **Ollama**: Run models locally

---

## Docker

**Best for**: Quick start, development, small deployments

Docker Compose bundles all dependencies (PostgreSQL with pgvector, API server, Control Plane) in a single command.

```bash
# Clone the repository
git clone https://github.com/vectorize-io/hindsight.git
cd hindsight

# Create environment file
cp .env.example .env
# Edit .env with your LLM API key:
# HINDSIGHT_API_LLM_PROVIDER=groq
# HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

# Start all services
cd docker
./start.sh
```

**Services started**:
- **API Server**: http://localhost:8888
- **Control Plane** (Web UI): http://localhost:3000
- **Swagger UI**: http://localhost:8888/docs

**Management**:
```bash
./stop.sh   # Stop services
./clean.sh  # Delete all data
```

---

## Helm / Kubernetes

**Best for**: Production deployments, auto-scaling, cloud environments

```bash
# Add Hindsight Helm repository
helm repo add hindsight https://vectorize-io.github.io/hindsight
helm repo update

# Install with built-in PostgreSQL
helm install hindsight hindsight/hindsight \
  --set api.llm.provider=groq \
  --set api.llm.apiKey=gsk_xxxxxxxxxxxx \
  --set postgresql.enabled=true

# Or use external PostgreSQL
helm install hindsight hindsight/hindsight \
  --set api.llm.provider=groq \
  --set api.llm.apiKey=gsk_xxxxxxxxxxxx \
  --set postgresql.enabled=false \
  --set api.database.url=postgresql://user:pass@postgres.example.com:5432/hindsight
```

**Requirements**:
- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- Helm 3+

See the [Helm chart documentation](https://github.com/vectorize-io/hindsight/tree/main/helm) for advanced configuration.

---

## Bare Metal (pip)

**Best for**: Custom deployments, integration into existing Python applications

### Install

```bash
pip install hindsight-all
```

### Run with Embedded Database

For development and testing, Hindsight can run with an embedded PostgreSQL (pg0):

```bash
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

hindsight-api
```

This creates a database in `~/.hindsight/data/` and starts the API on http://localhost:8888.

### Run with External PostgreSQL

For production, connect to your own PostgreSQL instance:

```bash
export HINDSIGHT_API_DATABASE_URL=postgresql://user:pass@localhost:5432/hindsight
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

hindsight-api
```

**Note**: The database must exist and have pgvector enabled (`CREATE EXTENSION vector;`).

### CLI Options

```bash
hindsight-api --port 9000          # Custom port (default: 8888)
hindsight-api --host 127.0.0.1     # Bind to localhost only
hindsight-api --workers 4          # Multiple worker processes
hindsight-api --mcp                # Enable MCP server
hindsight-api --log-level debug    # Verbose logging
```

---

## Next Steps

- [Configuration](./configuration.md) — Environment variables and settings
- [Models](./models.md) — ML models and providers
- [Metrics](./metrics.md) — Monitoring and observability
