---
sidebar_position: 1
---

# Python Client

Official Python client for the Memora API.

## Installation

```bash
pip install memora-client
```

## Quick Start

```python
from memora_client import Memora

client = Memora(base_url="http://localhost:8080")

# Store a memory
client.store(agent_id="my-agent", content="Alice works at Google")

# Search memories
results = client.search(agent_id="my-agent", query="What does Alice do?")
for r in results:
    print(r["text"], r["weight"])

# Generate response with personality
answer = client.think(agent_id="my-agent", query="Tell me about Alice")
print(answer["text"])
```

## Client Initialization

```python
from memora_client import Memora

client = Memora(
    base_url="http://localhost:8080",  # Memora API URL
    timeout=30.0,                       # Request timeout in seconds
)
```

## Memory Operations

### Store Single Memory

```python
client.store(
    agent_id="my-agent",
    content="Alice works at Google as a software engineer",
    context="career discussion",           # Optional context
    event_date="2024-01-15T10:00:00Z",    # Optional event date
)
```

### Store Batch

```python
client.store_batch(
    agent_id="my-agent",
    items=[
        {"content": "Alice works at Google", "context": "career"},
        {"content": "Bob is a data scientist", "context": "career"},
    ],
    document_id="conversation_001",  # Optional grouping
)
```

## Search Operations

### Basic Search

```python
results = client.search(
    agent_id="my-agent",
    query="What does Alice do?",
)

for r in results:
    print(f"{r['text']} (weight: {r['weight']})")
```

### Advanced Search

```python
results = client.search_memories(
    agent_id="my-agent",
    query="What does Alice do?",
    fact_type=["world", "agent"],  # Filter by type
    max_tokens=4096,               # Token budget for results
    top_k=10,                      # Max results
)
```

### Search by Fact Type

```python
# Search only world facts
world_facts = client.search_memories(
    agent_id="my-agent",
    query="Who works at Google?",
    fact_type=["world"],
)

# Search only opinions
opinions = client.search_memories(
    agent_id="my-agent",
    query="What do I think about Python?",
    fact_type=["opinion"],
)
```

## Think (Generate Response)

Generate personality-aware responses using retrieved memories:

```python
answer = client.think(
    agent_id="my-agent",
    query="What should I know about Alice?",
    thinking_budget=100,  # Tokens for query understanding
)

print(answer["text"])           # Generated response
print(answer["based_on"])       # Memories used
print(answer["new_opinions"])   # New opinions formed
```

## Agent Management

### Create Agent

```python
client.create_agent(
    agent_id="my-agent",
    name="Assistant",
    background="I am a helpful AI assistant",
    personality={
        "openness": 0.7,
        "conscientiousness": 0.8,
        "extraversion": 0.5,
        "agreeableness": 0.6,
        "neuroticism": 0.3,
        "bias_strength": 0.5,
    },
)
```

### Get Profile

```python
profile = client.get_profile(agent_id="my-agent")
print(profile["personality"])
print(profile["background"])
```

### List Agents

```python
agents = client.list_agents()
for agent in agents:
    print(agent["agent_id"])
```

### Update Personality

```python
client.update_personality(
    agent_id="my-agent",
    openness=0.9,
    conscientiousness=0.7,
)
```

### Update Background

```python
client.update_background(
    agent_id="my-agent",
    background="Additional context to merge with existing background",
)
```

## Error Handling

```python
from memora_client import Memora, MemoraError

client = Memora(base_url="http://localhost:8080")

try:
    results = client.search(agent_id="unknown", query="test")
except MemoraError as e:
    print(f"Error: {e.message}")
    print(f"Status: {e.status}")
```

## Async Support

```python
import asyncio
from memora_client import AsyncMemora

async def main():
    client = AsyncMemora(base_url="http://localhost:8080")

    # All methods have async versions
    await client.store(agent_id="my-agent", content="Hello world")
    results = await client.search(agent_id="my-agent", query="Hello")

    print(results)

asyncio.run(main())
```
