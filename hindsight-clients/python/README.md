# Memora Python Client

Clean, pythonic client for the Memora API - A semantic memory system with personality-driven thinking.

## Installation

```bash
pip install memora-client
```

## Quick Start

```python
from memora_client import Memora

# Initialize client
client = Memora(base_url="http://localhost:8888")

# Store a memory
client.store(agent_id="alice", content="Alice loves artificial intelligence")

# Search memories
results = client.search(agent_id="alice", query="What does Alice like?")
print(results)

# Generate contextual answer
answer = client.think(agent_id="alice", query="What are my interests?")
print(answer["text"])
```

## Main Operations

### Store Memories

```python
# Store a single memory
client.store(
    agent_id="alice",
    content="Alice completed a Python project using FastAPI",
    event_date=datetime(2024, 1, 15),
    context="work projects"
)

# Store multiple memories in batch
client.store_batch(
    agent_id="alice",
    items=[
        {"content": "Alice loves machine learning"},
        {"content": "Bob enjoys hiking", "event_date": datetime(2024, 10, 15)},
    ]
)
```

### Search Memories

```python
# Simple search
results = client.search(
    agent_id="alice",
    query="What does Alice like?",
    max_tokens=2048
)

# Advanced search with all options
response = client.search_memories(
    agent_id="alice",
    query="What are Alice's interests?",
    fact_type=["world"],
    max_tokens=4096,
    trace=True  # Include trace information
)
```

### Think (Generate Contextual Answers)

```python
answer = client.think(
    agent_id="alice",
    query="What should I focus on learning next?",
    thinking_budget=100,
    context="I want to advance my career in AI"
)

print(answer["text"])  # The generated answer
print(answer["based_on"])  # Facts used to generate the answer
```

## Structure

```
memora-client/
├── memora_client/              # Maintained wrapper (simple API)
│   ├── __init__.py
│   ├── memora_client.py        # Clean interface: store(), search(), think()
│   └── tests/
│       └── test_main_operations.py
│
└── hindsight_client_api/          # Auto-generated from OpenAPI spec
    ├── api/                     # Full API operations
    ├── models/                  # Request/response models
    └── ...
```

## Testing

Run integration tests (requires running Memora API server):

```bash
# Set API URL (optional, defaults to http://localhost:8888)
export MEMORA_API_URL=http://localhost:8888

# Run tests
pytest memora_client/tests/test_main_operations.py -v
```

## Development

### Regenerate Client

The low-level API client is auto-generated from the OpenAPI spec. The high-level wrapper (`memora_client/`) is maintained and won't be overwritten.

```bash
# Regenerate from OpenAPI spec
./scripts/generate-clients.sh
```

This preserves:
- `memora_client/` - Maintained wrapper
- `pyproject.toml` - Package configuration
- Tests and documentation

## License

Apache 2.0
