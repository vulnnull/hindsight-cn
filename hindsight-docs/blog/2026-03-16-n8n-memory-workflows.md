---
title: "3 Nodes. Zero Code. Persistent Memory for n8n Workflows"
authors: [benfrank241]
date: 2026-03-16
tags: [n8n, tutorial, workflow, memory, no-code]
image: /img/blog/n8n-memory-workflows.png
---

![How to Add Persistent Memory to n8n Workflows](/img/blog/n8n-memory-workflows.png)

n8n workflows are stateless — every execution starts from zero. [Hindsight](https://ui.hindsight.vectorize.io/signup) adds persistent n8n memory via three HTTP Request nodes. No custom nodes, no vector database, no code.

<!-- truncate -->

**TL;DR:**
- n8n workflows are stateless — every execution starts from zero
- Hindsight adds persistent memory via three HTTP Request nodes
- No custom nodes, no vector database, no code
- Works with Hindsight Cloud (zero setup) or self-hosted
- Retain customer interactions, recall relevant context, reflect for synthesis
- Works with any [n8n](https://n8n.io/) workflow: support bots, lead enrichment, onboarding sequences

## The problem: n8n workflows without memory

You build an n8n workflow that handles customer support tickets. It triages, responds, escalates. It works.

But every execution is isolated.

Ticket comes in from Alice. Your workflow doesn't know Alice called last week about the same issue. Doesn't know she's on the Enterprise plan. Doesn't know she prefers email.

You could store this in a database. But then you need:

- A schema for every fact type
- Queries for every retrieval pattern
- Logic to decide what's relevant

That's not a workflow anymore. That's a backend project.

What you actually need: store facts as they happen, retrieve what's relevant, and synthesize when asked. Without leaving n8n.

## Architecture: three nodes for n8n persistent memory

```
Trigger (webhook, schedule, etc.)
     ↓
Retain — POST to Hindsight, store the interaction
     ↓
Your workflow logic
     ↓
Recall — POST to Hindsight, get relevant past context
     ↓
AI node / response — use memory to personalize
```

Three [HTTP Request nodes](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/). Same workflow structure you already use.

Under the hood, Hindsight automatically extracts entities and relationships from your content, builds a [knowledge graph with semantic search](/blog/2026/03/12/spreading-activation-memory-graphs), and returns relevant facts when you query. You don't manage any of that — it's handled by the three API calls below.

## Setting up Hindsight and n8n

### Start Hindsight

You have two options: Hindsight Cloud (no setup) or self-hosted (run it yourself).

**Option A: Hindsight Cloud**

1. [Sign up at Hindsight Cloud](https://ui.hindsight.vectorize.io/signup)
2. Create a memory bank in the dashboard and copy your API key
3. Your base URL is `https://api.hindsight.vectorize.io` and all requests need an `Authorization: Bearer hsk_your-key-here` header.

This is the easiest path if you're using n8n Cloud, since n8n Cloud can't reach localhost. Hindsight Cloud gives you a public API endpoint with no infrastructure to manage.

**Option B: Self-hosted**

Install and start the memory server:

```bash
pip install hindsight-all
export HINDSIGHT_API_LLM_API_KEY=YOUR_OPENAI_KEY

hindsight-api
```

It runs at `http://localhost:8888`. Embedded Postgres, fact extraction, semantic search, knowledge graph — all included.

### Create a memory bank

If you're using Hindsight Cloud, create a bank in the dashboard. For self-hosted, create one via the API:

```bash
curl -X PUT http://localhost:8888/v1/default/banks/n8n-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "name": "n8n Workflow Memory",
    "mission": "Remember customer interactions and workflow context."
  }'
```

This is idempotent — safe to run multiple times.

### Start n8n

```bash
npx n8n
```

Open `http://localhost:5678` and create a new workflow.

## The three n8n memory operations: retain, recall, reflect

### Retain — store interactions as they happen

Add an [HTTP Request node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/) after your trigger:

- **Method**: POST
- **URL**:
  - Cloud: `https://api.hindsight.vectorize.io/v1/default/banks/n8n-workflow/memories`
  - Self-hosted: `http://YOUR_IP:8888/v1/default/banks/n8n-workflow/memories`
- **Send Body**: on
- **Body Content Type**: JSON
- **Specify Body**: Using JSON
- **JSON**:

```json
{"items": [{"content": "Customer Bob prefers email communication and is on the Enterprise plan."}]}
```

If you're using Hindsight Cloud, add an Authorization header: `Bearer hsk_your-key-here`. In the HTTP Request node, go to **Options → Headers** and add it.

> **Self-hosted gotcha**: Use your machine's IP address (e.g., `192.168.x.x`), not `localhost`. n8n resolves `localhost` to its own process. Find your IP with `ipconfig getifaddr en0` (macOS) or `hostname -I` (Linux). This doesn't apply if you're using Hindsight Cloud or n8n Cloud.

Click **Execute step**. You should get a success response:

```json
{
  "success": true,
  "bank_id": "n8n-workflow",
  "items_count": 1,
  "async": false
}
```

Hindsight extracts facts from the content automatically — entities, relationships, timestamps. You don't manage any of that.

### Recall — retrieve relevant context

Add another HTTP Request node:

- **Method**: POST
- **URL**:
  - Cloud: `https://api.hindsight.vectorize.io/v1/default/banks/n8n-workflow/memories/recall`
  - Self-hosted: `http://YOUR_IP:8888/v1/default/banks/n8n-workflow/memories/recall`
- **JSON**:

```json
{"query": "What do we know about Bob?", "budget": "low"}
```

Click **Execute step**. You'll see extracted facts come back:

```json
{
  "results": [
    {
      "text": "Bob prefers email communication and is subscribed to the Enterprise plan.",
      "type": "world",
      "entities": ["Bob"]
    }
  ]
}
```

This is what you inject into your AI node's system prompt to personalize responses.

### Reflect — synthesize across all memories

For synthesis questions — "summarize this customer" or "what patterns do we see" — use reflect:

- **Method**: POST
- **URL**:
  - Cloud: `https://api.hindsight.vectorize.io/v1/default/banks/n8n-workflow/reflect`
  - Self-hosted: `http://YOUR_IP:8888/v1/default/banks/n8n-workflow/reflect`
- **JSON**:

```json
{"query": "Summarize what we know about our customers"}
```

Reflect traverses the knowledge graph and reasons across all stored memories. It's slower than recall but produces synthesized analysis, not just raw facts.

## Making n8n memory dynamic

The examples above use hardcoded JSON. In a real workflow, you'd use [n8n expressions](https://docs.n8n.io/code/expressions/) to inject dynamic data.

For **retain**, wire in data from your trigger:

```json
{"items": [{"content": "{{ $json.customer_name }} submitted a {{ $json.ticket_type }} ticket: {{ $json.message }}"}]}
```

For **recall**, query based on the current customer:

```json
{"query": "What do we know about {{ $json.customer_name }}?", "budget": "low"}
```

For **reflect**, ask for a synthesis:

```json
{"query": "Summarize all interactions with {{ $json.customer_name }}"}
```

n8n expressions make the memory layer dynamic without writing code.

## Example: support bot with n8n memory

Here's a practical workflow:

1. **Webhook trigger** — receives incoming support message
2. **Recall node** — retrieves relevant past context for this customer
3. **AI node** (OpenAI, Anthropic, etc.) — generates response with memory in the system prompt
4. **Retain node** — stores the interaction for future reference
5. **Respond to Webhook** — sends the reply

The AI node gets a system prompt like:

```
You are a support agent. Here is what you know about this customer:
{{ $('Recall').item.json.results[0].text }}
```

Now your support bot remembers past conversations, knows customer preferences, and doesn't ask the same questions twice. You can further customize how the agent reasons about that context using [disposition traits](/blog/2026/03/13/disposition-aware-agents) — for example, making it more empathetic for support or more skeptical for fraud detection.

## Pitfalls and edge cases

1. **Use your machine IP, not localhost** (self-hosted only). n8n can't reach `localhost:8888` because it resolves to itself. Use `ipconfig getifaddr en0` (macOS) or `hostname -I` (Linux) to find your LAN IP. If you're using Hindsight Cloud, this isn't an issue — just use `https://api.hindsight.vectorize.io`.

2. **Retain is asynchronous.** Fact extraction happens in the background after the API returns. If you recall immediately after retaining, the new facts may not be available yet. Add a short delay or design your workflow so recall happens on subsequent executions.

3. **The retain endpoint is `/memories`, not `/memories/retain`.** The URL path is `POST /v1/default/banks/{bank_id}/memories` with an `items` array in the body. The Python client method is called `retain()` but the HTTP endpoint is different.

4. **Bank creation uses PUT, not POST.** `PUT /v1/default/banks/{bank_id}` — the bank ID is in the URL path, not the request body.

5. **Set Content-Type explicitly.** n8n's HTTP Request node handles this when you select JSON body content type, but if you switch modes or use expressions, make sure the header is set.

## Tradeoffs: n8n memory with Hindsight vs. a database

| | **Hindsight + n8n** | **Database + custom queries** |
|---|---|---|
| **Setup** | Three HTTP nodes | Schema design, migration, query logic |
| **What it stores** | Natural language facts | Structured records |
| **Retrieval** | Semantic search | Exact match / SQL |
| **Synthesis** | Built-in (reflect) | Build it yourself |
| **Maintenance** | Zero | Schema evolution, query tuning |

**Use Hindsight when**: you want natural language memory without building a backend — customer context, conversation history, learned preferences.

**Use a database when**: you need structured records with exact lookups — order IDs, account balances, inventory counts.

They complement each other. Use Hindsight for the fuzzy, contextual knowledge. Use your database for the structured data.

## Recap

- Three HTTP Request nodes give your n8n workflows persistent memory
- **Retain** (`POST /memories`) — store interactions as they happen
- **Recall** (`POST /memories/recall`) — retrieve relevant context before responding
- **Reflect** (`POST /reflect`) — synthesize across all stored memories
- Works with both [Hindsight Cloud](https://ui.hindsight.vectorize.io/signup) and self-hosted
- Use n8n expressions to make it dynamic

## Next steps

- **Add per-customer banks** — use a different `bank_id` per customer for full isolation
- **Use tags for scoped memory** — add `"tags": ["support"]` on retain, filter with `"tags": ["support"]` on recall
- **Wire recall into AI nodes** — inject memory context into system prompts for personalized responses
- **Try the hosted version** — [use Hindsight Cloud](https://ui.hindsight.vectorize.io/signup) instead of self-hosting
- **Explore the MCP server** — Hindsight also exposes an MCP endpoint at `/mcp/{bank_id}/` for tools that support it
- **Read the docs** — see the [full Hindsight API reference](https://docs.hindsight.vectorize.io/recall) for advanced features

Your workflows just got a long-term memory. No code required.
