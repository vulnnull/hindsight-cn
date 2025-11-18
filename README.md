# Memora - Entity-Aware Memory System for AI Agents

A temporal-semantic-entity memory system that enables AI agents to store, retrieve, and reason over memories using graph-based spreading activation search.

## Architecture

**See [architecture.md](architecture.md) for comprehensive technical documentation.**

The system provides:
- **Three Memory Networks**: Separate world knowledge, agent experiences, and formed opinions
- **Multi-Strategy Retrieval**: 4-way parallel search (semantic, keyword, graph, temporal-graph)
- **Entity Resolution**: Automatic entity disambiguation and linking
- **Personality Framework**: Big Five traits influencing opinion formation
- **Neural Reranking**: Optional cross-encoder for precision refinement

### Quick Architecture Overview

**Three Memory Networks**:
1. **World Network**: General knowledge ("Alice works at Google")
2. **Agent Network**: Agent's own actions ("I recommended Yosemite to Alice")
3. **Opinion Network**: Formed opinions with confidence scores ("Python is better for data science [0.85]")

**Retrieval Pipeline**:
```
Query → [Semantic + Keyword + Graph + Temporal] → RRF Merge → Cross-Encoder Reranking → MMR → Results
```
- 4-way parallel retrieval for high recall
- Neural cross-encoder reranking for precision
- MMR diversification to avoid redundancy

**Key Features**:
- Entity resolution links memories through shared people/places/things
- Graph spreading activation discovers indirect connections
- Temporal queries: "What did Alice do last spring?"
- Personality traits (Big Five model) influence opinion formation

## Quick Start

### Prerequisites

1. Install dependencies:
```bash
uv sync
```

2. Configure environment file:

Create `.env` file:
```bash
cat > .env << 'EOF'
# API Service Configuration
MEMORA_API_DATABASE_URL=postgresql://memora:memora_dev@localhost:5432/memora

# LLM Provider: "openai", "groq", or "ollama"
MEMORA_API_LLM_PROVIDER=groq

# API Key (not needed for ollama)
MEMORA_API_LLM_API_KEY=your_api_key_here

# LLM Model
MEMORA_API_LLM_MODEL=openai/gpt-oss-120b

# Optional: Custom base URL (for ollama or custom endpoints)
# MEMORA_API_LLM_BASE_URL=http://localhost:11434/v1

# Control Plane Configuration
MEMORA_CP_DATAPLANE_API_URL=http://localhost:8080
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
# Start all services with Docker (PostgreSQL, API, Control Plane)
cd ../docker
./start.sh

# Or start services individually:
# 1. Start PostgreSQL only
#    (then migrations run automatically when API starts)
# 2. Start the server with local environment
./scripts/start-server.sh --env local

# Stop all Docker services
cd ../docker
./stop.sh

# Erase all data and containers
cd ../docker
./clean.sh
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
- `PUT  /api/agents/{agent_id}` - Create/update agent with personality
- `GET  /api/agents/{agent_id}/profile` - Get agent profile
- `PUT  /api/agents/{agent_id}/profile` - Update personality traits
- `POST /api/agents/{agent_id}/background` - Merge agent background

## API Examples (curl)

### Create/Update Agent

```bash
# Create or update an agent with personality and background
curl -X PUT http://localhost:8080/api/agents/alice_agent \
  -H "Content-Type: application/json" \
  -d '{
    "personality": {
      "openness": 0.8,
      "conscientiousness": 0.6,
      "extraversion": 0.5,
      "agreeableness": 0.7,
      "neuroticism": 0.3,
      "bias_strength": 0.7
    },
    "background": "I am a creative software engineer with 10 years of startup experience"
  }'

# Create agent with just background (personality defaults to 0.5 for all traits)
curl -X PUT http://localhost:8080/api/agents/bob_agent \
  -H "Content-Type: application/json" \
  -d '{
    "background": "I am a data scientist interested in machine learning"
  }'
