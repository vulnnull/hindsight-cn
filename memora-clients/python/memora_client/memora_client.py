"""
Clean, pythonic wrapper for the Memora API client.

This file is MAINTAINED and NOT auto-generated. It provides a high-level,
easy-to-use interface on top of the auto-generated OpenAPI client.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

import memora_client_api
from memora_client_api.api import memory_operations_api, reasoning_api, agent_management_api
from memora_client_api.models import (
    search_request,
    batch_put_request,
    memory_item,
    think_request,
)


def _run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


class Memora:
    """
    High-level, easy-to-use Memora API client.

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

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the Memora client.

        Args:
            base_url: The base URL of the Memora API server
            timeout: Request timeout in seconds (default: 30.0)
        """
        config = memora_client_api.Configuration(host=base_url)
        self._api_client = memora_client_api.ApiClient(config)
        self._memory_api = memory_operations_api.MemoryOperationsApi(self._api_client)
        self._reasoning_api = reasoning_api.ReasoningApi(self._api_client)
        self._agent_api = agent_management_api.AgentManagementApi(self._api_client)

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

    def put(
        self,
        agent_id: str,
        content: str,
        event_date: Optional[datetime] = None,
        context: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store a single memory (simplified interface).

        Args:
            agent_id: The agent ID
            content: Memory content
            event_date: Optional event timestamp
            context: Optional context description
            document_id: Optional document ID for grouping

        Returns:
            Response with success status
        """
        return self.put_batch(
            agent_id=agent_id,
            items=[{"content": content, "event_date": event_date, "context": context}],
            document_id=document_id,
        )

    def put_batch(
        self,
        agent_id: str,
        items: List[Dict[str, Any]],
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store multiple memories in batch.

        Args:
            agent_id: The agent ID
            items: List of memory items with 'content' and optional 'event_date', 'context'
            document_id: Optional document ID for grouping memories

        Returns:
            Response with success status and item count
        """
        memory_items = [
            memory_item.MemoryItem(
                content=item["content"],
                event_date=item.get("event_date"),
                context=item.get("context"),
            )
            for item in items
        ]

        request_obj = batch_put_request.BatchPutRequest(
            items=memory_items,
            document_id=document_id,
        )

        response = _run_async(self._memory_api.batch_put_memories(agent_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    def search(
        self,
        agent_id: str,
        query: str,
        fact_type: Optional[List[str]] = None,
        max_tokens: int = 4096,
        thinking_budget: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search memories using semantic similarity.

        Args:
            agent_id: The agent ID
            query: Search query
            fact_type: Optional list of fact types to filter (world, agent, opinion)
            max_tokens: Maximum tokens in results (default: 4096)
            thinking_budget: Token budget for search (default: 100)

        Returns:
            List of search results
        """
        request_obj = search_request.SearchRequest(
            query=query,
            fact_type=fact_type,
            thinking_budget=thinking_budget,
            max_tokens=max_tokens,
            trace=False,
        )

        response = _run_async(self._memory_api.search_memories(agent_id, request_obj))

        if hasattr(response, 'results'):
            return [r.to_dict() if hasattr(r, 'to_dict') else r for r in response.results]
        return []

    def think(
        self,
        agent_id: str,
        query: str,
        thinking_budget: int = 50,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a contextual answer based on agent identity and memories.

        Args:
            agent_id: The agent ID
            query: The question or prompt
            thinking_budget: Token budget for thinking (default: 50)
            context: Optional additional context

        Returns:
            Response with answer text, facts used, and new opinions
        """
        request_obj = think_request.ThinkRequest(
            query=query,
            thinking_budget=thinking_budget,
            context=context,
        )

        response = _run_async(self._reasoning_api.think(agent_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    # Full-featured methods (expose more options)

    def search_memories(
        self,
        agent_id: str,
        query: str,
        fact_type: Optional[List[str]] = None,
        thinking_budget: int = 100,
        max_tokens: int = 4096,
        trace: bool = False,
        question_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search memories with all options (full-featured).

        Args:
            agent_id: The agent ID
            query: Search query
            fact_type: Optional list of fact types to filter
            thinking_budget: Token budget for thinking
            max_tokens: Maximum tokens in results
            trace: Enable trace output
            question_date: Optional ISO format date string

        Returns:
            Full search response with results and optional trace
        """
        request_obj = search_request.SearchRequest(
            query=query,
            fact_type=fact_type,
            thinking_budget=thinking_budget,
            max_tokens=max_tokens,
            trace=trace,
            question_date=question_date,
        )

        response = _run_async(self._memory_api.search_memories(agent_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    def list_memories(
        self,
        agent_id: str,
        fact_type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List memory units with pagination."""
        response = _run_async(self._memory_api.list_memories(
            agent_id=agent_id,
            fact_type=fact_type,
            q=search_query,
            limit=limit,
            offset=offset,
        ))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    def create_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        background: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update an agent."""
        from memora_client_api.models import create_agent_request

        request_obj = create_agent_request.CreateAgentRequest(
            name=name,
            background=background,
        )

        response = _run_async(self._agent_api.create_or_update_agent(agent_id, request_obj))
        return response.to_dict() if hasattr(response, 'to_dict') else response

    # Async methods (native async, no _run_async wrapper)

    async def aput_batch(
        self,
        agent_id: str,
        items: List[Dict[str, Any]],
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store multiple memories in batch (async).

        Args:
            agent_id: The agent ID
            items: List of memory items with 'content' and optional 'event_date', 'context'
            document_id: Optional document ID for grouping memories

        Returns:
            Response with success status and item count
        """
        memory_items = [
            memory_item.MemoryItem(
                content=item["content"],
                event_date=item.get("event_date"),
                context=item.get("context"),
            )
            for item in items
        ]

        request_obj = batch_put_request.BatchPutRequest(
            items=memory_items,
            document_id=document_id,
        )

        response = await self._memory_api.batch_put_memories(agent_id, request_obj)
        return response.to_dict() if hasattr(response, 'to_dict') else response

    async def aput(
        self,
        agent_id: str,
        content: str,
        event_date: Optional[datetime] = None,
        context: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store a single memory (async).

        Args:
            agent_id: The agent ID
            content: Memory content
            event_date: Optional event timestamp
            context: Optional context description
            document_id: Optional document ID for grouping

        Returns:
            Response with success status
        """
        return await self.aput_batch(
            agent_id=agent_id,
            items=[{"content": content, "event_date": event_date, "context": context}],
            document_id=document_id,
        )

    async def asearch(
        self,
        agent_id: str,
        query: str,
        fact_type: Optional[List[str]] = None,
        max_tokens: int = 4096,
        thinking_budget: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search memories using semantic similarity (async).

        Args:
            agent_id: The agent ID
            query: Search query
            fact_type: Optional list of fact types to filter (world, agent, opinion)
            max_tokens: Maximum tokens in results (default: 4096)
            thinking_budget: Token budget for search (default: 100)

        Returns:
            List of search results
        """
        request_obj = search_request.SearchRequest(
            query=query,
            fact_type=fact_type,
            thinking_budget=thinking_budget,
            max_tokens=max_tokens,
            trace=False,
        )

        response = await self._memory_api.search_memories(agent_id, request_obj)

        if hasattr(response, 'results'):
            return [r.to_dict() if hasattr(r, 'to_dict') else r for r in response.results]
        return []

    async def athink(
        self,
        agent_id: str,
        query: str,
        thinking_budget: int = 50,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a contextual answer based on agent identity and memories (async).

        Args:
            agent_id: The agent ID
            query: The question or prompt
            thinking_budget: Token budget for thinking (default: 50)
            context: Optional additional context

        Returns:
            Response with answer text, facts used, and new opinions
        """
        request_obj = think_request.ThinkRequest(
            query=query,
            thinking_budget=thinking_budget,
            context=context,
        )

        response = await self._reasoning_api.think(agent_id, request_obj)
        return response.to_dict() if hasattr(response, 'to_dict') else response


# Alias for backward compatibility
MemoraClient = Memora
