---
sidebar_position: 4
---

# MCP Server

Model Context Protocol server for AI assistants like Claude Desktop.

## Setup

The MCP server is included in the Hindsight API. When running the API with MCP enabled (default), it exposes MCP tools via SSE at `/mcp/sse`.

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hindsight": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8888/mcp/sse"]
    }
  }
}
```

## Available Tools

### hindsight_put

Store a memory for a user:

```json
{
  "name": "hindsight_put",
  "arguments": {
    "bank_id": "user_12345",
    "content": "User prefers Python for data analysis",
    "context": "programming_preferences"
  }
}
```

### hindsight_search

Search memories for a user:

```json
{
  "name": "hindsight_search",
  "arguments": {
    "bank_id": "user_12345",
    "query": "What does the user do for work?"
  }
}
```

## Usage Example

Once configured, Claude can use Hindsight naturally:

**User**: "Remember that I prefer morning meetings"

**Claude**: *Uses hindsight_put*

> "I've noted that you prefer morning meetings."

---

**User**: "What do you know about my preferences?"

**Claude**: *Uses hindsight_search*

> "Based on our conversations, you prefer morning meetings and like Python for data analysis."

## Per-User Memory

The MCP tools require a `bank_id` for each user:

- Each user must have a unique `bank_id` (user ID, email, session ID)
- Memories are isolated by `bank_id`
- Use consistent `bank_id` values across interactions

See [MCP API Reference](/api-reference/mcp) for full parameter details.