```

Response:
```json
{
  "agent_id": "alice_agent",
  "personality": {
    "openness": 0.8,
    "conscientiousness": 0.6,
    "extraversion": 0.5,
    "agreeableness": 0.7,
    "neuroticism": 0.3,
    "bias_strength": 0.7
  },
  "background": "I am a creative software engineer with 10 years of startup experience"
}
```

### Store Memories

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

### Temporal Queries

The system automatically detects temporal constraints and activates temporal graph retrieval:

```bash
# Temporal query - automatically uses 4-way retrieval with temporal graph
curl -X POST http://localhost:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "alice_agent",
    "query": "What did Alice do last spring?",
    "thinking_budget": 100,
    "top_k": 10
  }'
```

Supported temporal expressions:
- **Seasons**: "last spring", "this summer", "winter 2024"
- **Months**: "in June", "last March", "this November"
- **Relative**: "last year", "last month", "last week"
- **Ranges**: "between March and May"

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

## CLI Usage

The Memora CLI provides command-line access to memory operations and agent management:

**Memory Operations**:
```bash
# Store a memory
memora put <agent_id> "Alice works at Google"

# Search memories
memora search <agent_id> "What does Alice do?" --budget 100

# Think (reasoning with opinions)
memora think <agent_id> "What do you think about remote work?" -v
```

**Agent Management**:
```bash
# View agent profile
memora profile <agent_id>

# Update personality traits (all required)
memora set-personality <agent_id> \
  --openness 0.8 \
  --conscientiousness 0.6 \
  --extraversion 0.5 \
  --agreeableness 0.7 \
  --neuroticism 0.3 \
  --bias-strength 0.7

# Add/merge background
memora background <agent_id> "I was born in Texas"

# List all agents
memora agents
```

**Output Formats**:
```bash
# Pretty output (default)
memora search <agent_id> "query"

# JSON output
memora search <agent_id> "query" -o json

# YAML output
memora search <agent_id> "query" -o yaml

# Verbose mode (show requests/responses)
memora search <agent_id> "query" -v
```

## OpenAI Client Wrapper (`memora-openai`)

The `memora-openai` package provides a drop-in replacement for the OpenAI Python client that automatically integrates with Memora. It transparently stores conversations and injects relevant memories into prompts.

### Installation

```bash
cd memora-openai
uv pip install -e .
```

### Usage

```python
from memora_openai import configure, OpenAI

# Configure Memora integration once
configure(
    memora_api_url="http://localhost:8000",
    agent_id="my-agent",
    store_conversations=True,  # Store conversations to Memora
    inject_memories=True,      # Inject relevant memories into prompts
)

# Use OpenAI client as normal - Memora integration happens automatically
client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What did we discuss about AI?"}]
)
```

### Async Support

```python
from memora_openai import configure, AsyncOpenAI

configure(
    memora_api_url="http://localhost:8000",
    agent_id="my-agent",
)

client = AsyncOpenAI(api_key="sk-...")

response = await client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me about my preferences"}]
)
```

### Features

- **Automatic Memory Injection**: Relevant memories are automatically retrieved and injected as system messages before each API call
- **Conversation Storage**: All conversations are automatically stored to Memora for future retrieval
- **Zero Code Changes**: Works as a drop-in replacement for `openai.OpenAI` and `openai.AsyncOpenAI`
- **Configurable**: Control memory search budget, context window, and enable/disable features
- **Transparent**: Original OpenAI API responses are returned unchanged

### Configuration Options

```python
configure(
    memora_api_url="http://localhost:8000",  # Memora API URL
    agent_id="my-agent",                      # Agent identifier (required)
    store_conversations=True,                 # Store conversations
    inject_memories=True,                     # Inject memories
    memory_search_budget=10,                  # Number of memories to retrieve
    context_window=10,                        # Conversation history size
    document_id="session-123",                # Optional: Group conversations by document ID
    enabled=True,                             # Master switch
)
```

See [memora-openai/README.md](memora-openai/README.md) for full documentation and examples.

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
