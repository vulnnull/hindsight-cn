---
sidebar_position: 3
---

# LangGraph

Hindsight provides a `BaseStore` implementation for LangGraph's memory system.

## Installation

```bash
cd hindsight-langmem && uv pip install -e .
```

## Quick Start

```python
from hindsight_langmem import HindsightStore

# Create store
store = HindsightStore(
    base_url="http://localhost:8888",
    default_agent_id="my-agent",
)

# Store data
store.put(
    namespace=("user", "preferences"),
    key="language",
    value={"language": "Python", "reason": "data science"}
)

# Retrieve data
item = store.get(namespace=("user", "preferences"), key="language")
print(item.value)  # {"language": "Python", "reason": "data science"}

# Search
results = store.search(
    namespace_prefix=("user",),
    query="programming language",
    limit=10
)
```

## How It Works

`HindsightStore` implements LangGraph's `BaseStore` interface:

- **Namespaces** map to Hindsight agent IDs (joined with `__`)
- **Keys** map to document IDs
- **Values** are stored as JSON in memory content

## BaseStore Interface

### put

Store an item:

```python
store.put(
    namespace=("user", "session-123"),
    key="preferences",
    value={"theme": "dark", "language": "en"}
)
```

### get

Retrieve an item:

```python
item = store.get(namespace=("user", "session-123"), key="preferences")
if item:
    print(item.value)  # {"theme": "dark", "language": "en"}
    print(item.created_at)
    print(item.updated_at)
```

### search

Search within a namespace:

```python
results = store.search(
    namespace_prefix=("user",),
    query="theme preferences",
    limit=10,
    offset=0
)

for item in results:
    print(f"{item.key}: {item.value}")
```

### delete

Delete an item:

```python
store.delete(namespace=("user", "session-123"), key="preferences")
```

## Async Support

All operations have async variants:

```python
await store.aput(namespace, key, value)
item = await store.aget(namespace, key)
results = await store.asearch(namespace_prefix, query)
await store.adelete(namespace, key)
```

## With LangGraph

```python
from langgraph.graph import StateGraph
from hindsight_langmem import HindsightStore

store = HindsightStore(base_url="http://localhost:8888")

# Use store in your graph
graph = StateGraph()
# ... configure graph with store
```

## Namespace Mapping

Namespaces are converted to Hindsight agent IDs:

| Namespace | bank ID |
|-----------|----------|
| `("user",)` | `user` |
| `("user", "session")` | `user__session` |
| `("app", "v1", "data")` | `app__v1__data` |
| `()` | `default_agent_id` |

Memory banks are created automatically if they don't exist.
