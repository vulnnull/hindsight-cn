---
sidebar_position: 3
---

# MCP API

Model Context Protocol (MCP) tools exposed by the Hindsight MCP server.

## Available Tools

### hindsight_put

Store a new memory for a user.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_id` | string | yes | Unique identifier for the user (e.g., user_id, email) |
| `content` | string | yes | Memory content to store |
| `context` | string | yes | Category for the memory (e.g., 'personal_preferences', 'work_history') |
| `explanation` | string | no | Optional explanation for why this memory is being stored |

**Example:**

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

**Response:**

```
Fact stored successfully
```

---

### hindsight_search

Search memories for a user.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_id` | string | yes | Unique identifier for the user (e.g., user_id, email) |
| `query` | string | yes | Natural language search query |
| `max_tokens` | integer | no | Maximum tokens for results (default: 4096) |
| `explanation` | string | no | Optional explanation for why this search is being performed |

**Example:**

```json
{
  "name": "hindsight_search",
  "arguments": {
    "bank_id": "user_12345",
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
      "context": "work_history",
      "event_date": null,
      "document_id": null
    }
  ]
}
```

---

## Usage Guidelines

The MCP tools are designed for **per-user memory**:

- Each user MUST have a unique `bank_id` (user ID, email, session ID, etc.)
- Memories are isolated by `bank_id` — users cannot access each other's memories
- Use consistent `bank_id` values across all interactions with the same user

**When to use `hindsight_put`:**
- User shares personal facts, preferences, or interests
- Important events or milestones are mentioned
- Decisions, opinions, or goals are stated
- Any information the user would want remembered

**When to use `hindsight_search`:**
- Start of conversation to get user context
- Before making recommendations
- To provide continuity across conversations
- When user asks about something they may have mentioned before

---

## Error Responses

MCP tools return errors as strings:

```
Error: Memory bank 'unknown-bank' not found
```
