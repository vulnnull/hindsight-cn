# Models

Hindsight uses several machine learning models for different tasks. This page explains what models are used, why they're chosen, and how to optimize their performance.

## Model Overview

Hindsight's processing pipeline uses four types of models:

| Model Type | Purpose | Default Model | Configurable |
|------------|---------|---------------|--------------|
| **Embedding** | Vector representations for semantic search | `all-MiniLM-L6-v2` | Yes |
| **Cross-Encoder** | Reranking search results | `ms-marco-MiniLM-L-6-v2` | Yes |
| **Temporal Parser** | Understanding time expressions | `t5-small` | Yes |
| **LLM** | Fact extraction, reasoning, generation | Provider-specific | Yes |

All local models (embedding, cross-encoder, temporal) are automatically downloaded from HuggingFace on first run and cached in `~/.cache/huggingface/`.

## Embedding Model

### Purpose

The embedding model converts text into dense vector representations (embeddings) for semantic similarity search.

**Used for**:
- Encoding memory units during retention
- Encoding search queries during recall
- Vector similarity calculations

### Default: all-MiniLM-L6-v2

```
Model: sentence-transformers/all-MiniLM-L6-v2
Dimensions: 384
Size: ~90MB
Performance: ~2000 texts/second on CPU
```

**Why this model?**
- **Fast**: Optimized for CPU inference
- **Small**: Only 384 dimensions, efficient storage
- **Accurate**: Strong performance on semantic similarity tasks
- **Well-balanced**: Good trade-off between speed and quality

### Performance Optimization

#### 1. Use GPU Acceleration

```bash
# Enable CUDA (NVIDIA GPUs)
export HINDSIGHT_API_EMBEDDING_DEVICE=cuda

# Enable MPS (Apple Silicon)
export HINDSIGHT_API_EMBEDDING_DEVICE=mps

# Verify GPU usage in logs
hindsight-api --log-level debug
# Should see: "Loading embedding model on device: cuda"
```

**Expected speedup**:
- CPU: ~2000 texts/second
- GPU (CUDA): ~10,000-20,000 texts/second
- Apple Silicon (MPS): ~5,000-10,000 texts/second

#### 2. Increase Batch Size

```bash
# Default batch size
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=32

# Larger batch size for better throughput (requires more memory)
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=128

# Smaller batch size for limited memory
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=16
```

**Guidelines**:
- **CPU**: 32-64 (diminishing returns beyond 64)
- **GPU**: 128-256 (can go higher with more VRAM)
- **Memory-constrained**: 8-16

#### 3. Alternative Embedding Models

For different use cases, you can use other embedding models:

**Higher Quality (Slower)**

```bash
# 768 dimensions, better accuracy, slower
export HINDSIGHT_API_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

**Multilingual Support**

```bash
# Supports 50+ languages
export HINDSIGHT_API_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

**Larger Context Window**

```bash
# 512 token context (vs 256 for MiniLM)
export HINDSIGHT_API_EMBEDDING_MODEL=sentence-transformers/all-roberta-large-v1
```

### Memory Requirements

| Model | Dimensions | Model Size | Runtime RAM (CPU) | Runtime RAM (GPU) |
|-------|------------|------------|-------------------|-------------------|
| all-MiniLM-L6-v2 | 384 | 90MB | ~500MB | ~1GB |
| all-mpnet-base-v2 | 768 | 420MB | ~1GB | ~2GB |
| all-roberta-large-v1 | 1024 | 1.3GB | ~2GB | ~4GB |

## Cross-Encoder (Reranker)

### Purpose

The cross-encoder reranks initial search results to improve precision.

**How it works**:
1. Vector search returns top 50-100 candidates (fast but approximate)
2. Cross-encoder scores each candidate with the query (slower but accurate)
3. Results are reranked by cross-encoder score

### Default: ms-marco-MiniLM-L-6-v2

```
Model: cross-encoder/ms-marco-MiniLM-L-6-v2
Size: ~85MB
Performance: ~500 pairs/second on CPU
```

**Why this model?**
- **Accurate**: Trained on Microsoft MARCO dataset for passage ranking
- **Fast enough**: Can rerank 50 results in ~100ms on CPU
- **Small**: Efficient memory footprint

### Performance Optimization

#### 1. Control Reranking Scope

```bash
# Rerank top 50 results (default)
export HINDSIGHT_API_RERANK_TOP_K=50

# More thorough reranking (slower)
export HINDSIGHT_API_RERANK_TOP_K=100

# Faster reranking (less accurate)
export HINDSIGHT_API_RERANK_TOP_K=20

# Disable reranking entirely (fastest, less accurate)
export HINDSIGHT_API_RERANK_ENABLED=false
```

