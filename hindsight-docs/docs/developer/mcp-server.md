---
sidebar_position: 5
---

# MCP Server

Hindsight includes a built-in [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that allows AI assistants to store and retrieve memories directly.

## Access

The MCP server is **enabled by default** and mounted at `/mcp` on the API server:

```
http://localhost:8888/mcp
```

To disable it, set the environment variable:

```bash
export HINDSIGHT_API_MCP_ENABLED=false
```

## Available Tools

### hindsight_put

Store information to a user's memory bank.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_id` | string | Yes | Unique identifier for the user (e.g., `user_12345`, `alice@example.com`) |
| `content` | string | Yes | The fact or memory to store |
| `context` | string | Yes | Category for the memory (e.g., `personal_preferences`, `work_history`) |
| `explanation` | string | No | Why this memory is being stored |

**Example:**
```json
{
  "name": "hindsight_put",
  "arguments": {
    "bank_id": "user_12345",
    "content": "User prefers Python over JavaScript for backend development",
    "context": "programming_preferences"
  }
}
```

**When to use:**
- User shares personal facts, preferences, or interests
- Important events or milestones are mentioned
- Decisions, opinions, or goals are stated
- Work context or project details are discussed

---

### hindsight_search

Search a user's memory bank to provide personalized responses.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_id` | string | Yes | Unique identifier for the user |
| `query` | string | Yes | Natural language search query |
| `max_tokens` | integer | No | Maximum tokens for results (default: 4096) |
| `explanation` | string | No | Why this search is being performed |

**Example:**
```json
{
  "name": "hindsight_search",
  "arguments": {
    "bank_id": "user_12345",
    "query": "What are the user's programming language preferences?"
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "fact_abc123",
      "text": "User prefers Python over JavaScript for backend development",
      "type": "world",
      "context": "programming_preferences",
      "event_date": null,
      "document_id": null
    }
  ]
}
```

**When to use:**
- Start of conversation to recall relevant context
- Before making recommendations
- When user asks about something they may have mentioned before
- To provide continuity across conversations

---

## Per-User Isolation

Both tools require a `bank_id` that uniquely identifies the user. Memories are strictly isolated per bank — one user cannot access another user's memories.

**Best practices:**
- Use consistent identifiers (user ID, email, session ID)
- Don't share `bank_id` between different users
- Only call these tools when you can identify the specific user

---

## Integration with AI Assistants

The MCP server can be used with any MCP-compatible AI assistant. For Claude Desktop integration using the CLI, see [MCP Server (CLI)](/sdks/mcp).
