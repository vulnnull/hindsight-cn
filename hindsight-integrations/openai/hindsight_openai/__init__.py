"""Hindsight-OpenAI: Drop-in replacement for OpenAI client with automatic Hindsight integration.

This package provides a transparent wrapper around the OpenAI Python client that
automatically stores conversations and injects relevant memories from your Hindsight
memory system.

Basic usage:
    >>> from hindsight_openai import configure, OpenAI
    >>>
    >>> # Configure Hindsight integration
    >>> configure(
    ...     hindsight_api_url="http://localhost:8888",
    ...     agent_id="my-agent",
    ...     store_conversations=True,
    ...     inject_memories=True,
    ... )
    >>>
    >>> # Use OpenAI client as normal - Hindsight integration is automatic
    >>> client = OpenAI(api_key="sk-...")
    >>> response = client.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[{"role": "user", "content": "What did we discuss about AI?"}]
    ... )

Async usage:
    >>> from hindsight_openai import configure, AsyncOpenAI
    >>>
    >>> configure(
    ...     hindsight_api_url="http://localhost:8888",
    ...     agent_id="my-agent",
    ... )
    >>>
    >>> client = AsyncOpenAI(api_key="sk-...")
    >>> response = await client.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[{"role": "user", "content": "Tell me about quantum computing"}]
    ... )

Configuration options:
    - hindsight_api_url: URL of your Hindsight API server
    - agent_id: Agent identifier for memory operations
    - api_key: Optional API key for Hindsight authentication
    - store_conversations: Whether to store conversations to Hindsight (default: True)
    - inject_memories: Whether to inject relevant memories (default: True)
    - memory_search_budget: Number of memories to retrieve (default: 10)
    - context_window: Number of conversation turns to store (default: 10)
    - enabled: Master switch to disable Hindsight integration (default: True)
"""

from .client import OpenAI, AsyncOpenAI
from .config import (
    configure,
    get_config,
    is_configured,
    reset_config,
    HindsightConfig,
)
from .interceptor import cleanup_interceptor

__version__ = "0.1.0"

__all__ = [
    "OpenAI",
    "AsyncOpenAI",
    "configure",
    "get_config",
    "is_configured",
    "reset_config",
    "cleanup_interceptor",
    "HindsightConfig",
]
