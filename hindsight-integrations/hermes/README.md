# hindsight-hermes

Hindsight memory integration for [Hermes Agent](https://github.com/NousResearch/hermes-agent). Gives your Hermes agent persistent long-term memory via retain, recall, and reflect tools.

## What it does

**Automatic memory on every turn** — no tool calls required:

- **`pre_llm_call` hook** — Before each LLM call, recalls relevant memories and injects them into the system prompt. The model sees cross-session context automatically.
- **`post_llm_call` hook** — After each turn, retains the user/assistant exchange so it can be recalled in future sessions.

**Three explicit tools** for when the model wants direct control:

- **`hindsight_retain`** — Stores information to long-term memory. Hermes calls this when the user shares facts, preferences, or anything worth remembering.
- **`hindsight_recall`** — Searches long-term memory for relevant information. Returns a numbered list of matching memories.
- **`hindsight_reflect`** — Synthesizes a thoughtful answer from stored memories. Use this when you want Hermes to reason over what it knows rather than return raw facts.

These tools appear under the `[hindsight]` toolset in Hermes's `/tools` list.

> **Note:** The lifecycle hooks require hermes-agent with [PR #2823](https://github.com/NousResearch/hermes-agent/pull/2823) or later. On older versions, only the tools are registered — hooks are silently skipped.

## Setup

### 1. Install hindsight-hermes into the Hermes venv

The package must be installed in the **same Python environment** that Hermes runs in, so the entry point is discoverable.

```bash
# If you installed Hermes from source:
cd /path/to/hermes-agent
source .venv/bin/activate
pip install hindsight-hermes

# Or from a local checkout:
pip install -e /path/to/hindsight-integrations/hermes
```

### 2. Set environment variables

The plugin reads its configuration from environment variables. Set these before launching Hermes:

```bash
# Required — tells the plugin where Hindsight is running
export HINDSIGHT_API_URL=http://localhost:8888

# Required — the memory bank to read/write. Think of this as a "brain" for one user or agent.
export HINDSIGHT_BANK_ID=my-agent

# Optional — only needed if using Hindsight Cloud (https://api.hindsight.vectorize.io)
export HINDSIGHT_API_KEY=your-api-key

# Optional — recall budget: low (fast), mid (default), high (thorough)
export HINDSIGHT_BUDGET=mid
```

If neither `HINDSIGHT_API_URL` nor `HINDSIGHT_API_KEY` is set, the plugin silently skips registration — Hermes starts normally without the Hindsight tools.

### 3. Disable Hermes's built-in memory tool

Hermes has its own `memory` tool that saves to local files (`~/.hermes/`). If both are active, the LLM tends to prefer the built-in one since it's familiar. Disable it so the LLM uses Hindsight instead:

```bash
hermes tools disable memory
```

This persists across sessions. You can re-enable it later with `hermes tools enable memory`.

### 4. Start Hindsight API

In a separate terminal, start the Hindsight API server:

```bash
# From the hindsight repo
cd /path/to/hindsight-main
.venv/bin/hindsight-api

# Or if using Hindsight Cloud, skip this — just point HINDSIGHT_API_URL
# to https://api.hindsight.vectorize.io
```

Wait for the health check to pass:

```bash
curl http://localhost:8888/health
# {"status":"healthy","database":"connected"}
```

### 5. Launch Hermes

```bash
hermes
```

Verify the plugin loaded by typing `/tools` — you should see:

```
[hindsight]
  * hindsight_recall     - Search long-term memory for relevant information.
  * hindsight_reflect    - Synthesize a thoughtful answer from long-term memories.
  * hindsight_retain     - Store information to long-term memory for later retrieval.
```

### 6. Test it

**Store a memory:**
> Remember that my favourite colour is red

You should see `⚡ hindsight` in the response, confirming it called `hindsight_retain`.

**Recall a memory:**
> What's my favourite colour?

**Reflect on memories:**
> Based on what you know about me, suggest a colour scheme for my IDE

This calls `hindsight_reflect`, which synthesizes a response from all stored memories.

**Verify via API:**

```bash
curl -s http://localhost:8888/v1/default/banks/my-agent/memories/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "favourite colour", "budget": "low"}' | python3 -m json.tool
```

## Troubleshooting

### Tools don't appear in `/tools`

1. **Check the plugin is installed in the right venv.** Run this from the Hermes venv:
   ```bash
   python -c "from hindsight_hermes import register; print('OK')"
   ```

2. **Check the entry point is registered:**
   ```bash
   python -c "
   import importlib.metadata
   eps = importlib.metadata.entry_points(group='hermes_agent.plugins')
   print(list(eps))
   "
   ```
   You should see `EntryPoint(name='hindsight', value='hindsight_hermes', group='hermes_agent.plugins')`.

3. **Check env vars are set.** The plugin skips registration silently if `HINDSIGHT_API_URL` and `HINDSIGHT_API_KEY` are both unset.

### Hermes uses built-in memory instead of Hindsight

Run `hermes tools disable memory` and restart. The built-in `memory` tool and Hindsight tools have overlapping purposes — the LLM will prefer whichever it's more familiar with, which is usually the built-in one.

### Bank not found errors

The plugin auto-creates banks on first use. If you see bank errors, check that the Hindsight API is running and `HINDSIGHT_API_URL` is correct.

### Connection refused

Make sure the Hindsight API is running and listening on the URL you configured. Test with:
```bash
curl http://localhost:8888/health
```

## Manual registration (advanced)

If you don't want to use the plugin system, you can register tools directly in a Hermes startup script or custom agent:

```python
from hindsight_hermes import register_tools

register_tools(
    bank_id="my-agent",
    hindsight_api_url="http://localhost:8888",
    budget="mid",
    tags=["hermes"],           # applied to all retained memories
    recall_tags=["hermes"],    # filter recall to only these tags
)
```

This imports `tools.registry` from Hermes at call time and registers the three tools directly. This approach gives you more control over parameters but requires Hermes to be importable.

## Memory instructions (system prompt injection)

Pre-recall memories at startup and inject them into the system prompt, so the agent starts every conversation with relevant context:

```python
from hindsight_hermes import memory_instructions

context = memory_instructions(
    bank_id="my-agent",
    hindsight_api_url="http://localhost:8888",
    query="user preferences and important context",
    budget="low",
    max_results=5,
)
# Returns:
# Relevant memories:
# 1. User's favourite colour is red
# 2. User prefers dark mode
```

This never raises — if the API is down or no memories exist, it returns an empty string.

## Global configuration (advanced)

Instead of passing parameters to every call, configure once:

```python
from hindsight_hermes import configure

configure(
    hindsight_api_url="http://localhost:8888",
    api_key="your-key",
    budget="mid",
    tags=["hermes"],
)
```

Subsequent calls to `register_tools()` or `memory_instructions()` will use these defaults if no explicit values are provided.

## MCP alternative

Hermes also supports MCP servers natively. You can use Hindsight's MCP server directly instead of this plugin — no `hindsight-hermes` package needed:

```yaml
# In your Hermes config
mcp_servers:
  - name: hindsight
    url: http://localhost:8888/mcp
```

This exposes the same retain/recall/reflect operations through Hermes's MCP integration. The tradeoff is that MCP tools may have different naming and the LLM needs to discover them, whereas the plugin registers tools with Hermes-native schemas.

## Configuration reference

| Parameter | Env Var | Default | Description |
|-----------|---------|---------|-------------|
| `hindsight_api_url` | `HINDSIGHT_API_URL` | `https://api.hindsight.vectorize.io` | Hindsight API URL |
| `api_key` | `HINDSIGHT_API_KEY` | — | API key for authentication |
| `bank_id` | `HINDSIGHT_BANK_ID` | — | Memory bank ID |
| `budget` | `HINDSIGHT_BUDGET` | `mid` | Recall budget (low/mid/high) |
| — | `HINDSIGHT_AUTO_RETAIN` | `true` | Auto-retain conversation turns via `post_llm_call` hook |
| — | `HINDSIGHT_RECALL_BUDGET` | same as `budget` | Budget for the `pre_llm_call` recall hook |
| — | `HINDSIGHT_RECALL_MAX_TOKENS` | `4096` | Max tokens for the `pre_llm_call` recall hook |
| `max_tokens` | — | `4096` | Max tokens for recall results (tools) |
| `tags` | — | — | Tags applied when storing memories |
| `recall_tags` | — | — | Tags to filter recall results |
| `recall_tags_match` | — | `any` | Tag matching mode (any/all/any_strict/all_strict) |
| `toolset` | — | `hindsight` | Hermes toolset group name |
