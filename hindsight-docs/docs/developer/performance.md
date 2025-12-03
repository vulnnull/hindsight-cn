# Performance

Hindsight is designed for high-performance semantic memory operations at scale. This page covers performance characteristics, optimization strategies, and best practices.

## Overview

Hindsight's performance is optimized across three key operations:

- **Retain (Ingestion)**: Batch processing with async operations for large-scale memory storage
- **Recall (Search)**: Sub-second semantic search with configurable thinking budgets
- **Reflect (Reasoning)**: Personality-aware answer generation with controllable compute

## Design Philosophy: Optimized for Fast Reads

Hindsight is **architected from the ground up to prioritize read performance over write performance**. This design decision reflects the typical usage pattern of memory systems: memories are written once but read many times.

### Read-Optimized Architecture

The system makes deliberate trade-offs to ensure **sub-second recall operations**:

- **Pre-computed embeddings**: All memory embeddings are generated and indexed during retention
- **Optimized vector search**: HNSW indexes enable fast approximate nearest neighbor search
- **Fact extraction at write time**: Complex LLM-based fact extraction happens during retention, not retrieval
- **Structured memory graphs**: Relationships and temporal information are resolved upfront

This means **Recall (search) operations are blazingly fast** because all the heavy lifting has already been done.

### Write Performance: LLM-Bound Operations

The trade-off is that **Retain (write) operations are inherently slower** because they involve:

1. **LLM-based fact extraction**: Converting raw text into structured semantic facts
2. **Entity recognition and resolution**: Identifying and linking entities across memories
3. **Temporal reasoning**: Extracting and normalizing time references
4. **Relationship mapping**: Building the semantic graph structure
5. **Embedding generation**: Creating vector representations for search

**The LLM is the primary bottleneck for write latency.** Each piece of content requires one or more LLM calls for fact extraction, which typically takes 500ms-2000ms per batch depending on content complexity.

### Achieving Fast Writes

To maximize retention throughput, we recommend:

1. **Use high-throughput LLM providers**: Choose providers with high requests-per-minute (RPM) limits
   - ✅ **Recommended**: Groq (up to 30 RPM for Llama models), OpenAI GPT-4 Turbo/Mini
   - ⚠️ **Slower**: Claude with lower rate limits, local models

2. **Batch your operations**: Group related content into batch requests to amortize overhead
   ```python
   # Good: Batch retention
   client.retain_memories(bank_id="...", items=batch_of_100_items)

   # Less efficient: Individual retention
   for item in items:
       client.retain_memories(bank_id="...", items=[item])
   ```

3. **Use async mode for large datasets**: Queue operations in the background
   ```python
   client.retain_memories(bank_id="...", items=large_batch, async_=True)
   ```

4. **Parallel processing**: For very large datasets, use multiple concurrent retention requests with different `document_id` values

### Performance Comparison

| Operation | Typical Latency | Primary Bottleneck | Optimization Strategy |
|-----------|----------------|-------------------|----------------------|
| **Recall** | 100-600ms | Vector search, graph traversal | ✅ Already optimized |
| **Reflect** | 800-3000ms | LLM generation + search | Reduce search budget, use faster LLM |
| **Retain** | 500ms-2000ms per batch | **LLM fact extraction** | Use high-throughput LLM provider |

### The Bottom Line

Hindsight is designed to ensure your **application's read path (recall/reflect) is always fast**, even if it means spending more time upfront during writes. This is the right trade-off for memory systems where:

- Memories are retained in background processes or during low-traffic periods
- Memories are queried frequently in user-facing, latency-sensitive contexts
- The ratio of reads to writes is high (typically 10:1 or higher)

If your use case requires extremely fast writes, focus on **LLM provider selection** and **batching strategies** rather than database or infrastructure optimization.

## Retain Performance

### Batch Ingestion

Hindsight supports high-throughput batch ingestion for efficient memory storage:

```python
from hindsight_client import HindsightClient

client = HindsightClient(base_url="http://localhost:8888")

# Batch retain for better performance
items = [
    {"content": "Memory 1", "context": "Context 1"},
    {"content": "Memory 2", "context": "Context 2"},
    # ... up to thousands of items
]

result = client.retain_memories(
    bank_id="my-bank",
    items=items,
    document_id="batch-doc-001"
)
```

### Async Operations

For very large datasets, use async operations to avoid blocking:

```python
# Queue for background processing
result = client.retain_memories(
    bank_id="my-bank",
    items=large_dataset,
    async_=True  # Process in background
)

print(f"Queued {result.items_count} items for processing")

# Check operation status
operations = client.list_operations(bank_id="my-bank")
for op in operations:
    print(f"Operation {op.id}: {op.status}")
```

