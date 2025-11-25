---
sidebar_position: 3
---

# Retrieval

Hindsight's retrieval architecture (TEMPR) runs four search strategies in parallel and fuses results for optimal recall and precision.

:::tip Deep Dive on Temporal Reasoning
For a comprehensive guide on how Hindsight handles temporal facts and time-aware retrieval, see [Temporal Reasoning](./temporal-reasoning.md).
:::

## Pipeline Overview

```
Query → Embedding + Temporal Parse
         │
         ├─→ Semantic Search (pgvector)
         ├─→ Keyword Search (BM25)
         ├─→ Graph Traversal (spreading activation)
         └─→ Temporal-Graph (time-filtered)
         │
         ↓
    RRF Fusion
         │
         ↓
    Cross-Encoder Rerank
         │
         ↓
    Token Budget Filter → Results
```

## Four Strategies

### 1. Semantic Search

Vector similarity using pgvector HNSW index.

```sql
SELECT * FROM memories
WHERE (1 - (embedding <=> query_embedding)) >= 0.3
ORDER BY embedding <=> query_embedding
LIMIT 100
```

**Strengths**: Conceptual matches, paraphrasing, synonyms

**Example**: "Alice's job" → "Alice works as a software engineer"

### 2. Keyword Search (BM25)

PostgreSQL full-text search with BM25 ranking.

```sql
SELECT *, ts_rank_cd(search_vector, to_tsquery('english', query)) AS score
FROM memories
WHERE search_vector @@ to_tsquery('english', query)
ORDER BY score DESC
```

**Strengths**: Exact names, technical terms, proper nouns

**Example**: "Google" → all mentions of "Google"

### 3. Graph Traversal

Spreading activation from semantic entry points through the entity graph.

```python
1. Find top-5 semantic matches (similarity ≥ 0.5)
2. Initialize activation = similarity_score
3. For each node (up to thinking_budget):
   - Propagate: neighbor.activation = current × edge.weight × 0.8
   - Causal links get 2x boost
4. Return nodes with activation scores
```

**Strengths**: Indirect relationships, entity connections, causal reasoning

**Example**: "What does Alice do?" → Alice → Google → Google's products

### 4. Temporal-Graph Search

Activated when temporal expressions are detected. Uses T5-small for parsing.

| Expression | Parsed Range |
|------------|--------------|
| "last spring" | March 1 - May 31 (prev year) |
| "in June" | June 1-30 |
| "last year" | Jan 1 - Dec 31 (prev year) |
| "between March and May" | March 1 - May 31 |

**Strengths**: Historical queries, time-bounded search

**Example**: "What did Alice do last spring?" → Events in March-May range

**How it works**: Combines semantic entry points with time filtering, then traverses the entity graph while only following links to facts within the temporal range. See [Temporal Reasoning](./temporal-reasoning.md) for detailed explanation.

## Result Fusion (RRF)

Reciprocal Rank Fusion combines ranked lists without score normalization:

```
RRF_score(d) = Σ 1/(60 + rank_i(d))
```

Items appearing in multiple lists rank higher than single-list items.

## Cross-Encoder Reranking

Neural reranking with temporal awareness:

```python
input = f"[Date: {date_readable}] {memory_text}"
score = cross_encoder.predict([(query, input)])
```

Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`

## Token Budget Filtering

Final stage ensures results fit LLM context windows:

```python
for result in reranked_results:
    tokens = len(tokenizer.encode(result.text))
    if total_tokens + tokens <= max_tokens:
        filtered.append(result)
        total_tokens += tokens
```

## Search Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `thinking_budget` | 100 | Max nodes to explore in graph |
| `max_tokens` | 4096 | Token limit for results |
| `fact_type` | all | Filter: world, agent, opinion |

## Performance

Typical latency breakdown (p50):

| Stage | Time |
|-------|------|
| Query embedding | ~12ms |
| Semantic search | ~35ms |
| BM25 search | ~8ms |
| Graph traversal | ~42ms |
| RRF fusion | ~2ms |
| Cross-encoder | ~35ms |
| **Total** | **~135ms** |
