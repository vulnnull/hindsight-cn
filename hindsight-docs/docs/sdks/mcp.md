---
sidebar_position: 4
---

# MCP Server

Model Context Protocol server for AI assistants like Claude Desktop.

## Installation

```bash
cd hindsight-cli && cargo build --release
```

## Claude Desktop Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hindsight": {
      "command": "/path/to/hindsight",
      "args": ["mcp-server"],
      "env": {
        "HINDSIGHT_API_URL": "http://localhost:8888",
        "HINDSIGHT_AGENT_ID": "claude-agent"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_URL` | Hindsight API URL | `http://localhost:8888` |
| `HINDSIGHT_AGENT_ID` | Default bank ID | Required |

## Available Tools

### hindsight_search

Search memories:

```json
{
  "name": "hindsight_search",
  "arguments": {
    "query": "What does Alice do for work?",
    "top_k": 5
  }
}
```

### hindsight_think

Generate response using memories:

```json
{
  "name": "hindsight_think",
  "arguments": {
    "query": "What should I recommend to Alice?"
  }
}
```

### hindsight_store

Store new memory:

```json
{
  "name": "hindsight_store",
  "arguments": {
    "content": "User prefers Python for data analysis",
    "context": "programming discussion"
  }
}
```

### hindsight_agents

List available memory banks:

```json
{
  "name": "hindsight_agents",
  "arguments": {}
}
```

## Usage Example

Once configured, Claude can use Hindsight naturally:

**User**: "Remember that I prefer morning meetings"

**Claude**: *Uses hindsight_store*

> "I've noted that you prefer morning meetings."

---

**User**: "What do you know about my preferences?"

**Claude**: *Uses hindsight_search*

> "Based on our conversations, you prefer morning meetings and like Python for data analysis."

## Testing

Run standalone:

```bash
hindsight mcp-server
```

Debug mode:

```bash
RUST_LOG=debug hindsight mcp-server
```
