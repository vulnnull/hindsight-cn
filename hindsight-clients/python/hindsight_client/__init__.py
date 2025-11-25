"""
Hindsight Client - Clean, pythonic wrapper for the Hindsight API.

This package provides a high-level interface for common Hindsight operations.
For advanced use cases, use the auto-generated API client directly.

Example:
    ```python
    from hindsight_client import Hindsight

    client = Hindsight(base_url="http://localhost:8888")

    # Store a memory
    client.put(agent_id="alice", content="Alice loves AI")

    # Search memories
    results = client.search(agent_id="alice", query="What does Alice like?")

    # Generate contextual answer
    answer = client.think(agent_id="alice", query="What are my interests?")
    ```
"""

from .hindsight_client import Hindsight

__all__ = ["Hindsight"]