### Ingestion Throughput

Typical ingestion performance on standard hardware:

| Mode | Items/second | Use Case |
|------|--------------|----------|
| Synchronous | ~50-100 | Real-time updates, small batches |
| Async (batched) | ~500-1000 | Bulk imports, background processing |
| Parallel async | ~2000-5000 | Large-scale data migration |

**Factors affecting throughput:**
- Document size and complexity
- LLM provider rate limits (for fact extraction)
- Database write performance
- Available CPU/memory resources

### Optimization Tips

1. **Batch related memories**: Group related content into the same document for better context
2. **Use async for large batches**: Set `async_=True` for batches > 100 items
3. **Optimize chunk sizes**: Larger chunks (1000-2000 tokens) are more efficient than many small chunks
4. **Parallel processing**: Use multiple concurrent requests with different `document_id` values

## Recall Performance

### Search Latency

Hindsight provides sub-second semantic search with configurable performance/quality tradeoffs:

```python
# Fast search (low budget)
result = client.recall_memories(
    bank_id="my-bank",
    query="What did we discuss about the project?",
    budget="low"  # ~100-200ms
)

# Balanced search (mid budget)
result = client.recall_memories(
    bank_id="my-bank",
    query="What did we discuss about the project?",
    budget="mid"  # ~300-500ms
)

# Thorough search (high budget)
result = client.recall_memories(
    bank_id="my-bank",
    query="What did we discuss about the project?",
    budget="high"  # ~500-1000ms
)
```

### Thinking Budget

The `budget` parameter controls the search depth and quality:

| Budget | Latency | Memory Activation | Use Case |
|--------|---------|-------------------|----------|
| `low` | 100-300ms | ~10-50 facts | Quick lookups, real-time chat |
| `mid` | 300-600ms | ~50-200 facts | Standard queries, balanced performance |
| `high` | 500-1500ms | ~200-500 facts | Complex questions, thorough analysis |

### Search Optimization

1. **Appropriate budgets**: Use lower budgets for simple queries, higher for complex reasoning
2. **Limit result tokens**: Set `max_tokens` to control response size (default: 4096)
3. **Filter by fact type**: Specify `types` to search only relevant fact categories
4. **Temporal filtering**: Use `query_timestamp` for time-aware search

### Database Performance

Hindsight uses PostgreSQL with pgvector for efficient vector search:

- **Index type**: HNSW for approximate nearest neighbor search
- **Typical query time**: 10-50ms for vector search on 100K+ facts
- **Scalability**: Tested with millions of facts per bank

## Reflect Performance

### Answer Generation

Reflect combines semantic search with personality-aware reasoning:

```python
result = client.reflect(
    bank_id="my-bank",
    query="What should we prioritize next quarter?",
    budget="mid",  # Controls memory search depth
    context="We have limited resources"
)

print(result.text)  # Personality-aware answer
```

### Performance Characteristics

| Component | Latency | Description |
|-----------|---------|-------------|
| Memory search | 300-1000ms | Based on budget (low/mid/high) |
| LLM generation | 500-2000ms | Depends on provider and response length |
| **Total** | **800-3000ms** | Typical end-to-end latency |

### Optimization Strategies

1. **Budget selection**: Use lower budgets when context is sufficient
2. **Context provision**: Provide relevant `context` to reduce search requirements
3. **Streaming responses**: Use streaming APIs (when available) for faster time-to-first-token
4. **Caching**: Cache frequent queries at the application level

## Concurrent Operations

### Parallelism

Hindsight supports high levels of concurrent operations:

```python
import asyncio
from hindsight_client import AsyncHindsightClient

async def parallel_recall():
    client = AsyncHindsightClient(base_url="http://localhost:8888")

    # Execute multiple recalls in parallel
    tasks = [
        client.recall_memories("bank-1", query="query 1"),
        client.recall_memories("bank-2", query="query 2"),
        client.recall_memories("bank-3", query="query 3"),
    ]

    results = await asyncio.gather(*tasks)
    return results
```

### Concurrency Limits

Default limits (configurable in server settings):

- **Database connections**: Pool of 20 connections
- **LLM rate limits**: Depends on provider (typically 60-500 RPM)
- **Memory search**: No hard limit, scales with CPU cores
- **Concurrent requests**: 100+ simultaneous requests supported

## Scaling Strategies

### Horizontal Scaling

Hindsight can be scaled horizontally for high-throughput scenarios:

