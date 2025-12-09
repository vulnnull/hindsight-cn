"""
Hindsight Client - Clean, pythonic wrapper for the Hindsight API.

This package provides a high-level interface for common Hindsight operations.
For advanced use cases, use the auto-generated API client directly.

Example:
    ```python
    from hindsight_client import Hindsight

    client = Hindsight(base_url="http://localhost:8888")

    # Store a memory
    result = client.retain(bank_id="alice", content="Alice loves AI")
    print(result.success)

    # Search memories
    results = client.recall(bank_id="alice", query="What does Alice like?")
    for r in results:
        print(r.text)

    # Generate contextual answer
    answer = client.reflect(bank_id="alice", query="What are my interests?")
    print(answer.text)
    ```
"""

from .hindsight_client import Hindsight

# Re-export response types for convenient access
from hindsight_client_api.models.retain_response import RetainResponse
from hindsight_client_api.models.recall_response import RecallResponse
from hindsight_client_api.models.recall_result import RecallResult
from hindsight_client_api.models.reflect_response import ReflectResponse
from hindsight_client_api.models.reflect_fact import ReflectFact
from hindsight_client_api.models.list_memory_units_response import ListMemoryUnitsResponse
from hindsight_client_api.models.bank_profile_response import BankProfileResponse
from hindsight_client_api.models.disposition_traits import DispositionTraits

__all__ = [
    "Hindsight",
    # Response types
    "RetainResponse",
    "RecallResponse",
    "RecallResult",
    "ReflectResponse",
    "ReflectFact",
    "ListMemoryUnitsResponse",
    "BankProfileResponse",
    "DispositionTraits",
]
