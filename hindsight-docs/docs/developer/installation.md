# Installation

Hindsight can be deployed in multiple ways depending on your infrastructure and requirements. This guide covers all installation methods and explains the core dependencies.

## Dependencies

Hindsight has two core dependencies that you need to provide:

### 1. PostgreSQL Database

**Why PostgreSQL?**

Hindsight uses PostgreSQL with the **pgvector** extension to store and query semantic memories efficiently:

- **Vector search**: pgvector enables fast approximate nearest neighbor (ANN) search using HNSW indexes
- **Full-text search**: PostgreSQL's GIN indexes provide BM25-ranked text search
- **Graph storage**: Entity relationships are stored using relational tables
- **ACID compliance**: Ensures data consistency for memory operations
- **Temporal queries**: Native date/time support for temporal reasoning

**Requirements**:
- PostgreSQL 14+ (recommended: 16+)
- pgvector extension installed
- ~2GB+ RAM for small deployments, 4GB+ for production

### 2. LLM Provider

**Why an LLM?**

Hindsight uses Large Language Models for several critical operations:

- **Fact extraction**: Converting raw text into structured semantic facts during retention
- **Entity resolution**: Identifying and linking entities across memories
- **Temporal parsing**: Understanding time references in natural language
- **Opinion generation**: Creating personality-based opinions during reflection
- **Answer generation**: Synthesizing responses from retrieved memories

**Performance Impact**: The LLM is the primary bottleneck for **write operations (retention)**. See [Performance](./performance.md) for details on optimizing throughput.

**Supported Providers**:
- **Groq**: Fast inference, high throughput (recommended for production)
- **OpenAI**: GPT-4, GPT-4o, GPT-4 Mini
- **Anthropic**: Claude 3.5 Sonnet, Haiku
- **Ollama**: Run models locally (llama3.1, mixtral, etc.)
- **Any OpenAI-compatible API**: Custom endpoints

## Installation Methods

### Docker Compose (Recommended)

**Best for**: Quick start, development, small deployments

**Why use this?**: Bundles all dependencies (PostgreSQL with pgvector, API server, optional Control Plane) in a single command.

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

**What you get**:
- **API Server**: http://localhost:8888
- **Control Plane** (Web UI): http://localhost:3000
- **Swagger UI**: http://localhost:8888/docs
- **PostgreSQL**: Runs in container with pgvector extension

**Management**:
```bash
# Stop services
cd docker && ./stop.sh

# Clean all data (WARNING: deletes all memories)
cd docker && ./clean.sh

# View logs
docker-compose logs -f api
docker-compose logs -f postgres
```

### Helm Chart (Kubernetes)

**Best for**: Production deployments, auto-scaling, cloud environments

**Why use this?**: Kubernetes-native deployment with proper resource management, health checks, and auto-scaling capabilities.

```bash
# Add Hindsight Helm repository
helm repo add hindsight https://vectorize-io.github.io/hindsight
helm repo update

# Install with basic configuration
helm install hindsight hindsight/hindsight \
  --set api.llm.provider=groq \
  --set api.llm.apiKey=gsk_xxxxxxxxxxxx \
  --set postgresql.enabled=true

# Or use your own PostgreSQL
helm install hindsight hindsight/hindsight \
  --set api.llm.provider=groq \
  --set api.llm.apiKey=gsk_xxxxxxxxxxxx \
  --set postgresql.enabled=false \
  --set api.database.url=postgresql://user:pass@postgres.example.com:5432/hindsight
```

**What you need**:
- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- kubectl configured
- Helm 3+
- External PostgreSQL with pgvector (recommended) or use built-in PostgreSQL

