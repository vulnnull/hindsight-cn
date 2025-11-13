# memora-client

Python client for Memora - Semantic memory system with personality-driven thinking.

**Auto-generated from OpenAPI spec** - provides type-safe access to all Memora API endpoints.

## Installation

```bash
pip install memora-client
```

## Quick Start

```python
from agent_memory_api_client import Client
from agent_memory_api_client.api.memory_storage import put_api_put_post
from agent_memory_api_client.api.reasoning import think_api_think_post

client = Client(base_url="http://localhost:8000")

# Store memory
put_api_put_post.sync(
    client=client,
    body={
        "agent_id": "user123",
        "content": "Alice loves machine learning"
    }
)

# Think (generate answer with personality)
response = think_api_think_post.sync(
    client=client,
    body={
        "agent_id": "user123",
        "query": "What does Alice think about AI?",
        "thinking_budget": 50
    }
)
print(response.text)
```

## Async Support

```python
from agent_memory_api_client import Client
from agent_memory_api_client.api.reasoning import think_api_think_post

async with Client(base_url="http://localhost:8000") as client:
    response = await think_api_think_post.asyncio(
        client=client,
        body={
            "agent_id": "user123",
            "query": "What does Alice think about AI?"
        }
    )
    print(response.text)
```

## API Modules

This client provides access to:
- `memory_storage` - Store and retrieve facts
- `search` - Semantic and temporal search
- `reasoning` - Personality-driven thinking
- `visualization` - Memory graphs and statistics
- `management` - Agent profiles and configuration
- `documents` - Document tracking

See auto-generated code for full API surface and type hints.

## Development

Auto-generated from `openapi.json`. See [RELEASE.md](../../RELEASE.md) for regeneration instructions.

## Links

- [GitHub Repository](https://github.com/nicoloboschi/memora)
- [Full Documentation](https://github.com/nicoloboschi/memora/blob/main/README.md)
