---
sidebar_position: 4
---

# MCP Server

Model Context Protocol server for AI assistants like Claude Desktop.

## Installation

```bash
cd memora-cli && cargo build --release
```

## Claude Desktop Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memora": {
      "command": "/path/to/memora",
      "args": ["mcp-server"],
      "env": {
        "MEMORA_API_URL": "http://localhost:8080",
        "MEMORA_AGENT_ID": "claude-agent"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMORA_API_URL` | Memora API URL | `http://localhost:8080` |
| `MEMORA_AGENT_ID` | Default agent ID | Required |

## Available Tools

### memora_search

Search memories:

```json
{
  "name": "memora_search",
  "arguments": {
    "query": "What does Alice do for work?",
    "top_k": 5
  }
}
```

### memora_think

Generate response using memories:

```json
{
  "name": "memora_think",
  "arguments": {
    "query": "What should I recommend to Alice?"
  }
}
```

### memora_store

Store new memory:

```json
{
  "name": "memora_store",
  "arguments": {
    "content": "User prefers Python for data analysis",
    "context": "programming discussion"
  }
}
```

### memora_agents

List available agents:

```json
{
  "name": "memora_agents",
  "arguments": {}
}
```

## Usage Example

Once configured, Claude can use Memora naturally:

**User**: "Remember that I prefer morning meetings"

**Claude**: *Uses memora_store*

> "I've noted that you prefer morning meetings."

---

**User**: "What do you know about my preferences?"

**Claude**: *Uses memora_search*

> "Based on our conversations, you prefer morning meetings and like Python for data analysis."

## Testing

Run standalone:

```bash
memora mcp-server
```

Debug mode:

```bash
RUST_LOG=debug memora mcp-server
```