See the [Helm chart documentation](https://github.com/vectorize-io/hindsight/tree/main/deploy/helm) for advanced configuration.

### pip install (Python Package)

**Best for**: Custom deployments, development, integration into existing Python applications

**Why use this?**: Maximum flexibility. Runs as a Python application with embedded PostgreSQL (pg0) by default, or connects to your own database.

#### Install

```bash
# Install the all-in-one package
pip install hindsight-all

# Verify installation
hindsight-api --version
```

#### Run with Embedded Database (pg0)

**Best for**: Development, testing, single-machine deployments

```bash
# Configure LLM provider
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

# Start the server - uses embedded pg0
hindsight-api
```

**What happens**:
- Creates `~/.hindsight/data/` directory for database storage
- Downloads ML models on first run (~500MB)
- Starts API server on http://localhost:8888
- Ready to use - no external dependencies needed!

**Limitations**:
- Single process only (no horizontal scaling)
- Lower performance than dedicated PostgreSQL
- Not recommended for production

#### Run with External PostgreSQL

**Best for**: Production, high-performance deployments

```bash
# Configure database
export HINDSIGHT_API_DATABASE_URL=postgresql://user:pass@localhost:5432/hindsight

# Configure LLM
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

# Start the server
hindsight-api
```

**Requirements**:
- PostgreSQL 14+ with pgvector extension
- Database must already exist
- pgvector extension must be enabled: `CREATE EXTENSION vector;`

#### CLI Options

```bash
hindsight-api --help

# Common options
hindsight-api --port 9000              # Custom port (default: 8888)
hindsight-api --host 127.0.0.1         # Bind to localhost only
hindsight-api --workers 4              # Multiple worker processes
hindsight-api --mcp                    # Enable MCP server
hindsight-api --log-level debug        # Verbose logging
hindsight-api --reload                 # Auto-reload on code changes (dev)
```

### Cloud Managed Services

**Best for**: Production with minimal ops overhead

You can deploy Hindsight to cloud platforms using their managed services:

#### AWS

```bash
# Use RDS PostgreSQL with pgvector
# Deploy via ECS, EKS, or EC2
# Example: ECS with Fargate
docker build -t hindsight-api .
aws ecr get-login-password | docker login --username AWS
docker push your-ecr-repo/hindsight-api
# Deploy via ECS task definition
```

**Required AWS Services**:
- **RDS PostgreSQL** with pgvector extension
- **ECS/EKS** for container orchestration
- **Secrets Manager** for API keys
- **ALB** for load balancing (optional)

#### Google Cloud

```bash
# Use Cloud SQL PostgreSQL with pgvector
# Deploy via Cloud Run or GKE
gcloud run deploy hindsight \
  --image gcr.io/your-project/hindsight-api \
  --set-env-vars HINDSIGHT_API_DATABASE_URL=... \
  --set-secrets HINDSIGHT_API_LLM_API_KEY=...
```

**Required GCP Services**:
- **Cloud SQL PostgreSQL** with pgvector
- **Cloud Run** or **GKE** for deployment
- **Secret Manager** for API keys

#### Supabase

**Simplest cloud deployment** - Supabase provides PostgreSQL with pgvector built-in:

```bash
# 1. Create a Supabase project at supabase.com
# 2. Get your database URL from Settings > Database
# 3. Deploy API server with DATABASE_URL

export HINDSIGHT_API_DATABASE_URL=postgresql://postgres:password@db.xxxxxxxxxxxx.supabase.co:5432/postgres
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

hindsight-api
```

## Choosing an Installation Method

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Docker Compose** | Development, small deployments | Easy setup, all dependencies included | Not scalable, single host |
| **Helm/Kubernetes** | Production, auto-scaling | Scalable, cloud-native, resilient | Complex setup, K8s knowledge required |
| **pip install** | Development, custom integration | Flexible, Python-native, embedded DB option | Manual dependency management |
| **Cloud Services** | Production with managed infrastructure | Minimal ops, auto-scaling, managed DB | Higher cost, cloud lock-in |

## Post-Installation

### Verify Installation

```bash
# Check API server health
curl http://localhost:8888/health

# List banks (should return empty array initially)
curl http://localhost:8888/api/v1/banks

# View API documentation
open http://localhost:8888/docs
```

### First Steps

1. **Create your first bank**:
   ```bash
   curl -X POST http://localhost:8888/api/v1/banks/my-first-bank \
     -H "Content-Type: application/json" \
     -d '{"name": "My First Bank"}'
   ```

2. **Retain your first memory**:
   ```bash
   curl -X POST http://localhost:8888/api/v1/banks/my-first-bank/retain \
     -H "Content-Type: application/json" \
     -d '{"items": [{"content": "The Eiffel Tower is in Paris."}]}'
   ```

3. **Recall the memory**:
   ```bash
   curl -X POST http://localhost:8888/api/v1/banks/my-first-bank/recall \
     -H "Content-Type: application/json" \
     -d '{"query": "Where is the Eiffel Tower?"}'
   ```

### Next Steps

- **Configure** your deployment: [Configuration](./configuration.md)
- **Understand ML models**: [Models](./models.md)
- **Monitor performance**: [Metrics](./metrics.md)
- **Optimize for production**: [Performance](./performance.md)

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Test database connection
psql "$HINDSIGHT_API_DATABASE_URL"

# Verify pgvector extension
psql -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Enable pgvector if missing
psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### LLM Provider Issues

```bash
# Test Groq API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $HINDSIGHT_API_LLM_API_KEY"

# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $HINDSIGHT_API_LLM_API_KEY"
```

### Port Already in Use

```bash
# Find process using port 8888
lsof -i :8888

# Kill the process
kill -9 <PID>

# Or use a different port
hindsight-api --port 9000
```

### Model Download Issues

```bash
# Models are downloaded to ~/.cache/huggingface/
# Clear cache and retry
rm -rf ~/.cache/huggingface/
hindsight-api  # Will re-download models
```

---

For installation issues not covered here, please [open an issue](https://github.com/your-repo/hindsight/issues) on GitHub.
