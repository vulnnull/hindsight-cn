---
sidebar_position: 1
---

# Quick Start

Get up and running with Hindsight in 60 seconds.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::tip Prerequisites
Make sure you've [installed Hindsight](./installation) and configured your LLM provider.
:::

## Basic Usage

<Tabs>
<TabItem value="python" label="Python">

### With All-in-One Package

```python
import os
from hindsight import HindsightServer, HindsightClient

# Start embedded server (PostgreSQL + HTTP API)
with HindsightServer(
    llm_provider="openai",
    llm_model="gpt-4o-mini",
    llm_api_key=os.environ["OPENAI_API_KEY"]
) as server:
    client = HindsightClient(base_url=server.url)

    # Retain: Store information
    client.retain(bank_id="my-bank", content="Alice works at Google as a software engineer")
    client.retain(bank_id="my-bank", content="Bob prefers Python over JavaScript")

    # Recall: Search memories
    results = client.recall(bank_id="my-bank", query="What does Alice do?")
    for r in results:
        print(r["text"])

    # Reflect: Generate personality-aware response
    response = client.reflect(bank_id="my-bank", query="Tell me about Alice")
    print(response["text"])
```

### With Client Only

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain: Store information
client.retain(bank_id="my-bank", content="Alice works at Google as a software engineer")

# Recall: Search memories
results = client.recall(bank_id="my-bank", query="What does Alice do?")

# Reflect: Generate response
response = client.reflect(bank_id="my-bank", query="Tell me about Alice")
print(response["text"])
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
const { HindsightClient } = require('@hindsight/client');

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

// Retain: Store information
await client.retain({
    bankId: 'my-bank',
    content: 'Alice works at Google as a software engineer'
});

// Recall: Search memories
const results = await client.recall({
    bankId: 'my-bank',
    query: 'What does Alice do?'
});

// Reflect: Generate response
const response = await client.reflect({
    bankId: 'my-bank',
    query: 'Tell me about Alice'
});
console.log(response.text);
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Retain: Store information
hindsight retain my-bank "Alice works at Google as a software engineer"

# Recall: Search memories
hindsight recall my-bank "What does Alice do?"

# Reflect: Generate response
hindsight reflect my-bank "Tell me about Alice"
```

</TabItem>
</Tabs>

## What's Happening

**Retain** → Content is processed, facts are extracted, entities are identified and linked in a knowledge graph

**Recall** → Four search strategies (semantic, keyword, graph, temporal) run in parallel to find relevant memories

**Reflect** → Retrieved memories are used to generate a personality-aware response with formed opinions

## Next Steps

- [**Main Methods**](./main-methods) — Detailed guide to retain, recall, and reflect
- [**Bank Identity**](./bank-identity) — Configure personality and background
- [**Server Options**](/developer/server) — Production deployment
