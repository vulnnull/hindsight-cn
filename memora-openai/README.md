# Memora-OpenAI

Drop-in replacement for OpenAI Python client with automatic Memora integration.

## Overview

`memora-openai` is a transparent wrapper around the official OpenAI Python client that automatically:
- 🧠 **Injects relevant memories** from your Memora system into conversations
- 💾 **Stores conversation history** to Memora for future retrieval
- 🔄 **Works seamlessly** with existing OpenAI code (just change the import)
- ⚡ **Supports both sync and async** clients

## Installation

```bash
cd memora-openai
uv pip install -e .
```

## Quick Start

### Basic Usage

```python
from memora_openai import configure, OpenAI

# Configure Memora integration once
configure(
    memora_api_url="http://localhost:8000",
    agent_id="my-agent",
    store_conversations=True,
    inject_memories=True,
)

# Use OpenAI client as normal - Memora integration happens automatically
client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "What did we discuss about AI last week?"}
    ]
)

print(response.choices[0].message.content)
```

### Async Usage

```python
from memora_openai import configure, AsyncOpenAI

configure(
    memora_api_url="http://localhost:8000",
    agent_id="my-agent",
)

client = AsyncOpenAI(api_key="sk-...")

response = await client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Remind me about my preferences"}
    ]
)
```

## Configuration Options

The `configure()` function accepts the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `memora_api_url` | str | `"http://localhost:8000"` | URL of your Memora API server |
| `agent_id` | str | `None` | **Required.** Agent identifier for memory operations |
| `api_key` | str | `None` | Optional API key for Memora authentication |
| `store_conversations` | bool | `True` | Store conversations to Memora |
| `inject_memories` | bool | `True` | Inject relevant memories into prompts |
| `memory_search_budget` | int | `10` | Number of memories to retrieve for context |
| `auto_extract_facts` | bool | `False` | Automatically extract facts from responses |
| `event_timestamp` | str | `None` | Custom timestamp for memory events (ISO format) |
| `context_window` | int | `10` | Number of recent conversation turns to consider |
| `document_id` | str | `None` | Optional document ID for stored conversations |
| `enabled` | bool | `True` | Master switch to enable/disable Memora integration |

## How It Works

### Memory Injection

When `inject_memories=True`, the wrapper:

1. Extracts the user's query from the last message
2. Searches Memora for relevant memories using the query
3. Injects the top memories as a system message before the conversation
4. Sends the enhanced conversation to OpenAI

Example:

```python
# Your code:
messages = [
    {"role": "user", "content": "What's my favorite programming language?"}
]

# What gets sent to OpenAI (automatically):
messages = [
    {
        "role": "system",
        "content": "Relevant context from your memory:\n\n1. User prefers Python for its simplicity\n   (Date: 2024-01-15)\n   (Type: opinion)"
    },
    {"role": "user", "content": "What's my favorite programming language?"}
]
```

### Conversation Storage

When `store_conversations=True`, the wrapper:

1. Captures the conversation context (recent messages)
2. Captures the assistant's response
3. Stores the complete exchange to Memora asynchronously
4. Tags it with context `"openai_conversation"` for filtering

This creates a searchable memory of all your AI conversations.

## Advanced Usage

### Disable for Specific Requests

```python
from memora_openai import configure, OpenAI, reset_config

# Configure globally
configure(memora_api_url="http://localhost:8000", agent_id="agent-1")

client = OpenAI(api_key="sk-...")

# Normal request with Memora
response1 = client.chat.completions.create(...)

# Temporarily disable
reset_config()
response2 = client.chat.completions.create(...)  # No Memora integration

# Re-enable
configure(memora_api_url="http://localhost:8000", agent_id="agent-1")
```

### Custom Memory Search Budget

```python
configure(
    memora_api_url="http://localhost:8000",
    agent_id="my-agent",
    memory_search_budget=20,  # Retrieve more memories for richer context
)
```

### Using Document ID

Group related conversations together using a document ID:

```python
configure(
    memora_api_url="http://localhost:8000",
    agent_id="my-agent",
    document_id="meeting-2024-01-15",  # All conversations tagged with this ID
)

client = OpenAI(api_key="sk-...")

# All these calls will be stored under the same document
response1 = client.chat.completions.create(...)
response2 = client.chat.completions.create(...)
```

### Cleanup

```python
from memora_openai import cleanup_interceptor

# Clean up resources when done
await cleanup_interceptor()
```

## Requirements

- Python >= 3.10
- openai >= 1.0.0
- httpx >= 0.23.0
- A running Memora API server

## Development

### Running Tests

```bash
uv run pytest tests
```

### Project Structure

```
memora-openai/
├── src/memora_openai/
│   ├── __init__.py       # Main exports
│   ├── client.py         # OpenAI client wrappers
│   ├── config.py         # Global configuration
│   └── interceptor.py    # Request/response interception logic
├── tests/
│   └── test_client.py    # Test suite
├── pyproject.toml        # Package configuration
└── README.md             # This file
```

## License

Part of the Memora project.
