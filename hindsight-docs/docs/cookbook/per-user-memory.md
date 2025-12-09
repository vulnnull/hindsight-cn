---
sidebar_position: 1
---

# Per-User Memory

The simplest pattern: give your agent persistent memory for each user. The agent remembers past conversations, user preferences, and context across sessions.

## The Problem

Without memory, every conversation starts from scratch:

```
Session 1: "I prefer dark mode and use Python"
Session 2: "What's my preferred language?" → Agent doesn't know
```

## The Solution: One Bank Per User

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User A Bank   │     │   User B Bank   │     │   User C Bank   │
│                 │     │                 │     │                 │
│  - Conversations│     │  - Conversations│     │  - Conversations│
│  - Preferences  │     │  - Preferences  │     │  - Preferences  │
│  - Context      │     │  - Context      │     │  - Context      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   100% isolated          100% isolated           100% isolated
```

Each user gets their own memory bank. Complete isolation, simple mental model.

## Implementation

### 1. Create a Bank When User Signs Up

```python
from hindsight import HindsightClient

client = HindsightClient()

def on_user_signup(user_id: str):
    client.create_bank(
        bank_id=f"user-{user_id}",
        name=f"Memory for {user_id}"
    )
```

### 2. Save Conversations After Each Session

```python
async def save_conversation(user_id: str, messages: list):
    await client.retain(
        bank_id=f"user-{user_id}",
        content=messages  # [{"role": "user", "content": "..."}, ...]
    )
```

### 3. Recall Context Before Responding

```python
async def get_context(user_id: str, query: str):
    result = await client.recall(
        bank_id=f"user-{user_id}",
        query=query
    )
    return result.results
```

### 4. Complete Agent Loop

```python
async def handle_message(user_id: str, user_message: str):
    # 1. Recall relevant context
    context = await client.recall(
        bank_id=f"user-{user_id}",
        query=user_message
    )

    # 2. Build prompt with memory
    prompt = f"""You are a helpful assistant with memory of past conversations.

## What you remember about this user
{format_results(context.results)}

## Current message
{user_message}
"""

    # 3. Generate response
    response = await llm.complete(prompt)

    # 4. Save the conversation
    await client.retain(
        bank_id=f"user-{user_id}",
        content=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ]
    )

    return response
```

## What Gets Remembered

Hindsight automatically extracts and connects:

- **Facts**: "User prefers Python", "User is building a CLI tool"
- **Entities**: People, projects, technologies mentioned
- **Relationships**: How entities relate to each other
- **Temporal context**: When things happened

You don't need to manually extract or structure this - just retain the conversations.

## When to Use This Pattern

**Good fit:**
- Chatbots and assistants
- Personal AI companions
- Any 1:1 user-to-agent interaction

**Consider adding shared knowledge if:**
- You have product docs or FAQs to reference
- Multiple users need access to the same information
- See [Support Agent with Shared Knowledge](./support-agent-with-shared-knowledge)
