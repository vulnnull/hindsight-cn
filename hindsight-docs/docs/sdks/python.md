---
sidebar_position: 1
---

# Python Client

Official Python client for the Hindsight API.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## Installation

<Tabs>
<TabItem value="all-in-one" label="All-in-One (Recommended)">

The `hindsight-all` package includes embedded PostgreSQL, HTTP API server, and client:

```bash
pip install hindsight-all
```

</TabItem>
<TabItem value="client-only" label="Client Only">

If you already have a Hindsight server running:

```bash
pip install hindsight-client
```

</TabItem>
</Tabs>

## Quick Start

<Tabs>
<TabItem value="all-in-one" label="All-in-One">

```python
import os
from hindsight import HindsightServer, HindsightClient

with HindsightServer(
    llm_provider="openai",
    llm_model="gpt-4.1-mini",
    llm_api_key=os.environ["OPENAI_API_KEY"]
) as server:
    client = HindsightClient(base_url=server.url)

    # Retain a memory
    client.retain(bank_id="my-agent", content="Alice works at Google")

    # Recall memories
    results = client.recall(bank_id="my-agent", query="What does Alice do?")
    for r in results:
        print(r.text)

    # Reflect - generate response with personality
    answer = client.reflect(bank_id="my-agent", query="Tell me about Alice")
    print(answer.text)
```

</TabItem>
<TabItem value="client-only" label="Client Only">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain a memory
client.retain(bank_id="my-agent", content="Alice works at Google")

# Recall memories
results = client.recall(bank_id="my-agent", query="What does Alice do?")
for r in results:
    print(r.text)

# Reflect - generate response with personality
answer = client.reflect(bank_id="my-agent", query="Tell me about Alice")
print(answer.text)
```

</TabItem>
</Tabs>

## Client Initialization

```python
from hindsight_client import Hindsight

client = Hindsight(
    base_url="http://localhost:8888",  # Hindsight API URL
    timeout=30.0,                       # Request timeout in seconds
)
```

## Core Operations

### Retain (Store Memory)

```python
# Simple
client.retain(
    bank_id="my-agent",
    content="Alice works at Google as a software engineer",
)

# With options
from datetime import datetime

client.retain(
    bank_id="my-agent",
    content="Alice got promoted",
    context="career update",
    timestamp=datetime(2024, 1, 15),
    document_id="conversation_001",
    metadata={"source": "slack"},
)
```

### Retain Batch

```python
client.retain_batch(
    bank_id="my-agent",
    items=[
        {"content": "Alice works at Google", "context": "career"},
        {"content": "Bob is a data scientist", "context": "career"},
    ],
    document_id="conversation_001",
    retain_async=False,  # Set True for background processing
)
```

### Recall (Search)

```python
# Simple - returns list of RecallResult
results = client.recall(
    bank_id="my-agent",
    query="What does Alice do?",
)

for r in results:
    print(f"{r.text} (type: {r.type})")

# With options
results = client.recall(
    bank_id="my-agent",
    query="What does Alice do?",
    types=["world", "opinion"],  # Filter by fact type
    max_tokens=4096,
    budget="high",  # low, mid, or high
)
```

### Recall with Full Response

```python
# Returns RecallResponse with entities and trace info
response = client.recall_memories(
    bank_id="my-agent",
    query="What does Alice do?",
    types=["world", "experience"],
    budget="mid",
    max_tokens=4096,
    trace=True,
    include_entities=True,
    max_entity_tokens=500,
)

print(f"Found {len(response.results)} memories")
for r in response.results:
    print(f"  - {r.text}")

# Access entities
if response.entities:
    for entity in response.entities:
        print(f"Entity: {entity.name}")
```

### Reflect (Generate Response)

```python
answer = client.reflect(
    bank_id="my-agent",
    query="What should I know about Alice?",
    budget="low",  # low, mid, or high
    context="preparing for a meeting",
)

print(answer.text)  # Generated response
print(answer.based_on)  # Memories used
```

## Bank Management

### Create Bank

```python
client.create_bank(
    bank_id="my-agent",
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

### List Memories

```python
response = client.list_memories(
    bank_id="my-agent",
    type="world",  # Optional: filter by type
    search_query="Alice",  # Optional: text search
    limit=100,
    offset=0,
)

for memory in response.memories:
    print(f"{memory.id}: {memory.text}")
```

## Async Support

All methods have async versions prefixed with `a`:

```python
import asyncio
from hindsight_client import Hindsight

async def main():
    client = Hindsight(base_url="http://localhost:8888")

    # Async retain
    await client.aretain(bank_id="my-agent", content="Hello world")

    # Async recall
    results = await client.arecall(bank_id="my-agent", query="Hello")
    for r in results:
        print(r.text)

    # Async reflect
    answer = await client.areflect(bank_id="my-agent", query="What did I say?")
    print(answer.text)

    client.close()

asyncio.run(main())
```

## Response Types

The client exports response types for type hints:

```python
from hindsight_client import (
    Hindsight,
    RetainResponse,
    RecallResponse,
    RecallResult,
    ReflectResponse,
    BankProfileResponse,
    PersonalityTraits,
)
```

## Context Manager

```python
from hindsight_client import Hindsight

with Hindsight(base_url="http://localhost:8888") as client:
    client.retain(bank_id="my-agent", content="Hello")
    results = client.recall(bank_id="my-agent", query="Hello")
# Client automatically closed
```