**Trade-offs**:
- More reranking = Better precision, higher latency
- Less reranking = Faster queries, lower precision
- No reranking = Fastest, relies only on vector similarity

#### 2. GPU Acceleration

Cross-encoders also benefit from GPU:

```bash
# Uses same device as embedding model
export HINDSIGHT_API_EMBEDDING_DEVICE=cuda
```

**Speedup**: ~5-10x faster on GPU vs CPU

### Alternative Reranker Models

**Higher Accuracy**

```bash
export HINDSIGHT_API_RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-12-v2
# Larger model, ~200MB, better accuracy
```

**Multilingual**

```bash
export HINDSIGHT_API_RERANK_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
# Supports multiple languages
```

## Temporal Parser

### Purpose

Parses natural language time expressions into structured dates.

**Examples**:
- "last spring" → 2024-03-20 to 2024-06-20
- "in June 2024" → 2024-06-01 to 2024-06-30
- "two weeks ago" → 2024-05-15 to 2024-05-15

### Default: t5-small

```
Model: google/t5-small
Size: ~240MB
Performance: ~100 expressions/second on CPU
```

**Why this model?**
- **Accurate**: Good performance on temporal expression parsing
- **Compact**: Small enough for CPU inference
- **Standard**: Well-established model for sequence-to-sequence tasks

### Performance Optimization

Temporal parsing is typically not a bottleneck, but you can:

1. **Use a larger model for better accuracy**:
   ```bash
   export HINDSIGHT_API_TEMPORAL_MODEL=google/t5-base
   # ~850MB, better at complex temporal expressions
   ```

2. **Use GPU** (shared with other models):
   ```bash
   export HINDSIGHT_API_EMBEDDING_DEVICE=cuda
   ```

## LLM (Large Language Model)

### Purpose

The LLM is used for high-level reasoning tasks that require language understanding and generation.

**Used for**:
- **Fact extraction**: Converting text into structured facts (retention)
- **Entity resolution**: Identifying and linking entities (retention)
- **Opinion generation**: Creating personality-based opinions (reflection)
- **Answer synthesis**: Generating responses from memories (reflect)

### Default: Provider-Specific

Hindsight supports multiple LLM providers. The default depends on your configuration:

| Provider | Default Model | Best For |
|----------|---------------|----------|
| **Groq** | `llama-3.1-70b-versatile` | High throughput, fast inference |
| **OpenAI** | `gpt-4o` | Best quality, general-purpose |
| **Anthropic** | `claude-3-5-sonnet-20241022` | Long context, complex reasoning |
| **Ollama** | User-specified | Local deployment, privacy |

### Performance Optimization

**The LLM is the primary bottleneck for write operations (retention).** See [Performance](./performance.md) for detailed optimization strategies.

#### 1. Choose the Right Provider

For **high-throughput retention** (many memories/second):

```bash
# Groq - fastest inference
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_MODEL=llama-3.1-70b-versatile
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
```

**Groq advantages**:
- 10-30x faster than OpenAI for similar models
- High rate limits (30+ RPM for free tier)
- Low latency (~500ms for retention)

For **best quality** (reasoning, complex fact extraction):

```bash
# OpenAI GPT-4
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_MODEL=gpt-4o
export HINDSIGHT_API_LLM_API_KEY=sk-xxxxxxxxxxxx
```

For **cost optimization**:

```bash
# OpenAI GPT-4 Mini - 60x cheaper than GPT-4
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_MODEL=gpt-4o-mini
export HINDSIGHT_API_LLM_API_KEY=sk-xxxxxxxxxxxx
```

For **local/private deployment**:

```bash
# Ollama with local Llama 3.1
export HINDSIGHT_API_LLM_PROVIDER=ollama
export HINDSIGHT_API_LLM_BASE_URL=http://localhost:11434/v1
export HINDSIGHT_API_LLM_MODEL=llama3.1
```

#### 2. Optimize LLM Configuration

```bash
# Increase timeout for slower providers
export HINDSIGHT_API_LLM_TIMEOUT=60  # seconds

# Increase retries for reliability
export HINDSIGHT_API_LLM_MAX_RETRIES=5

# Enable request caching (if supported by provider)
export HINDSIGHT_API_LLM_CACHE_ENABLED=true
```

#### 3. Rate Limit Management

For providers with strict rate limits:

1. **Use async retention** to queue operations:
   ```python
   client.retain_memories(bank_id="...", items=batch, async_=True)
   ```

