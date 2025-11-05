# Memora - Entity-Aware Memory System for AI Agents

A temporal-semantic-entity memory system that enables AI agents to store, retrieve, and reason over memories using graph-based spreading activation search.

## Architecture

### Three Memory Networks

The system maintains three separate but interconnected memory networks:

**1. World Network** (`fact_type='world'`)
- General knowledge and facts about the world
- Information not specific to the agent's actions
- Example: "Alice works at Google", "Yosemite is in California"

**2. Agent Network** (`fact_type='agent'`)
- Facts about what the AI agent specifically did
- Agent's own actions and experiences
- Example: "The agent helped debug a Python script", "The agent recommended Yosemite"

**3. Opinion Network** (`fact_type='opinion'`)
- Agent's formed opinions and perspectives
- Automatically extracted during think operations
- Includes reasons and confidence scores (0.0-1.0)
- Immutable once formed (event_date = when opinion was formed)
- Example: "Python is better for data science than JavaScript (Reasons: has better libraries like pandas and numpy) [confidence: 0.85]"

All three networks share the same infrastructure (temporal/semantic/entity links) but can be searched independently or together.

### Core Components

**Memory Units**: Individual sentence-level memories that are:
- Self-contained (pronouns resolved to actual referents by LLM)
- Validated to have subject + verb (complete thoughts)
- Embedded as 384-dim vectors using `BAAI/bge-small-en-v1.5`
- Timestamped for temporal relationships
- Linked to extracted entities via spaCy NER
- Classified as 'world', 'agent', or 'opinion'

**Entity Resolution**: Named entities (PERSON, ORG, PLACE, PRODUCT, CONCEPT, OTHER) are:
- Extracted using spaCy NER
- Disambiguated using scoring algorithm (name similarity 50%, co-occurrence 30%, temporal proximity 20%)
- Tracked with canonical IDs across all memories
- Used to create strong connections between related memories

### Three Types of Memory Links

**1. Temporal Links** (Time-Based)
- Connect memories within time window (default: 24 hours)
- Weight: `max(0.3, 1.0 - (time_diff / window_size))`
- Closer in time = stronger link
- Use case: "What happened recently?" or understanding sequences

**2. Semantic Links** (Meaning-Based)
- Connect memories with similar embeddings
- Uses pgvector with HNSW index for fast nearest neighbor search
- Create links only if cosine similarity > threshold (default: 0.7)
- Weight = cosine similarity score
- Use case: "Tell me about hiking" retrieves all semantically related activities

**3. Entity Links** (Identity-Based)
- Connect ALL memories mentioning the same entity
- No decay over time (weight 1.0)
- Critical advantage: Solves the problem where "Alice loves hiking" wouldn't normally connect to "Alice works at Google" through semantic similarity alone
- Use case: "What does Alice do?" returns ALL memories about Alice

### Spreading Activation Search

The search algorithm explores the memory graph using spreading activation with backpressure limiting (max 32 concurrent searches):

1. **Entry Points**: Find top-3 semantically similar memories (vector search, similarity ≥ 0.5)
2. **Activation Spreading**: Start with activation = actual similarity score at entry points
3. **Graph Traversal**: Follow links to neighbors, spreading activation with decay (0.8 factor)
4. **Thinking Budget**: Limit exploration to N units (controls computational cost)
5. **Dynamic Weighting**: Combine activation, semantic similarity, recency, and frequency:
   ```
   final_weight = w_a × activation + w_s × semantic_similarity + w_r × recency + w_f × frequency

   Default weights (configurable):
   w_a = 0.30  # Activation weight (graph structure)
   w_s = 0.30  # Semantic similarity weight
   w_r = 0.25  # Recency weight (logarithmic decay, 1-year half-life)
   w_f = 0.15  # Frequency weight (normalized access_count)
   ```
6. **MMR Diversification**: Optional Maximal Marginal Relevance to balance relevance with diversity
7. **Return Top-K**: Sort by final weight and return top results

