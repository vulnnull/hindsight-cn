"""Memora-OpenAI: Drop-in replacement for OpenAI client with automatic Memora integration.

This package provides a transparent wrapper around the OpenAI Python client that
automatically stores conversations and injects relevant memories from your Memora
memory system.

Basic usage:
    >>> from memora_openai import configure, OpenAI
    >>>
    >>> # Configure Memora integration
    >>> configure(
    ...     memora_api_url="http://localhost:8000",
    ...     agent_id="my-agent",
    ...     store_conversations=True,
    ...     inject_memories=True,
    ... )
    >>>
    >>> # Use OpenAI client as normal - Memora integration is automatic
    >>> client = OpenAI(api_key="sk-...")
    >>> response = client.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[{"role": "user", "content": "What did we discuss about AI?"}]
    ... )

Async usage:
    >>> from memora_openai import configure, AsyncOpenAI
    >>>
    >>> configure(
    ...     memora_api_url="http://localhost:8000",
    ...     agent_id="my-agent",
    ... )
    >>>
    >>> client = AsyncOpenAI(api_key="sk-...")
    >>> response = await client.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[{"role": "user", "content": "Tell me about quantum computing"}]
    ... )

Configuration options:
    - memora_api_url: URL of your Memora API server
    - agent_id: Agent identifier for memory operations
    - api_key: Optional API key for Memora authentication
    - store_conversations: Whether to store conversations to Memora (default: True)
    - inject_memories: Whether to inject relevant memories (default: True)
    - memory_search_budget: Number of memories to retrieve (default: 10)
    - context_window: Number of conversation turns to store (default: 10)
    - enabled: Master switch to disable Memora integration (default: True)
"""

from .client import OpenAI, AsyncOpenAI
from .config import (
    configure,
    get_config,
    is_configured,
    reset_config,
    MemoraConfig,
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
    "MemoraConfig",
]
