---
sidebar_position: 0
---

# Installation

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## Choose Your Setup

<Tabs>
<TabItem value="python" label="Python">

### All-in-One (Recommended)

The `hindsight-all` package includes everything: embedded PostgreSQL, HTTP API server, and Python client.

```bash
pip install hindsight-all
```

**Use when:** You want the simplest setup for development or small deployments.

### Client Only

If you already have a Hindsight server running:

```bash
pip install hindsight-client
```

**Use when:** You're connecting to an existing Hindsight server (development, staging, or production).

</TabItem>
<TabItem value="node" label="Node.js">

```bash
npm install @hindsight/client
```

**Requires:** A running Hindsight server (see [Server Deployment](/developer/server) for setup).

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Coming soon
```

The CLI is included with the Rust distribution. See [CLI documentation](/sdks/cli) for installation.

</TabItem>
</Tabs>

## LLM Provider Setup

Hindsight requires an LLM that supports **structured output** for fact extraction and reasoning. Configure your provider:

<Tabs>
<TabItem value="openai" label="OpenAI">

```bash
export OPENAI_API_KEY=sk-...
```

**Requirement:** Model must support structured output (JSON mode)

</TabItem>
<TabItem value="groq" label="Groq">

```bash
export GROQ_API_KEY=gsk_...
```

**Requirement:** Model must support structured output (JSON mode)

</TabItem>
<TabItem value="ollama" label="Ollama (Local)">

```bash
# No API key needed - runs locally
```

**Requirement:** Model must support structured output (JSON mode)

See [Ollama documentation](https://ollama.ai) for setup.

</TabItem>
</Tabs>

## Verify Installation

<Tabs>
<TabItem value="python" label="Python">

```python
import hindsight
print(hindsight.__version__)
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
const { HindsightClient } = require('@hindsight/client');
console.log('Hindsight client loaded');
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight --version
```

</TabItem>
</Tabs>

## Next Steps

- [**Quick Start**](./quickstart) — Get running in 60 seconds
- [**Server Deployment**](/developer/server) — Production setup options