1. **Multiple API instances**: Deploy multiple Hindsight servers behind a load balancer
2. **Shared database**: All instances connect to the same PostgreSQL database
3. **LLM provider limits**: Distribute load across multiple API keys/providers
4. **Bank isolation**: Distribute banks across different instances for better isolation

### Database Scaling

For very large deployments:

1. **Connection pooling**: Use pgBouncer for connection management
2. **Read replicas**: Use PostgreSQL read replicas for read-heavy workloads
3. **Partitioning**: Partition large banks by time or topic
4. **Vacuum and analyze**: Regular maintenance for optimal query performance

### Resource Requirements

Recommended specifications per 1M facts:

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4-8 cores |
| RAM | 4GB | 8-16GB |
| Database storage | 10GB | 20GB+ (with indexes) |
| Vector index RAM | 2GB | 4GB+ |

## Benchmarks

### LoComo Benchmark Results

Hindsight has been evaluated on the LoComo (Long Context Memory) benchmark:

- **Dataset**: 10 conversations with multi-hop, temporal, and reasoning questions
- **Overall accuracy**: ~65-75% (varies by category)
- **Average recall latency**: 400-600ms (mid budget)
- **Average reflect latency**: 1500-2500ms (end-to-end)

See the [GitHub repository](https://github.com/vectorize-io/hindsight/tree/main/hindsight-dev/benchmarks) for detailed benchmark results.

### Performance Metrics

Key performance indicators to monitor:

1. **Latency percentiles**: Track p50, p95, p99 for recall/reflect operations
2. **Throughput**: Requests per second for each operation type
3. **Error rates**: Failed requests, timeouts, LLM errors
4. **Resource utilization**: CPU, memory, database connection pool usage
5. **LLM costs**: Token usage and API costs per operation

## Monitoring and Optimization

### Enable Trace Information

Use the `trace` parameter to analyze performance:

```python
result = client.recall_memories(
    bank_id="my-bank",
    query="test query",
    trace=True
)

if result.trace:
    print(f"Total time: {result.trace.get('total_time')}ms")
    print(f"Activations: {result.trace.get('activation_count')}")
```

### Metrics Collection

Hindsight exposes Prometheus metrics for monitoring:

```bash
curl http://localhost:8888/metrics
```

Key metrics:
- `hindsight_recall_duration_seconds`: Recall operation latency
- `hindsight_reflect_duration_seconds`: Reflect operation latency
- `hindsight_retain_items_total`: Number of items retained
- `hindsight_database_connections`: Active database connections

### Performance Tuning

Server configuration options (environment variables):

```bash
# Database connection pool
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=10

# LLM configuration
export LLM_PROVIDER=openai
export LLM_MAX_RETRIES=3
export LLM_TIMEOUT=30

# Search configuration
export DEFAULT_THINKING_BUDGET=500
export MAX_SEARCH_RESULTS=100
```

## Best Practices

1. **Use appropriate budgets**: Don't over-provision thinking budget for simple queries
2. **Batch operations**: Group related retains together for better efficiency
3. **Monitor costs**: Track LLM token usage and optimize prompts
4. **Cache when possible**: Cache frequently accessed queries at the application level
5. **Clean old data**: Regularly archive or delete unused memory banks
6. **Profile queries**: Use trace information to identify slow operations
7. **Load test**: Test your specific workload before production deployment

## Cost Optimization

### LLM Token Usage

Optimize costs by controlling token usage:

1. **Chunk size**: Larger chunks reduce overhead but increase individual LLM calls
2. **Max tokens**: Limit `max_tokens` to reduce response size
3. **Fact extraction**: Use efficient models (e.g., GPT-4 Mini) for retain operations
4. **Budget management**: Lower budgets reduce the number of facts processed

### Typical Costs

Example costs using OpenAI GPT-4:

| Operation | Tokens | Cost per request | Notes |
|-----------|--------|------------------|-------|
| Retain (1 item) | ~1000-2000 | $0.01-0.02 | Fact extraction |
| Recall | ~2000-8000 | $0.02-0.08 | Depends on budget |
| Reflect | ~4000-12000 | $0.04-0.12 | Search + generation |

**Note**: Costs vary significantly by model provider and configuration. Use cheaper models (GPT-4 Mini, Claude Haiku) for non-critical operations.

## Future Improvements

Planned optimizations:

- **Adaptive budgeting**: Automatically adjust thinking budget based on query complexity
- **Incremental updates**: Update facts without full re-extraction
- **Query caching**: Built-in cache for frequently accessed memories
- **Multi-modal support**: Efficient processing of images and documents
- **Distributed search**: Shard large banks across multiple databases

---

For specific performance issues or questions, please [open an issue](https://github.com/your-repo/hindsight/issues) on GitHub.
