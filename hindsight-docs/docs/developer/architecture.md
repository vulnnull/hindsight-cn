---
sidebar_position: 2
---

# Architecture

Hindsight's architecture consists of three main pipelines: ingestion, retrieval, and reasoning.

## Memory Ingestion

When content is stored, Hindsight processes it through an LLM-powered extraction pipeline.

### Narrative Fact Extraction

Unlike traditional systems that create atomic fragments, Hindsight extracts **comprehensive narrative facts** that preserve context:

**Fragmented (traditional)**:
- "Bob suggested Summer Vibes"
- "Alice wanted something unique"
- "They chose Beach Beats"

**Narrative (Hindsight)**:
- "Alice and Bob discussed naming their summer party playlist. Bob suggested 'Summer Vibes' because it's catchy, but Alice wanted something unique. They ultimately decided on 'Beach Beats' for its playful tone."

This approach:
- Preserves conversational flow and reasoning
- Resolves pronouns ("she" → "Alice")
- Normalizes temporal expressions ("last year" → "2024")
- Reduces fact count while maintaining context

### Entity Extraction

The LLM identifies entities in each fact:

| Type | Examples |
|------|----------|
| PERSON | "Alice", "Bob Chen" |
| ORGANIZATION | "Google", "Stanford" |
| LOCATION | "Yosemite", "California" |
| PRODUCT | "Python", "TensorFlow" |
| CONCEPT | "machine learning", "remote work" |

### Entity Resolution

Multiple mentions are resolved to canonical entities:

- "Alice" + "Alice Chen" + "Alice C." → single entity
- "Bob" + "Robert Chen" → single entity (nicknames)
- Context-aware: "Apple (company)" vs "apple (fruit)"

### Graph Construction

Three types of links connect memories:

**Entity Links** (`weight=1.0`)
- Connect all memories mentioning the same entity
- Enable "tell me everything about X" queries

**Temporal Links** (`weight=0.3-1.0`)
- Connect memories close in time
- Weight decays with time distance
- Enable "what happened around then?" queries

**Semantic Links** (`weight=0.7-1.0`)
- Connect semantically similar memories
- Based on embedding cosine similarity
- Enable "tell me about similar topics" queries

**Causal Links** (`weight=1.0`, boosted 2x in retrieval)
- Connect cause-effect relationships
- Types: `causes`, `caused_by`, `enables`, `prevents`
- Enable "why did this happen?" queries

## Memory Unit Structure

Each stored memory contains:

```python
{
    "id": "uuid",
    "agent_id": "my-agent",
    "text": "Alice works at Google as a software engineer...",
    "fact_type": "world",  # world, agent, or opinion
    "confidence_score": 0.85,  # only for opinions
    "embedding": [0.12, -0.34, ...],  # 384-dim vector
    "occurred_start": "2023-11-01",  # when fact started
    "occurred_end": "2023-11-01",    # when fact ended
    "mentioned_at": "2024-01-15",    # when we learned it
    "entities": ["Alice", "Google"]
}
```

## Temporal Model

Hindsight distinguishes **when facts occurred** from **when they were mentioned**:

- `occurred_start/end`: When the fact/event actually happened
- `mentioned_at`: When the agent learned about it

This enables:
- Accurate temporal queries: "What did Alice do in 2020?"
- Recency-aware ranking: Recent mentions get priority
- Historical queries without losing old information

## Storage

PostgreSQL with pgvector provides:

- **HNSW Index**: Fast approximate nearest neighbor search
- **GIN Index**: Full-text search with BM25 ranking
- **Entity Graph**: Adjacency list for graph traversal
- **ACID Transactions**: Consistent memory updates