This approach ensures:
- Semantic relevance to query is always considered (30%)
- Graph structure influences results through activation (30%)
- Recently accessed memories get boosted (25%)
- Frequently accessed memories get boosted (15%)

### LLM-Based Fact Extraction

Raw content is processed through an LLM (Groq by default) to extract meaningful facts:

- Filters out noise (greetings, filler words)
- Extracts only substantive facts (biographical, events, opinions, recommendations)
- Creates self-contained statements with subject+action+context
- Resolves pronouns to actual referents
- Automatic chunking for large documents (>120k chars)
- Structured output using Pydantic models
- Retry logic for JSON validation failures

### Technology Stack

**Database**:
- PostgreSQL 15+ with `pgvector` and `uuid-ossp` extensions

**Python Libraries**:
- `asyncpg` - Async PostgreSQL client with connection pooling
- `sentence-transformers` - Local embedding model (BAAI/bge-small-en-v1.5)
- `openai` - LLM API client (supports Groq, OpenAI)
- `fastapi` - Web API framework

**Architecture Patterns**:
- Mixin pattern for code organization
- Connection pooling with backpressure (32 concurrent searches max)
- Background task management for opinion storage
- Cached LLM client for performance

## Quick Start

### Prerequisites

1. Install dependencies:
```bash
uv sync
```

2. Configure environment files:

Create `.env.local` for local development:
```bash
cat > .env.local << 'EOF'
# Database
DATABASE_URL=postgresql://memora:memora_dev@localhost:5432/memora

# LLM Provider: "openai", "groq", or "ollama"
LLM_PROVIDER=groq

# API Key (not needed for ollama)
LLM_API_KEY=your_api_key_here

# Optional: Custom base URL (for ollama or custom endpoints)
# LLM_BASE_URL=http://localhost:11434/v1
EOF
```

Create `.env.dev` for dev/production environment:
```bash
cat > .env.dev << 'EOF'
# Database
DATABASE_URL=postgresql://user:password@host:5432/memora

# LLM Provider: "openai", "groq", or "ollama"
LLM_PROVIDER=groq

# API Key (not needed for ollama)
LLM_API_KEY=your_api_key_here

# Optional: Custom base URL
# LLM_BASE_URL=https://api.custom-provider.com/v1
EOF
```

### LLM Provider Configuration

The system supports multiple LLM providers with separate configuration for main operations and benchmark evaluation:

#### Main LLM (for memory operations)

**Groq** (default, fast inference):
```bash
LLM_PROVIDER=groq
LLM_API_KEY=your_groq_api_key
```

**OpenAI**:
```bash
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
```

**Ollama** (local, no API key needed):
```bash
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1  # Default, can be customized
```

#### Judge LLM (for benchmark evaluation)

Benchmarks can use a separate LLM for evaluation (e.g., using Groq for fast answer generation but OpenAI GPT-4 for accurate judging):

```bash
# If not set, falls back to main LLM configuration
JUDGE_LLM_PROVIDER=openai
JUDGE_LLM_API_KEY=your_openai_api_key
# JUDGE_LLM_BASE_URL=https://api.custom.com/v1  # Optional
```

**Example: Fast generation, accurate judging**:
```bash
# Main LLM - Groq for speed
LLM_PROVIDER=groq
LLM_API_KEY=your_groq_key

# Judge LLM - OpenAI GPT-4 for accuracy
JUDGE_LLM_PROVIDER=openai
JUDGE_LLM_API_KEY=your_openai_key
```

### Local Development

```bash
# Start local PostgreSQL (with initialization)
./scripts/start-local-db.sh

# Start the server with local environment (default)
./scripts/start-server.sh --env local

# Start the server with dev environment
./scripts/start-server.sh --env dev

# Erase local database (stop + cleanup)
./scripts/erase-local-db.sh
```

The server will start at http://localhost:8080

**API Endpoints**:
- `GET  /` - Interactive visualization UI
- `POST /api/memories/batch` - Store memories
- `POST /api/search` - Search all networks
- `POST /api/world_search` - Search world facts only
- `POST /api/agent_search` - Search agent facts only
- `POST /api/opinion_search` - Search opinions only
- `POST /api/think` - Think and generate contextual answers
- `GET  /api/graph` - Get graph data for visualization
- `GET  /api/agents` - List all agents