2. **Distribute across multiple API keys**:
   ```bash
   # Rotate between keys in application logic
   export HINDSIGHT_API_LLM_API_KEY_1=sk-key1
   export HINDSIGHT_API_LLM_API_KEY_2=sk-key2
   ```

3. **Use multiple providers** for different operations:
   ```bash
   # Groq for retention (fast)
   # OpenAI for reflection (quality)
   ```

### Model Comparison

| Provider | Model | Speed | Quality | Cost/1M tokens | Rate Limit |
|----------|-------|-------|---------|----------------|------------|
| Groq | llama-3.1-70b | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free tier | 30 RPM |
| OpenAI | gpt-4o-mini | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $0.15 / $0.60 | 500 RPM |
| OpenAI | gpt-4o | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $2.50 / $10.00 | 500 RPM |
| Anthropic | claude-3-5-sonnet | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $3.00 / $15.00 | 50 RPM |
| Ollama | llama3.1 (local) | ⭐⭐ | ⭐⭐⭐ | Free | Unlimited |

## Resource Requirements

### Minimal Configuration (Development)

```
CPU: 2 cores
RAM: 4GB
Storage: 5GB (models + data)
```

Models loaded:
- Embedding model (~500MB RAM)
- Cross-encoder (~300MB RAM)
- Temporal parser (~500MB RAM)
- **Total**: ~1.5GB for models + 2GB for application

### Recommended Configuration (Production)

```
CPU: 4-8 cores
RAM: 8-16GB
GPU: Optional (NVIDIA with 4GB+ VRAM for 10x speedup)
Storage: 20GB+ (models + database)
```

Models loaded:
- Same models as minimal
- Additional RAM for connection pooling
- PostgreSQL in separate container/server

### High-Performance Configuration

```
CPU: 8-16 cores
RAM: 16-32GB
GPU: NVIDIA T4, V100, or A100 (8-40GB VRAM)
Storage: 50GB+ SSD
```

Benefits:
- GPU acceleration for embeddings: 10x faster
- More RAM for larger batch sizes
- More CPU cores for parallel processing

## Model Caching and Storage

### Cache Locations

```bash
# HuggingFace models
~/.cache/huggingface/

# Model-specific caches
~/.cache/torch/

# Clear caches
rm -rf ~/.cache/huggingface/
rm -rf ~/.cache/torch/
```

### Preloading Models

To avoid download delays in production:

```bash
# Pre-download all models
python -c "
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Download embedding model
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Download cross-encoder
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Download temporal parser
T5ForConditionalGeneration.from_pretrained('google/t5-small')
T5Tokenizer.from_pretrained('google/t5-small')
"
```

Or build into Docker image:

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install hindsight-all

# Pre-download models
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Rest of Dockerfile...
```

## Monitoring Model Performance

### Check Model Loading

```bash
# Enable debug logging
export HINDSIGHT_API_LOG_LEVEL=debug
hindsight-api

# Look for logs like:
# INFO: Loading embedding model: all-MiniLM-L6-v2 on device: cpu
# INFO: Loading cross-encoder: ms-marco-MiniLM-L-6-v2
# INFO: Loading temporal parser: t5-small
```

### Monitor Resource Usage

```python
# In your application logs
import psutil

# Memory usage
print(f"RAM: {psutil.virtual_memory().percent}%")

# CPU usage
print(f"CPU: {psutil.cpu_percent()}%")

# GPU usage (if available)
import torch
if torch.cuda.is_available():
    print(f"GPU Memory: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
```

## Troubleshooting

### Models Not Downloaded

```bash
# Check cache directory
ls -lh ~/.cache/huggingface/

# Manually download
python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Check network connectivity
curl https://huggingface.co/
```

### Out of Memory

```bash
# Reduce batch size
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=8

# Use smaller models
export HINDSIGHT_API_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # smallest

# Disable reranking
export HINDSIGHT_API_RERANK_ENABLED=false
```

### Slow Inference

```bash
# Enable GPU if available
export HINDSIGHT_API_EMBEDDING_DEVICE=cuda

# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Increase batch size (if you have RAM)
export HINDSIGHT_API_EMBEDDING_BATCH_SIZE=128
```

### LLM Rate Limits

```bash
# Use Groq for higher limits
export HINDSIGHT_API_LLM_PROVIDER=groq

# Use async retention to queue operations
# (in your application code)
client.retain_memories(..., async_=True)
```

---

For model-related questions or issues, please [open an issue](https://github.com/your-repo/hindsight/issues) on GitHub.
