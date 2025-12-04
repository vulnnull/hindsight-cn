# Models

Hindsight uses several machine learning models for different tasks.

## Overview

| Model Type | Purpose | Default | Configurable |
|------------|---------|---------|--------------|
| **Embedding** | Vector representations for semantic search | `all-MiniLM-L6-v2` | Yes |
| **Cross-Encoder** | Reranking search results | `ms-marco-MiniLM-L-6-v2` | Yes |
| **Temporal Parser** | Understanding time expressions | `t5-small` | Yes |
| **LLM** | Fact extraction, reasoning, generation | Provider-specific | Yes |

All local models (embedding, cross-encoder, temporal) are automatically downloaded from HuggingFace on first run.

---

## Embedding Model

Converts text into dense vector representations for semantic similarity search.

**Default:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, ~90MB)

**Alternatives:**

| Model | Dimensions | Use Case |
|-------|------------|----------|
| `all-MiniLM-L6-v2` | 384 | Default, fast, good quality |
| `all-mpnet-base-v2` | 768 | Higher accuracy, slower |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Multilingual (50+ languages) |

**Configuration:**

```bash
export HINDSIGHT_API_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
export HINDSIGHT_API_EMBEDDING_DEVICE=cuda  # or mps for Apple Silicon
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=64
```

---

## Cross-Encoder (Reranker)

Reranks initial search results to improve precision.

**Default:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (~85MB)

**Alternatives:**

| Model | Use Case |
|-------|----------|
| `ms-marco-MiniLM-L-6-v2` | Default, fast |
| `ms-marco-MiniLM-L-12-v2` | Higher accuracy |
| `mmarco-mMiniLMv2-L12-H384-v1` | Multilingual |

**Configuration:**

```bash
export HINDSIGHT_API_RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-12-v2
export HINDSIGHT_API_RERANK_TOP_K=50      # How many results to rerank
export HINDSIGHT_API_RERANK_ENABLED=true  # Set to false to disable
```

---

## Temporal Parser

Parses natural language time expressions into structured dates.

**Examples:**
- "last spring" → 2024-03-20 to 2024-06-20
- "two weeks ago" → calculated date range

**Default:** `google/t5-small` (~240MB)

**Alternatives:**

| Model | Use Case |
|-------|----------|
| `t5-small` | Default, compact |
| `t5-base` | Better accuracy for complex expressions |

**Configuration:**

```bash
export HINDSIGHT_API_TEMPORAL_MODEL=google/t5-base
```

---

## LLM

Used for fact extraction, entity resolution, opinion generation, and answer synthesis.

**Supported providers:** Groq, OpenAI, Ollama

| Provider | Recommended Model | Best For |
|----------|-------------------|----------|
| **Groq** | `gpt-oss-20b` | Fast inference, high throughput (recommended) |
| **OpenAI** | `gpt-4o-mini` | Good quality, cost-effective |
| **OpenAI** | `gpt-4o` | Best quality |
| **Ollama** | `llama3.1` | Local deployment, privacy |

**Configuration:**

```bash
# Groq (recommended)
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=openai/gpt-oss-20b

# OpenAI
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_API_KEY=sk-xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=gpt-4o-mini

# Ollama (local)
export HINDSIGHT_API_LLM_PROVIDER=ollama
export HINDSIGHT_API_LLM_BASE_URL=http://localhost:11434/v1
export HINDSIGHT_API_LLM_MODEL=llama3.1
```

**Note:** The LLM is the primary bottleneck for write operations. See [Performance](./performance) for optimization strategies.

---

## Model Comparison

| Provider | Model | Speed | Quality | Cost |
|----------|-------|-------|---------|------|
| Groq | gpt-oss-20b | Fast | Good | Free tier |
| OpenAI | gpt-4o-mini | Medium | Good | $0.15 / $0.60 per 1M tokens |
| OpenAI | gpt-4o | Slower | Best | $2.50 / $10.00 per 1M tokens |
| Ollama | llama3.1 | Varies | Good | Free (local) |
