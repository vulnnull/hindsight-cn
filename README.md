# Memora

**Long-term memory for AI agents.**

AI assistants forget everything between sessions. Memora fixes that with a memory system that handles temporal reasoning, entity connections, and personality-aware responses.

## Why Memora?

- **Temporal queries** — "What did Alice do last spring?" requires more than vector search
- **Entity connections** — Knowing "Alice works at Google" + "Google is in Mountain View" = "Alice works in Mountain View"
- **Agent opinions** — Agents form and recall beliefs with confidence scores
- **Personality** — Big Five traits influence how agents process and respond to information

## 5-Minute Setup

### 1. Start the server

```bash
# Clone and start with Docker
git clone https://github.com/anthropics/memora.git
cd memora/docker
./start.sh
```

Server runs at `http://localhost:8080`

### 2. Install the Python client

```bash
pip install memora-client
```

### 3. Use it

```python
from memora_client import Memora

client = Memora(base_url="http://localhost:8080")

# Store memories
client.store(agent_id="my-agent", content="Alice works at Google")
client.store(agent_id="my-agent", content="Bob prefers Python over JavaScript")

# Search memories
results = client.search(agent_id="my-agent", query="What does Alice do?")
for r in results:
    print(f"{r['text']} ({r['weight']:.2f})")

# Generate personality-aware responses
answer = client.think(agent_id="my-agent", query="Tell me about Alice")
print(answer["text"])
```

## Documentation

Full documentation: [memora-docs](./memora-docs)

- [Architecture](./memora-docs/docs/developer/architecture.md) — How ingestion, storage, and retrieval work
- [Python Client](./memora-docs/docs/sdks/python.md) — Full API reference
- [API Reference](./memora-docs/docs/api-reference/index.md) — REST API endpoints
- [Personality](./memora-docs/docs/developer/personality.md) — Big Five traits and opinion formation

## License

MIT
