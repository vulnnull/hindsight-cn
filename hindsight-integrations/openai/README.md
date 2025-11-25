# Hindsight-OpenAI

Drop-in replacement for OpenAI Python client with automatic Hindsight integration.

## Overview

`hindsight-openai` is a transparent wrapper around the official OpenAI Python client that automatically:
- 🧠 **Injects relevant memories** from your Hindsight system into conversations
- 💾 **Stores conversation history** to Hindsight for future retrieval
- 🔄 **Works seamlessly** with existing OpenAI code (just change the import)
- ⚡ **Supports both sync and async** clients

## Installation

This package is part of the Hindsight workspace. Install from the root:

```bash
# From repository root
uv sync

# Or install just this package
cd hindsight-integrations/openai
uv pip install -e .
```

## Quick Start

### Basic Usage

```python
from hindsight_openai import configure, OpenAI

# Configure Hindsight integration once
configure(
    hindsight_api_url="http://localhost:8888",
    agent_id="my-agent",
    store_conversations=True,
    inject_memories=True,
)

# Use OpenAI client as normal - Hindsight integration happens automatically
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
from hindsight_openai import configure, AsyncOpenAI

configure(
    hindsight_api_url="http://localhost:8888",
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
| `hindsight_api_url` | str | `"http://localhost:8888"` | URL of your Hindsight API server |
| `agent_id` | str | `None` | **Required.** Agent identifier for memory operations |
| `api_key` | str | `None` | Optional API key for Hindsight authentication |
| `store_conversations` | bool | `True` | Store conversations to Hindsight |
| `inject_memories` | bool | `True` | Inject relevant memories into prompts |
| `document_id` | str | `None` | Optional document ID for stored conversations |
| `enabled` | bool | `True` | Master switch to enable/disable Hindsight integration |

## How It Works

### Memory Injection

When `inject_memories=True`, the wrapper:

1. Extracts the user's query from the last message
2. Searches Hindsight for relevant memories using the query
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
3. Stores the complete exchange to Hindsight asynchronously
4. Tags it with context `"openai_conversation"` for filtering

This creates a searchable memory of all your AI conversations.

## Advanced Usage

### Disable for Specific Requests

```python
from hindsight_openai import configure, OpenAI, reset_config

# Configure globally
configure(hindsight_api_url="http://localhost:8888", agent_id="agent-1")

client = OpenAI(api_key="sk-...")

# Normal request with Hindsight
response1 = client.chat.completions.create(...)

# Temporarily disable
reset_config()
response2 = client.chat.completions.create(...)  # No Hindsight integration

# Re-enable
configure(hindsight_api_url="http://localhost:8888", agent_id="agent-1")
```

### Using Document ID

Group related conversations together using a document ID:

```python
configure(
    hindsight_api_url="http://localhost:8888",
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
from hindsight_openai import cleanup_interceptor

# Clean up resources when done
await cleanup_interceptor()
```

## Requirements

- Python >= 3.10
- openai >= 1.0.0
- httpx >= 0.23.0
- A running Hindsight API server

## Development

### Running Tests

```bash
uv run pytest tests
```

### Project Structure

```
hindsight-integrations/openai/
├── hindsight_openai/
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

Part of the Hindsight project.
