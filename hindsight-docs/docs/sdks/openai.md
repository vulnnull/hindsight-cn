---
sidebar_position: 2
---

# OpenAI

Drop-in replacement for the OpenAI Python client with automatic memory integration.

## Installation

```bash
cd hindsight-openai && uv pip install -e .
```

## Quick Start

```python
from hindsight_openai import configure, OpenAI

# Configure once
configure(
    hindsight_api_url="http://localhost:8888",
    agent_id="my-agent",
)

# Use OpenAI client normally
client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What did we discuss about AI?"}]
)
```

## How It Works

The wrapper intercepts OpenAI calls:

1. **Before**: Retrieves relevant memories and injects as system message
2. **After**: Stores conversation to Hindsight

Your code works exactly as before, but now has memory.

## Configuration

```python
configure(
    hindsight_api_url="http://localhost:8888",  # Hindsight API
    agent_id="my-agent",                      # Required
    store_conversations=True,                 # Store conversations
    inject_memories=True,                     # Inject memories into prompts
    document_id="session-123",                # Group by document
    enabled=True,                             # Master switch
)
```

## Memory Injection

When enabled, memories are automatically injected:

```python
# Your code
messages = [{"role": "user", "content": "What trails did Alice recommend?"}]

# What gets sent to OpenAI
messages = [
    {
        "role": "system",
        "content": "Relevant context:\n- Alice loves hiking in Yosemite\n- Alice recommended Half Dome trail"
    },
    {"role": "user", "content": "What trails did Alice recommend?"}
]
```

## Async Support

```python
from hindsight_openai import configure, AsyncOpenAI

configure(hindsight_api_url="http://localhost:8888", agent_id="my-agent")

client = AsyncOpenAI(api_key="sk-...")

response = await client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me about my preferences"}]
)
```

## Streaming

Fully supported:

```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

## Disable Temporarily

```python
from hindsight_openai import configure

configure(enabled=False)  # Disable
configure(enabled=True)   # Re-enable
```
