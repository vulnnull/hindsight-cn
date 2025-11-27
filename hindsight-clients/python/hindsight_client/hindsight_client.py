"""
Clean, pythonic wrapper for the Hindsight API client.

This file is MAINTAINED and NOT auto-generated. It provides a high-level,
easy-to-use interface on top of the auto-generated OpenAPI client.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

import hindsight_client_api
from hindsight_client_api.api import default_api
from hindsight_client_api.models import (
    recall_request,
    retain_request,
    memory_item,
    reflect_request,
)


def _run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


class Hindsight:
    """
    High-level, easy-to-use Hindsight API client.

    Example:
        ```python
        from hindsight_client import Hindsight

        client = Hindsight(base_url="http://localhost:8888")

        # Store a memory
        client.retain(bank_id="alice", content="Alice loves AI")

        # Recall memories
        results = client.recall(bank_id="alice", query="What does Alice like?")

        # Generate contextual answer
        answer = client.reflect(bank_id="alice", query="What are my interests?")
        ```
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the Hindsight client.

        Args:
            base_url: The base URL of the Hindsight API server
            timeout: Request timeout in seconds (default: 30.0)
        """
        config = hindsight_client_api.Configuration(host=base_url)
        self._api_client = hindsight_client_api.ApiClient(config)
        self._api = default_api.DefaultApi(self._api_client)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the API client."""
        if self._api_client:
            _run_async(self._api_client.close())

    # Simplified methods for main operations

    def retain(
        self,
        bank_id: str,
        content: str,
        timestamp: Optional[datetime] = None,
        context: Optional[str] = None,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Store a single memory (simplified interface).

        Args:
            bank_id: The memory bank ID
            content: Memory content
            timestamp: Optional event timestamp
            context: Optional context description
            document_id: Optional document ID for grouping
            metadata: Optional user-defined metadata

        Returns:
            Response with success status
        """
        return self.retain_batch(
            bank_id=bank_id,
            items=[{"content": content, "timestamp": timestamp, "context": context, "metadata": metadata}],
            document_id=document_id,
        )

    def retain_batch(
        self,
        bank_id: str,
        items: List[Dict[str, Any]],
        document_id: Optional[str] = None,
        async_: bool = False,
    ) -> Dict[str, Any]:
        """
        Store multiple memories in batch.

        Args:
            bank_id: The memory bank ID
            items: List of memory items with 'content' and optional 'timestamp', 'context', 'metadata'
            document_id: Optional document ID for grouping memories
            async_: If True, process asynchronously in background (default: False)

        Returns:
            Response with success status and item count
        """
        memory_items = [
            memory_item.MemoryItem(
                content=item["content"],
                timestamp=item.get("timestamp"),
                context=item.get("context"),
                metadata=item.get("metadata"),
            )
            for item in items
        ]

        request_obj = retain_request.RetainRequest(
            items=memory_items,
            document_id=document_id,
            async_=async_,
        )

        response = _run_async(self._api.retain_memories(bank_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    def recall(
        self,
        bank_id: str,
        query: str,
        types: Optional[List[str]] = None,
        max_tokens: int = 4096,
        budget: str = "mid",
    ) -> List[Dict[str, Any]]:
        """
        Recall memories using semantic similarity.

        Args:
            bank_id: The memory bank ID
            query: Search query
            types: Optional list of fact types to filter (world, agent, opinion, observation)
            max_tokens: Maximum tokens in results (default: 4096)
            budget: Budget level for recall - "low", "mid", or "high" (default: "mid")

        Returns:
            List of recall results
        """
        request_obj = recall_request.RecallRequest(
            query=query,
            types=types,
            budget=budget,
            max_tokens=max_tokens,
            trace=False,
        )

        response = _run_async(self._api.recall_memories(bank_id, request_obj))

        if hasattr(response, 'results'):
            return [r.to_dict() if hasattr(r, 'to_dict') else r for r in response.results]
        return []

    def reflect(
        self,
        bank_id: str,
        query: str,
        budget: str = "low",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a contextual answer based on bank identity and memories.

        Args:
            bank_id: The memory bank ID
            query: The question or prompt
            budget: Budget level for reflection - "low", "mid", or "high" (default: "low")
            context: Optional additional context

        Returns:
            Response with answer text and optionally facts used
        """
        request_obj = reflect_request.ReflectRequest(
            query=query,
            budget=budget,
            context=context,
        )

        response = _run_async(self._api.reflect(bank_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    # Full-featured methods (expose more options)

    def recall_memories(
        self,
        bank_id: str,
        query: str,
        types: Optional[List[str]] = None,
        budget: str = "mid",
        max_tokens: int = 4096,
        trace: bool = False,
        query_timestamp: Optional[str] = None,
        include_entities: bool = True,
        max_entity_tokens: int = 500,
    ) -> Dict[str, Any]:
        """
        Recall memories with all options (full-featured).

        Args:
            bank_id: The memory bank ID
            query: Search query
            types: Optional list of fact types to filter (world, agent, opinion, observation)
            budget: Budget level - "low", "mid", or "high"
            max_tokens: Maximum tokens in results
            trace: Enable trace output
            query_timestamp: Optional ISO format date string (e.g., '2023-05-30T23:40:00')
            include_entities: Include entity observations in results (default: True)
            max_entity_tokens: Maximum tokens for entity observations (default: 500)

        Returns:
            Full recall response with results, optional entities, and optional trace
        """
        from hindsight_client_api.models import include_options, entity_include_options

        include_opts = include_options.IncludeOptions(
            entities=entity_include_options.EntityIncludeOptions(max_tokens=max_entity_tokens) if include_entities else None
        )

        request_obj = recall_request.RecallRequest(
            query=query,
            types=types,
            budget=budget,
            max_tokens=max_tokens,
            trace=trace,
            query_timestamp=query_timestamp,
            include=include_opts,
        )

        response = _run_async(self._api.recall_memories(bank_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    def list_memories(
        self,
        bank_id: str,
        type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List memory units with pagination."""
        response = _run_async(self._api.list_memories(
            bank_id=bank_id,
            type=type,
            q=search_query,
            limit=limit,
            offset=offset,
        ))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    def create_bank(
        self,
        bank_id: str,
        name: Optional[str] = None,
        background: Optional[str] = None,
        personality: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Create or update a memory bank."""
        from hindsight_client_api.models import create_bank_request, personality_traits

        personality_obj = None
        if personality:
            personality_obj = personality_traits.PersonalityTraits(**personality)

        request_obj = create_bank_request.CreateBankRequest(
            name=name,
            background=background,
            personality=personality_obj,
        )

        response = _run_async(self._api.create_or_update_bank(bank_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    # Async methods (native async, no _run_async wrapper)

    async def aretain_batch(
        self,
        bank_id: str,
        items: List[Dict[str, Any]],
        document_id: Optional[str] = None,
        async_: bool = False,
    ) -> Dict[str, Any]:
        """
        Store multiple memories in batch (async).

        Args:
            bank_id: The memory bank ID
            items: List of memory items with 'content' and optional 'timestamp', 'context', 'metadata'
            document_id: Optional document ID for grouping memories
            async_: If True, process asynchronously in background (default: False)

        Returns:
            Response with success status and item count
        """
        memory_items = [
            memory_item.MemoryItem(
                content=item["content"],
                timestamp=item.get("timestamp"),
                context=item.get("context"),
                metadata=item.get("metadata"),
            )
            for item in items
        ]

        request_obj = retain_request.RetainRequest(
            items=memory_items,
            document_id=document_id,
            async_=async_,
        )

        response = await self._api.retain_memories(bank_id, request_obj)
        return response.to_dict() if hasattr(response, 'to_dict') else response

    async def aretain(
        self,
        bank_id: str,
        content: str,
        timestamp: Optional[datetime] = None,
        context: Optional[str] = None,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Store a single memory (async).

        Args:
            bank_id: The memory bank ID
            content: Memory content
            timestamp: Optional event timestamp
            context: Optional context description
            document_id: Optional document ID for grouping
            metadata: Optional user-defined metadata

        Returns:
            Response with success status
        """
        return await self.aretain_batch(
            bank_id=bank_id,
            items=[{"content": content, "timestamp": timestamp, "context": context, "metadata": metadata}],
            document_id=document_id,
        )

    async def arecall(
        self,
        bank_id: str,
        query: str,
        types: Optional[List[str]] = None,
        max_tokens: int = 4096,
        budget: str = "mid",
    ) -> List[Dict[str, Any]]:
        """
        Recall memories using semantic similarity (async).

        Args:
            bank_id: The memory bank ID
            query: Search query
            types: Optional list of fact types to filter (world, agent, opinion, observation)
            max_tokens: Maximum tokens in results (default: 4096)
            budget: Budget level for recall - "low", "mid", or "high" (default: "mid")

        Returns:
            List of recall results
        """
        request_obj = recall_request.RecallRequest(
            query=query,
            types=types,
            budget=budget,
            max_tokens=max_tokens,
            trace=False,
        )

        response = await self._api.recall_memories(bank_id, request_obj)

        if hasattr(response, 'results'):
            return [r.to_dict() if hasattr(r, 'to_dict') else r for r in response.results]
        return []

    async def areflect(
        self,
        bank_id: str,
        query: str,
        budget: str = "low",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a contextual answer based on bank identity and memories (async).

        Args:
            bank_id: The memory bank ID
            query: The question or prompt
            budget: Budget level for reflection - "low", "mid", or "high" (default: "low")
            context: Optional additional context

        Returns:
            Response with answer text and optionally facts used
        """
        request_obj = reflect_request.ReflectRequest(
            query=query,
            budget=budget,
            context=context,
        )

        response = await self._api.reflect(bank_id, request_obj)
        return response.to_dict() if hasattr(response, 'to_dict') else response
