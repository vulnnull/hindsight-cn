"""Hindsight memory for LlamaIndex agents.

Provides automatic long-term memory via Hindsight's retain/recall APIs.
Messages are automatically stored on ``put()`` and relevant memories
are recalled on ``get()`` to enrich agent prompts.

Usage::

    from llama_index.memory.hindsight import HindsightMemory

    memory = HindsightMemory.from_client(
        client=client,
        bank_id="user-123",
    )
    agent = ReActAgent(tools=tools, llm=llm, memory=memory)
"""

from .base import HindsightMemory

__version__ = "0.1.0"

__all__ = ["HindsightMemory"]