## API Examples (curl)

### Store Memories (PUT)

```bash
# Store memories for an agent
curl -X POST http://localhost:8080/api/memories/batch \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "alice_agent",
    "items": [
      {
        "content": "Alice works at Google as a software engineer. She joined last year and focuses on machine learning infrastructure.",
        "context": "career discussion",
        "event_date": "2024-01-15T10:00:00Z"
      },
      {
        "content": "Alice loves hiking in Yosemite National Park. She goes every weekend and has climbed Half Dome three times.",
        "context": "hobby conversation"
      }
    ],
    "document_id": "conversation_001"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Successfully stored 2 memory items",
  "agent_id": "alice_agent",
  "document_id": "conversation_001",
  "items_count": 2
}
```

### Search Memories

```bash
# Search across all networks
curl -X POST http://localhost:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "alice_agent",
    "query": "What does Alice do?",
    "thinking_budget": 100,
    "top_k": 10,
    "mmr_lambda": 0.5,
    "trace": false
  }'
```

Response:
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "text": "Alice works at Google as a software engineer",
      "context": "career discussion",
      "event_date": "2024-01-15T10:00:00Z",
      "weight": 0.95,
      "fact_type": "world"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "text": "Alice joined Google last year",
      "weight": 0.87,
      "fact_type": "world"
    }
  ],
  "trace": null
}
```

### Think and Generate Answer

```bash
# Think operation: combines agent identity, world knowledge, and opinions
curl -X POST http://localhost:8080/api/think \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "alice_agent",
    "query": "What do you know about Alice?",
    "thinking_budget": 50,
    "top_k": 10
  }'
```

Response:
```json
{
  "text": "Alice is a software engineer at Google who joined last year. She specializes in machine learning infrastructure. In her free time, she's an avid hiker who frequents Yosemite National Park on weekends and has climbed Half Dome three times.",
  "based_on": {
    "world": [
      {
        "text": "Alice works at Google as a software engineer",
        "weight": 0.95,
        "id": "550e8400-e29b-41d4-a716-446655440000"
      },
      {
        "text": "Alice loves hiking in Yosemite National Park",
        "weight": 0.89,
        "id": "550e8400-e29b-41d4-a716-446655440002"
      }
    ],
    "agent": [],
    "opinion": []
  },
  "new_opinions": []
}
```

## Running Benchmarks

The system includes two benchmarks for evaluating memory retrieval quality:

### LoComo Benchmark

Long-term Conversational Memory benchmark - evaluates multi-turn conversation understanding:

```bash
# Run full benchmark with think API (uses local env by default)
./scripts/benchmarks/run-locomo.sh --use-think

# Run with dev environment
./scripts/benchmarks/run-locomo.sh --use-think --env dev

# Run with limits for quick testing
./scripts/benchmarks/run-locomo.sh --use-think --max-conversations 5 --max-questions 3

# Skip ingestion (use existing data)
./scripts/benchmarks/run-locomo.sh --use-think --skip-ingestion
```

### LongMemEval Benchmark

Long-term Memory Evaluation benchmark - tests memory retention and retrieval:

```bash
# Run full benchmark (uses local env by default)
./scripts/benchmarks/run-longmemeval.sh

# Run with dev environment
./scripts/benchmarks/run-longmemeval.sh --env dev

# Run with arguments (pass any args directly)
./scripts/benchmarks/run-longmemeval.sh --max-instances 10 --max-questions 5

# Skip ingestion
./scripts/benchmarks/run-longmemeval.sh --skip-ingestion
```

### Visualizer

View benchmark results in an interactive web interface:

```bash
# Start the visualizer server
./scripts/benchmarks/start-visualizer.sh
```

The visualizer will be available at http://localhost:8001

**Benchmark Results**: Results are saved to `benchmark_results.json` in each benchmark directory with metrics including accuracy, F1 score, and per-question performance.

## License

MIT
