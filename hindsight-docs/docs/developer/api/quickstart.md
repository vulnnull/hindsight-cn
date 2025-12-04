---
sidebar_position: 0
---

# Quick Start

Get up and running with Hindsight in 60 seconds.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## Start the Server

<Tabs>
<TabItem value="pip" label="pip (API only)">

```bash
pip install hindsight-all
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

hindsight-api
```

API available at http://localhost:8888

</TabItem>
<TabItem value="docker" label="Docker (Full Experience)">

```bash
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=groq \
  -e HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx \
  ghcr.io/vectorize-io/hindsight
```

- **API**: http://localhost:8888
- **Control Plane** (Web UI): http://localhost:9999

</TabItem>
</Tabs>

:::tip LLM Provider
Hindsight requires an LLM with structured output support. Recommended: **Groq** with `gpt-oss-20b` for fast, cost-effective inference. Also supports OpenAI and Ollama.
:::

---

## Use the Client

<Tabs>
<TabItem value="python" label="Python">

```bash
pip install hindsight-client
```

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain: Store information
client.retain(bank_id="my-bank", content="Alice works at Google as a software engineer")

# Recall: Search memories
client.recall(bank_id="my-bank", query="What does Alice do?")

# Reflect: Generate personality-aware response
client.reflect(bank_id="my-bank", query="Tell me about Alice")
```

</TabItem>
<TabItem value="node" label="Node.js">

```bash
npm install @vectorize-io/hindsight-client
```

```javascript
const { HindsightClient } = require('@vectorize-io/hindsight-client');

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

// Retain: Store information
await client.retain('my-bank', 'Alice works at Google as a software engineer');

// Recall: Search memories
await client.recall('my-bank', 'What does Alice do?');

// Reflect: Generate response
await client.reflect('my-bank', 'Tell me about Alice');
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

```bash
# Retain: Store information
hindsight memory retain my-bank "Alice works at Google as a software engineer"

# Recall: Search memories
hindsight memory recall my-bank "What does Alice do?"

# Reflect: Generate response
hindsight memory reflect my-bank "Tell me about Alice"
```

</TabItem>
</Tabs>

---

## What's Happening

| Operation | What it does |
|-----------|--------------|
| **Retain** | Content is processed, facts are extracted, entities are identified and linked in a knowledge graph |
| **Recall** | Four search strategies (semantic, keyword, graph, temporal) run in parallel to find relevant memories |
| **Reflect** | Retrieved memories are used to generate a personality-aware response |

---

## Next Steps

- [**Retain**](./retain) — Advanced options for storing memories
- [**Recall**](./recall) — Search and retrieval strategies
- [**Reflect**](./reflect) — Personality-aware reasoning
- [**Memory Banks**](./memory-banks) — Configure personality and background
- [**Server Deployment**](/developer/installation) — Docker Compose, Helm, and production setup
