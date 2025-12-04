---
sidebar_position: 4
---

# MCP Server

Model Context Protocol server for AI assistants like Claude Desktop.

## Setup

The MCP server is included in the Hindsight API. When running the API with MCP enabled, it exposes MCP tools at `/mcp/{bank_id}/sse`.

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hindsight": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8888/mcp/my-bank-id/sse"]
    }
  }
}
```

Replace `my-bank-id` with your memory bank ID.

## Available Tools

### retain

Store a memory:

```json
{
  "name": "retain",
  "arguments": {
    "content": "User prefers Python for data analysis",
    "context": "preferences"
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | yes | Memory content to store |
| `context` | string | no | Category (default: 'general') |

### recall

Search memories:

```json
{
  "name": "recall",
  "arguments": {
    "query": "What does the user do for work?"
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Natural language search query |
| `max_results` | integer | no | Max results (default: 10) |

## Usage Example

Once configured, Claude can use Hindsight naturally:

**User**: "Remember that I prefer morning meetings"

**Claude**: *Uses retain*

> "I've noted that you prefer morning meetings."

---

**User**: "What do you know about my preferences?"

**Claude**: *Uses recall*

> "Based on our conversations, you prefer morning meetings and like Python for data analysis."
