---
sidebar_position: 5
---

# Claude Code

Biomimetic long-term memory for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) using [Hindsight](https://vectorize.io/hindsight). Automatically captures conversations and intelligently recalls relevant context — a complete port of [`hindsight-openclaw`](./openclaw) adapted to Claude Code's hook-based plugin architecture.

[View Changelog →](/changelog/integrations/claude-code)

## Quick Start

```bash
# 1. Add the Hindsight marketplace and install the plugin
claude plugin marketplace add vectorize-io/hindsight
claude plugin install hindsight-memory

# 2. Configure your LLM provider for memory extraction
# Option A: OpenAI (auto-detected)
export OPENAI_API_KEY="sk-your-key"

# Option B: Anthropic (auto-detected)
export ANTHROPIC_API_KEY="your-key"

# Option C: No API key needed (uses Claude Code's own model — personal/local use only)
export HINDSIGHT_LLM_PROVIDER=claude-code

# Option D: Connect to an external Hindsight server instead of running locally
mkdir -p ~/.hindsight
echo '{"hindsightApiUrl": "https://your-hindsight-server.com"}' > ~/.hindsight/claude-code.json

# 3. Start Claude Code — the plugin activates automatically
claude
```

That's it! The plugin will automatically start capturing and recalling memories.

## Features

- **Auto-recall** — on every user prompt, queries Hindsight for relevant memories and injects them as context (invisible to the chat transcript, visible to Claude)
- **Auto-retain** — after every response (or every N turns), extracts and retains conversation content to Hindsight for long-term storage
- **Daemon management** — can auto-start/stop `hindsight-embed` locally or connect to an external Hindsight server
- **Dynamic bank IDs** — supports per-agent, per-project, or per-session memory isolation
- **Channel-agnostic** — works with Claude Code Channels (Telegram, Discord, Slack) or interactive sessions
- **Zero dependencies** — pure Python stdlib, no pip install required

## Architecture

The plugin uses all four Claude Code hook events:

| Hook | Event | Purpose |
|------|-------|---------|
| `session_start.py` | `SessionStart` | Health check — verify Hindsight is reachable |
| `recall.py` | `UserPromptSubmit` | **Auto-recall** — query memories, inject as `additionalContext` |
| `retain.py` | `Stop` | **Auto-retain** — extract transcript, POST to Hindsight (async) |
| `session_end.py` | `SessionEnd` | Cleanup — stop auto-managed daemon if started |

## Connection Modes

### 1. External API (recommended for production)

Connect to a running Hindsight server (cloud or self-hosted). No local LLM needed — the server handles fact extraction.

```json
{
  "hindsightApiUrl": "https://your-hindsight-server.com",
  "hindsightApiToken": "your-token"
}
```

### 2. Local Daemon (auto-managed)

The plugin automatically starts and stops `hindsight-embed` via `uvx`. Requires an LLM provider API key for local fact extraction.

Set an LLM provider:
```bash
export OPENAI_API_KEY="sk-your-key"      # Auto-detected, uses gpt-4o-mini
# or
export ANTHROPIC_API_KEY="your-key"       # Auto-detected, uses claude-3-5-haiku
# or
export HINDSIGHT_LLM_PROVIDER=claude-code # No API key needed
```

### 3. Existing Local Server

If you already have `hindsight-embed` running, leave `hindsightApiUrl` empty and set `apiPort` to match your server's port. The plugin will detect it automatically.

## Configuration

All settings are in `~/.hindsight/claude-code.json`. Every setting can also be overridden via environment variables.

### Connection & Daemon

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| `hindsightApiUrl` | `""` | `HINDSIGHT_API_URL` | External Hindsight API URL. Empty = use local daemon. |
| `hindsightApiToken` | `null` | `HINDSIGHT_API_TOKEN` | Auth token for external API |
| `apiPort` | `9077` | `HINDSIGHT_API_PORT` | Port for local Hindsight daemon |
| `daemonIdleTimeout` | `0` | `HINDSIGHT_DAEMON_IDLE_TIMEOUT` | Seconds before idle daemon shuts down (0 = never) |
| `embedVersion` | `"latest"` | `HINDSIGHT_EMBED_VERSION` | `hindsight-embed` version for `uvx` |

### LLM Provider (daemon mode only)

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| `llmProvider` | auto-detect | `HINDSIGHT_LLM_PROVIDER` | LLM provider: `openai`, `anthropic`, `gemini`, `groq`, `ollama`, `openai-codex`, `claude-code` |
| `llmModel` | provider default | `HINDSIGHT_LLM_MODEL` | Model override |

Auto-detection checks these env vars in order: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`.

### Memory Bank

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| `bankId` | `"claude_code"` | `HINDSIGHT_BANK_ID` | Static bank ID (when `dynamicBankId` is false) |
| `bankMission` | generic assistant | `HINDSIGHT_BANK_MISSION` | Agent identity/purpose for the memory bank |
| `retainMission` | extraction prompt | — | Custom retain mission (what to extract from conversations) |
| `dynamicBankId` | `false` | `HINDSIGHT_DYNAMIC_BANK_ID` | Enable per-context memory banks |
| `dynamicBankGranularity` | `["agent", "project"]` | — | Fields for dynamic bank ID: `agent`, `project`, `session`, `channel`, `user` |
| `bankIdPrefix` | `""` | — | Prefix for all bank IDs (e.g. `"prod"`) |

### Auto-Recall

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| `autoRecall` | `true` | `HINDSIGHT_AUTO_RECALL` | Enable automatic memory recall |
| `recallBudget` | `"mid"` | `HINDSIGHT_RECALL_BUDGET` | Recall effort: `low`, `mid`, `high` |
| `recallMaxTokens` | `1024` | `HINDSIGHT_RECALL_MAX_TOKENS` | Max tokens in recall response |
| `recallContextTurns` | `1` | `HINDSIGHT_RECALL_CONTEXT_TURNS` | Prior turns for query composition |

### Auto-Retain

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| `autoRetain` | `true` | `HINDSIGHT_AUTO_RETAIN` | Enable automatic retention |
| `retainEveryNTurns` | `10` | — | Retain every Nth turn (sliding window) |
| `retainOverlapTurns` | `2` | — | Extra overlap turns for continuity |
| `retainRoles` | `["user", "assistant"]` | — | Which message roles to retain |

### Miscellaneous

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| `debug` | `false` | `HINDSIGHT_DEBUG` | Enable debug logging to stderr |

## Claude Code Channels

With [Claude Code Channels](https://docs.anthropic.com/en/docs/claude-code), Claude Code can operate as a persistent background agent connected to Telegram, Discord, Slack, and other messaging platforms. This plugin gives Channel-based agents the same long-term memory that `hindsight-openclaw` provides for Openclaw agents.

For Channel agents, enable dynamic bank IDs for per-channel/per-user memory isolation:

```json
{
  "dynamicBankId": true,
  "dynamicBankGranularity": ["agent", "channel", "user"]
}
```

And set channel context via environment variables:

```bash
export HINDSIGHT_CHANNEL_ID="telegram-group-12345"
export HINDSIGHT_USER_ID="user-67890"
```

## Troubleshooting

**Plugin not activating**: Check Claude Code logs for `[Hindsight]` messages. Enable `"debug": true` in `~/.hindsight/claude-code.json`.

**Recall returning no memories**: Verify the Hindsight server is reachable (`curl http://localhost:9077/health`). Memories need at least one retain cycle before they're available.

**Daemon not starting**: Ensure an LLM API key is set (or use `HINDSIGHT_LLM_PROVIDER=claude-code`). Review daemon logs at `~/.hindsight/profiles/claude-code.log`.

**High latency on recall**: The recall hook has a 12-second timeout. Use `recallBudget: "low"` or reduce `recallMaxTokens` for faster responses.
