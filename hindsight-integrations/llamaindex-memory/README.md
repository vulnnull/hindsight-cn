# llama-index-memory-hindsight

Automatic long-term memory for LlamaIndex agents via [Hindsight](https://github.com/vectorize-io/hindsight).

Implements LlamaIndex's `BaseMemory` interface:
- **`put()`** — automatically retains user/assistant messages to Hindsight
- **`get()`** — recalls relevant memories and injects them as context
- **`reset()`** — clears the local chat buffer

## Installation

```bash
pip install llama-index-memory-hindsight
```

## Quick Start

```python
from hindsight_client import Hindsight
from llama_index.memory.hindsight import HindsightMemory
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI

client = Hindsight(base_url="http://localhost:8888")
memory = HindsightMemory.from_client(
    client=client,
    bank_id="user-123",
    mission="Track user preferences and project context",
)

agent = ReActAgent(tools=tools, llm=OpenAI(model="gpt-4o"), memory=memory)
```

## How It Works

- When the agent receives a message, `get(input)` recalls relevant memories from Hindsight and prepends them as a system message
- When the agent produces output, `put(message)` stores the conversation turn in Hindsight for future recall
- Chat history is kept in a local buffer for the current session; Hindsight provides cross-session persistence

## Requirements

- Python 3.10+
- `llama-index-core >= 0.11.0`
- `hindsight-client >= 0.4.0`
