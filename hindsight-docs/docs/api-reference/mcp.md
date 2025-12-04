---
sidebar_position: 3
---

# MCP API

Model Context Protocol (MCP) tools exposed by the Hindsight MCP server.

## Endpoint

```
/mcp/{bank_id}/sse
```

The `bank_id` is extracted from the URL path and used for all tool operations. The MCP server uses Server-Sent Events (SSE) transport.

## Available Tools

### retain

Store a new memory.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | yes | Memory content to store |
| `context` | string | no | Category for the memory (default: 'general') |

**Example:**

```json
{
  "name": "retain",
  "arguments": {
    "content": "User prefers Python for data analysis",
    "context": "preferences"
  }
}
```

**Response:**

```
Memory stored successfully
```

---

### recall

Search memories.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Natural language search query |
| `max_results` | integer | no | Maximum results to return (default: 10) |

**Example:**

```json
{
  "name": "recall",
  "arguments": {
    "query": "What does the user do for work?"
  }
}
```

**Response:**

```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "text": "User works at Google as a software engineer",
      "type": "world",
      "context": "work",
      "event_date": null
    }
  ]
}
```

---

## Usage Guidelines

**When to use `retain`:**
- User shares personal facts, preferences, or interests
- Important events or milestones are mentioned
- Decisions, opinions, or goals are stated

**When to use `recall`:**
- Start of conversation to get user context
- Before making recommendations
- To provide continuity across conversations
