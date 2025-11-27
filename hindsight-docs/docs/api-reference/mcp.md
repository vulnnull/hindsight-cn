---
sidebar_position: 3
---

# MCP API

Model Context Protocol (MCP) tools exposed by the Hindsight MCP server.

## Available Tools

### hindsight_search

Search memories for a memory bank.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Search query |
| `agent_id` | string | no | bank ID (uses default if not specified) |
| `top_k` | integer | no | Number of results (default: 10) |

**Example:**

```json
{
  "name": "hindsight_search",
  "arguments": {
    "query": "What does Alice do for work?",
    "top_k": 5
  }
}
```

**Response:**

```json
{
  "results": [
    {
      "text": "Alice works at Google as a software engineer",
      "weight": 0.95,
      "fact_type": "world"
    }
  ]
}
```

---

### hindsight_think

Generate a personality-aware response using retrieved memories.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | yes | Question or prompt |
| `agent_id` | string | no | bank ID (uses default if not specified) |
| `budget` | string | no | Budget level: 'low', 'mid', 'high' (default: 'low') |

**Example:**

```json
{
  "name": "hindsight_think",
  "arguments": {
    "query": "What should I recommend to Alice?"
  }
}
```

**Response:**

```json
{
  "text": "Based on Alice's interest in machine learning and her work at Google, I would recommend...",
  "based_on": [
    {"text": "Alice works at Google", "weight": 0.95}
  ],
  "new_opinions": []
}
```

---

### hindsight_store

Store a new memory.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | yes | Memory content to store |
| `agent_id` | string | no | bank ID (uses default if not specified) |
| `context` | string | no | Context or topic of the memory |

**Example:**

```json
{
  "name": "hindsight_store",
  "arguments": {
    "content": "User prefers Python for data analysis",
    "context": "programming discussion"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Memory stored successfully"
}
```

---

### hindsight_agents

List all available memory banks.

**Parameters:** None

**Example:**

```json
{
  "name": "hindsight_agents",
  "arguments": {}
}
```

**Response:**

```json
{
  "memory banks": [
    {"agent_id": "default"},
    {"agent_id": "assistant"},
    {"agent_id": "researcher"}
  ]
}
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_URL` | Hindsight API URL | `http://localhost:8888` |
| `HINDSIGHT_AGENT_ID` | Default bank ID | Required |

## Error Responses

MCP tools return errors in the standard MCP error format:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Memory bank 'unknown-agent' not found"
  }
}
```

| Code | Description |
|------|-------------|
| `INVALID_PARAMS` | Missing or invalid parameters |
| `NOT_FOUND` | Memory bank or resource not found |
| `INTERNAL_ERROR` | Server error |
