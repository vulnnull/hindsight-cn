# llama-index-tools-hindsight

LlamaIndex tools integration for [Hindsight](https://github.com/vectorize-io/hindsight) — persistent long-term memory for AI agents.

Provides Hindsight memory as a native LlamaIndex `BaseToolSpec`, giving agents retain/recall/reflect capabilities through LlamaIndex's standard tool interface.

For automatic memory (auto-recall on input, auto-retain on output), see [`llama-index-memory-hindsight`](../llamaindex-memory/).

## Installation

```bash
pip install llama-index-tools-hindsight
```

## Quick Start

```python
import asyncio
from hindsight_client import Hindsight
from llama_index.tools.hindsight import HindsightToolSpec
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent

async def main():
    client = Hindsight(base_url="http://localhost:8888")

    spec = HindsightToolSpec(
        client=client,
        bank_id="user-123",
        mission="Track user preferences",
    )
    tools = spec.to_tool_list()

    agent = ReActAgent(tools=tools, llm=OpenAI(model="gpt-4o"))
    response = await agent.run("Remember that I prefer dark mode")
    print(response)

asyncio.run(main())
```

### Factory Function

```python
from llama_index.tools.hindsight import create_hindsight_tools

tools = create_hindsight_tools(
    client=client,
    bank_id="user-123",
    include_reflect=False,  # only retain + recall
)
```

## Configuration

```python
from llama_index.tools.hindsight import configure

configure(
    hindsight_api_url="http://localhost:8888",
    api_key="your-api-key",
    budget="mid",
    tags=["source:llamaindex"],
    context="my-app",
    mission="Track user preferences",
)
```

## Requirements

- Python 3.10+
- `llama-index-core >= 0.11.0`
- `hindsight-client >= 0.4.0`

## Documentation

- [Integration docs](https://docs.hindsight.vectorize.io/docs/sdks/integrations/llamaindex)
- [Hindsight API docs](https://docs.hindsight.vectorize.io)
