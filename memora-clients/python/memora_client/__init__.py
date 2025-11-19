"""
Memora Client - Clean, pythonic wrapper for the Memora API.

This package provides a high-level interface for common Memora operations.
For advanced use cases, use the auto-generated API client directly.

Example:
    ```python
    from memora_client import Memora

    client = Memora(base_url="http://localhost:8000")

    # Store a memory
    client.put(agent_id="alice", content="Alice loves AI")

    # Search memories
    results = client.search(agent_id="alice", query="What does Alice like?")

    # Generate contextual answer
    answer = client.think(agent_id="alice", query="What are my interests?")
    ```
"""

from .memora_client import Memora

__all__ = ["Memora"]
