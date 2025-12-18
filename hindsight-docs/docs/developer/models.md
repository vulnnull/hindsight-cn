# Models

Hindsight uses several machine learning models for different tasks.

## Overview

| Model Type | Purpose | Default | Configurable |
|------------|---------|---------|--------------|
| **LLM** | Fact extraction, reasoning, generation | Provider-specific | Yes |
| **Embedding** | Vector representations for semantic search | `BAAI/bge-small-en-v1.5` | Yes |
| **Cross-Encoder** | Reranking search results | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Yes |

All local models (embedding, cross-encoder) are automatically downloaded from HuggingFace on first run.

---

## LLM

Used for fact extraction, entity resolution, opinion generation, and answer synthesis.

**Supported providers:** OpenAI, Gemini, Groq, Ollama, and **any OpenAI-compatible API**

:::tip OpenAI-Compatible Providers
Hindsight works with any provider that exposes an OpenAI-compatible API (e.g., Azure OpenAI). Simply set `HINDSIGHT_API_LLM_PROVIDER=openai` and configure `HINDSIGHT_API_LLM_BASE_URL` to point to your provider's endpoint.

See [Configuration](./configuration#llm-provider) for setup examples.
:::

### Tested Models

The following models have been tested and verified to work correctly with Hindsight:

| Provider | Model |
|----------|-------|
| **OpenAI** | `gpt-5.2` |
| **OpenAI** | `gpt-5` |
| **OpenAI** | `gpt-5-mini` |
| **OpenAI** | `gpt-5-nano` |
| **OpenAI** | `gpt-4.1-mini` |
| **OpenAI** | `gpt-4.1-nano` |
| **OpenAI** | `gpt-4o-mini` |
| **Gemini** | `gemini-3-pro-preview` |
| **Gemini** | `gemini-2.5-flash` |
| **Gemini** | `gemini-2.5-flash-lite` |
| **Groq** | `openai/gpt-oss-120b` |
| **Groq** | `openai/gpt-oss-20b` |

### Using Other Models

Other LLM models not listed above may work with Hindsight, but they must support **at least 65,000 output tokens** to ensure reliable fact extraction. If you need support for a specific model that doesn't meet this requirement, please [open an issue](https://github.com/hindsight-ai/hindsight/issues) to request an exception.

### Configuration

```bash
# Groq (recommended)
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

# Ollama (local)
export HINDSIGHT_API_LLM_PROVIDER=ollama
export HINDSIGHT_API_LLM_BASE_URL=http://localhost:11434/v1
export HINDSIGHT_API_LLM_MODEL=gpt-oss-20b
```

**Note:** The LLM is the primary bottleneck for retain operations. See [Performance](./performance) for optimization strategies.

---

## Embedding Model

Converts text into dense vector representations for semantic similarity search.

**Default:** `BAAI/bge-small-en-v1.5` (384 dimensions, ~130MB)

**Alternatives:**

| Model | Use Case |
|-------|----------|
| `BAAI/bge-small-en-v1.5` | Default, fast, good quality |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Multilingual (50+ languages) |

:::warning
All embedding models must produce **384-dimensional vectors** to match the database schema.
:::

**Configuration:**

```bash
# Local provider (default)
export HINDSIGHT_API_EMBEDDINGS_PROVIDER=local
export HINDSIGHT_API_EMBEDDINGS_LOCAL_MODEL=BAAI/bge-small-en-v1.5

# TEI provider (remote)
export HINDSIGHT_API_EMBEDDINGS_PROVIDER=tei
export HINDSIGHT_API_EMBEDDINGS_TEI_URL=http://localhost:8080
```

---

## Cross-Encoder (Reranker)

Reranks initial search results to improve precision.

**Default:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (~85MB)

**Alternatives:**

| Model | Use Case |
|-------|----------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Default, fast |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | Higher accuracy |
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | Multilingual |

**Configuration:**

```bash
# Local provider (default)
export HINDSIGHT_API_RERANKER_PROVIDER=local
export HINDSIGHT_API_RERANKER_LOCAL_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# TEI provider (remote)
export HINDSIGHT_API_RERANKER_PROVIDER=tei
export HINDSIGHT_API_RERANKER_TEI_URL=http://localhost:8081
```
