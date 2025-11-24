---
sidebar_position: 6
---

# Server Administration

Guide to deploying and configuring the Memora server.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  Python Client  │  Node.js Client │      CLI        │   AI Assistants       │
│  memora-client  │  @memora/client │   memora-cli    │  (Claude, etc.)       │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────┬───────────┘
         │                 │                 │                     │
         │                 │                 │                     │
         ▼                 ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEMORA API SERVER                                  │
│                          (localhost:8080)                                    │
├─────────────────────────────────┬───────────────────────────────────────────┤
│          HTTP API               │              MCP API                       │
│    /api/memories/*              │         MCP Server (stdio)                 │
│    /api/agents/*                │      memora_search, memora_think,          │
│    /api/search, /api/think      │      memora_store, memora_agents           │
└─────────────────────────────────┴───────────────────────────────────────────┘
         │                                           │
         │                                           │
         ▼                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PROCESSING PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   INGESTION  │    │  RETRIEVAL   │    │  REASONING   │                   │
│  │              │    │   (TEMPR)    │    │   (CARA)     │                   │
│  │  LLM Extract │    │              │    │              │                   │
│  │  Entity Res. │    │  4-way Search│    │  Personality │                   │
│  │  Graph Build │    │  RRF Fusion  │    │  Opinion Gen │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ML MODELS                                       │
├───────────────────┬───────────────────┬─────────────────────────────────────┤
│    Embeddings     │   Cross-Encoder   │         LLM Provider                 │
│  all-MiniLM-L6-v2 │ ms-marco-MiniLM   │   OpenAI / Groq / Ollama            │
│    (384-dim)      │   (reranking)     │   (extraction, reasoning)           │
└───────────────────┴───────────────────┴─────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL + PGVECTOR                                │
│                          (localhost:5432)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Memory Units (facts, opinions)    • HNSW Vector Index                    │
│  • Entity Graph (nodes, edges)       • GIN Full-Text Index                  │
│  • Agent Profiles                    • Temporal Indexes                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONTROL PLANE (Optional)                                │
│                         (localhost:3000)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Web UI for administration         • Agent management                     │
│  • Memory visualization              • Graph explorer                       │
│  • Connects to API Server            • Monitoring dashboard                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/memora/memora.git
cd memora

# Create environment file
cp .env.example .env
# Edit .env with your LLM API key

# Start all services
cd docker
./start.sh
```

Services will be available at:
- **API Server**: http://localhost:8080
- **Control Plane**: http://localhost:3000
- **Swagger UI**: http://localhost:8080/docs

### Local Development

```bash
# Install dependencies
uv sync

# Start PostgreSQL only (via Docker)
cd docker && docker-compose up -d postgres

# Start the API server
./scripts/start-server.sh --env local
```

## Environment Variables

### API Server (`MEMORA_API_*`)

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMORA_API_DATABASE_URL` | PostgreSQL connection string | Required |
| `MEMORA_API_LLM_PROVIDER` | LLM provider: `openai`, `groq`, `ollama` | `groq` |
| `MEMORA_API_LLM_API_KEY` | API key for LLM provider | Required (except ollama) |
| `MEMORA_API_LLM_MODEL` | Model name | `openai/gpt-oss-20b` |
| `MEMORA_API_LLM_BASE_URL` | Custom LLM endpoint | Provider default |
| `MEMORA_API_HOST` | Server bind address | `0.0.0.0` |
| `MEMORA_API_PORT` | Server port | `8080` |
| `MEMORA_API_MCP_ENABLED` | Enable MCP server | `true` |

### Control Plane (`MEMORA_CP_*`)

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMORA_CP_DATAPLANE_API_URL` | API server URL | `http://localhost:8080` |
| `MEMORA_CP_HOSTNAME` | Server bind address | `0.0.0.0` |
| `MEMORA_CP_PORT` | Server port | `3000` |

### Example Configuration

```bash
# .env file

# Database
MEMORA_API_DATABASE_URL=postgresql://memora:memora_dev@localhost:5432/memora

# LLM - Using Groq (fast inference)
MEMORA_API_LLM_PROVIDER=groq
MEMORA_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
MEMORA_API_LLM_MODEL=llama-3.1-70b-versatile

# LLM - Using OpenAI
# MEMORA_API_LLM_PROVIDER=openai
# MEMORA_API_LLM_API_KEY=sk-xxxxxxxxxxxx
# MEMORA_API_LLM_MODEL=gpt-4o

# LLM - Using Ollama (local, no API key)
# MEMORA_API_LLM_PROVIDER=ollama
# MEMORA_API_LLM_BASE_URL=http://localhost:11434/v1
# MEMORA_API_LLM_MODEL=llama3.1

# Control Plane
MEMORA_CP_DATAPLANE_API_URL=http://localhost:8080
```

## ML Models

Memora uses several ML models for different stages of the pipeline:

### Embedding Model

| Model | Dimensions | Purpose |
|-------|------------|---------|
| `all-MiniLM-L6-v2` | 384 | Semantic vector embeddings |

Downloaded automatically on first run. Used for:
- Memory vectorization
- Query embedding
- Semantic similarity search

### Cross-Encoder (Reranking)

| Model | Purpose |
|-------|---------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Neural reranking |

Reranks search results for precision after initial retrieval. Includes temporal context in input.

### Temporal Parser

| Model | Purpose |
|-------|---------|
| `t5-small` | Temporal expression parsing |

Parses natural language time expressions like "last spring" or "in June 2024".

### LLM (Configurable)

Used for:
- Fact extraction from raw content
- Entity extraction and resolution
- Opinion generation with personality
- Think/reasoning responses

Supported providers:
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5-turbo
- **Groq**: Llama 3.1, Mixtral (fast inference)
- **Ollama**: Any local model

## Database Schema

PostgreSQL with pgvector extension:

```sql
-- Memory units (facts and opinions)
CREATE TABLE memory_units (
    id UUID PRIMARY KEY,
    agent_id VARCHAR NOT NULL,
    text TEXT NOT NULL,
    fact_type VARCHAR NOT NULL,  -- 'world', 'agent', 'opinion'
    confidence_score FLOAT,
    embedding VECTOR(384),
    occurred_start DATE,
    occurred_end DATE,
    mentioned_at TIMESTAMP,
    context VARCHAR,
    document_id VARCHAR
);

-- Entity graph
CREATE TABLE entities (
    id UUID PRIMARY KEY,
    agent_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    entity_type VARCHAR NOT NULL,
    canonical_name VARCHAR
);

CREATE TABLE entity_links (
    memory_id UUID REFERENCES memory_units(id),
    entity_id UUID REFERENCES entities(id),
    PRIMARY KEY (memory_id, entity_id)
);

-- Agent profiles
CREATE TABLE agent_profiles (
    agent_id VARCHAR PRIMARY KEY,
    background TEXT,
    openness FLOAT DEFAULT 0.5,
    conscientiousness FLOAT DEFAULT 0.5,
    extraversion FLOAT DEFAULT 0.5,
    agreeableness FLOAT DEFAULT 0.5,
    neuroticism FLOAT DEFAULT 0.5,
    bias_strength FLOAT DEFAULT 0.5
);
```

### Indexes

- **HNSW Index**: Fast approximate nearest neighbor for vector search
- **GIN Index**: Full-text search with BM25 ranking
- **B-tree Indexes**: Agent ID, timestamps, entity lookups

## Docker Services

```yaml
services:
  postgres:     # pgvector/pgvector:pg16
  api:          # Memora API server
  control-plane: # Admin UI (optional)
```

### Commands

```bash
# Start all services
cd docker && ./start.sh

# Stop services
cd docker && ./stop.sh

# Clean all data
cd docker && ./clean.sh

# View logs
docker-compose logs -f api
docker-compose logs -f control-plane
```

## Health Checks

### API Server

```bash
curl http://localhost:8080/api/v1/agents
```

### Control Plane

```bash
curl http://localhost:3000/
```

## Production Deployment

For production deployments:

1. **Use managed PostgreSQL** with pgvector extension
2. **Set proper secrets** via environment variables or secrets manager
3. **Configure resource limits** for ML model inference
4. **Set up monitoring** for API latency and error rates
5. **Use HTTPS** with proper TLS certificates
6. **Configure rate limiting** at load balancer level

### Resource Requirements

| Component | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| API Server | 2+ cores | 4GB+ | ML models loaded in memory |
| PostgreSQL | 2+ cores | 4GB+ | Depends on data size |
| Control Plane | 1 core | 512MB | Lightweight Next.js app |
