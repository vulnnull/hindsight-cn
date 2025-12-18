# Configuration

Complete reference for configuring Hindsight services through environment variables.

Hindsight has two services, each with its own configuration prefix:

| Service | Prefix | Description |
|---------|--------|-------------|
| **API Service** | `HINDSIGHT_API_*` | Core memory engine |
| **Control Plane** | `HINDSIGHT_CP_*` | Web UI |

---

## API Service

The API service handles all memory operations (retain, recall, reflect).

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_DATABASE_URL` | PostgreSQL connection string | `pg0` (embedded) |

If not provided, the server uses embedded `pg0` — convenient for development but not recommended for production.

### LLM Provider

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_LLM_PROVIDER` | Provider: `groq`, `openai`, `gemini`, `ollama` | `openai` |
| `HINDSIGHT_API_LLM_API_KEY` | API key for LLM provider | - |
| `HINDSIGHT_API_LLM_MODEL` | Model name | `gpt-5-mini` |
| `HINDSIGHT_API_LLM_BASE_URL` | Custom LLM endpoint | Provider default |

**Provider Examples**

```bash
# Groq (recommended for fast inference)
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=openai/gpt-oss-20b

# OpenAI
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_API_KEY=sk-xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=gpt-4o

# Gemini
export HINDSIGHT_API_LLM_PROVIDER=gemini
export HINDSIGHT_API_LLM_API_KEY=xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=gemini-2.0-flash

# Ollama (local, no API key)
export HINDSIGHT_API_LLM_PROVIDER=ollama
export HINDSIGHT_API_LLM_BASE_URL=http://localhost:11434/v1
export HINDSIGHT_API_LLM_MODEL=gpt-oss-20b

# OpenAI-compatible endpoint
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_BASE_URL=https://your-endpoint.com/v1
export HINDSIGHT_API_LLM_API_KEY=your-api-key
export HINDSIGHT_API_LLM_MODEL=your-model-name
```

### Embeddings

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_EMBEDDINGS_PROVIDER` | Provider: `local` or `tei` | `local` |
| `HINDSIGHT_API_EMBEDDINGS_LOCAL_MODEL` | Model for local provider | `BAAI/bge-small-en-v1.5` |
| `HINDSIGHT_API_EMBEDDINGS_TEI_URL` | TEI server URL | - |

```bash
# Local (default) - uses SentenceTransformers
export HINDSIGHT_API_EMBEDDINGS_PROVIDER=local
export HINDSIGHT_API_EMBEDDINGS_LOCAL_MODEL=BAAI/bge-small-en-v1.5

# TEI - HuggingFace Text Embeddings Inference (recommended for production)
export HINDSIGHT_API_EMBEDDINGS_PROVIDER=tei
export HINDSIGHT_API_EMBEDDINGS_TEI_URL=http://localhost:8080
```

:::warning
All embedding models must produce 384-dimensional vectors to match the database schema.
:::

### Reranker

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_RERANKER_PROVIDER` | Provider: `local` or `tei` | `local` |
| `HINDSIGHT_API_RERANKER_LOCAL_MODEL` | Model for local provider | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `HINDSIGHT_API_RERANKER_TEI_URL` | TEI server URL | - |

```bash
# Local (default) - uses SentenceTransformers CrossEncoder
export HINDSIGHT_API_RERANKER_PROVIDER=local
export HINDSIGHT_API_RERANKER_LOCAL_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# TEI - for high-performance inference
export HINDSIGHT_API_RERANKER_PROVIDER=tei
export HINDSIGHT_API_RERANKER_TEI_URL=http://localhost:8081
```

### Server

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_HOST` | Bind address | `0.0.0.0` |
| `HINDSIGHT_API_PORT` | Server port | `8888` |
| `HINDSIGHT_API_LOG_LEVEL` | Log level: `debug`, `info`, `warning`, `error` | `info` |
| `HINDSIGHT_API_MCP_ENABLED` | Enable MCP server | `true` |

### Programmatic Configuration

You can also configure the API programmatically using `MemoryEngine.from_env()`:

```python
from hindsight_api import MemoryEngine

memory = MemoryEngine.from_env()
await memory.initialize()
```

---

## Control Plane

The Control Plane is the web UI for managing memory banks.

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_CP_DATAPLANE_API_URL` | URL of the API service | `http://localhost:8888` |

```bash
# Point Control Plane to a remote API service
export HINDSIGHT_CP_DATAPLANE_API_URL=http://api.example.com:8888
```

---

## Example .env File

```bash
# API Service
HINDSIGHT_API_DATABASE_URL=postgresql://hindsight:hindsight_dev@localhost:5432/hindsight
HINDSIGHT_API_LLM_PROVIDER=groq
HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

# Control Plane
HINDSIGHT_CP_DATAPLANE_API_URL=http://localhost:8888
```

---

For configuration issues not covered here, please [open an issue](https://github.com/vectorize-io/hindsight/issues) on GitHub.
