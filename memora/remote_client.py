"""
Remote client for Memora API.

This module provides a client that connects to a remote Memora API server
instead of using the local TemporalSemanticMemory instance directly.
"""
import httpx
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class RemoteMemoryClient:
    """
    HTTP client for Memora API that provides the same interface as TemporalSemanticMemory.

    This allows benchmarks to connect to a remote Memora API server instead of
    accessing the memory system directly.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 300.0):
        """
        Initialize remote memory client.

        Args:
            base_url: Base URL of the Memora API server (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 300s for large batch operations)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def initialize(self):
        """Initialize the client (no-op for remote client)."""
        pass

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def put_batch_async(
        self,
        agent_id: str,
        contents: List[Dict[str, Any]],
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store multiple memory items via API.

        Args:
            agent_id: Agent identifier
            contents: List of content dicts with 'content', 'event_date', 'context' keys
            document_id: Optional document identifier (always upserts if document exists)

        Returns:
            Result dict with success status
        """
        # Convert contents to API format
        items = []
        for content in contents:
            item = {
                "content": content["content"]
            }
            if "event_date" in content and content["event_date"]:
                # Convert datetime to ISO format string
                event_date = content["event_date"]
                if isinstance(event_date, datetime):
                    item["event_date"] = event_date.isoformat()
                else:
                    item["event_date"] = event_date
            if "context" in content and content["context"]:
                item["context"] = content["context"]
            items.append(item)

        # Make API request
        request_data = {
            "agent_id": agent_id,
            "items": items
        }

        if document_id:
            request_data["document_id"] = document_id

        response = await self.client.post(
            f"{self.base_url}/api/memories/batch_async",
            json=request_data
        )
        response.raise_for_status()
        return response.json()

    async def search_async(
        self,
        agent_id: str,
        query: str,
        thinking_budget: int = 100,
        max_tokens: int = 4096,
        enable_trace: bool = False,
        reranker: str = "heuristic",
        fact_type: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Search memories via API.

        Args:
            agent_id: Agent identifier
            query: Search query
            thinking_budget: Budget for spreading activation
            max_tokens: Maximum tokens to retrieve
            enable_trace: Whether to return trace information
            reranker: Reranker type ("heuristic" or other)
            fact_type: Optional list of fact types to search (e.g., ['world', 'agent'])

        Returns:
            Tuple of (results, trace)
        """
        request_data = {
            "agent_id": agent_id,
            "query": query,
            "thinking_budget": thinking_budget,
            "max_tokens": max_tokens,
            "trace": enable_trace,
            "reranker": reranker
        }

        if fact_type:
            request_data["fact_type"] = fact_type

        response = await self.client.post(
            f"{self.base_url}/api/search",
            json=request_data
        )
        response.raise_for_status()

        result = response.json()
        return result.get("results", []), result.get("trace")

    async def think_async(
        self,
        agent_id: str,
        query: str,
        thinking_budget: int = 50
    ) -> Dict[str, Any]:
        """
        Generate answer using think API.

        Args:
            agent_id: Agent identifier
            query: Question to answer
            thinking_budget: Budget for memory exploration

        Returns:
            Dict with 'text', 'based_on', and 'new_opinions' keys
        """
        request_data = {
            "agent_id": agent_id,
            "query": query,
            "thinking_budget": thinking_budget
        }

        response = await self.client.post(
            f"{self.base_url}/api/think",
            json=request_data
        )
        response.raise_for_status()
        return response.json()

    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete all data for an agent.

        Note: This endpoint may not be available in the API.
        For now, this is a no-op that returns success.

        Args:
            agent_id: Agent identifier

        Returns:
            Result dict
        """
        # Note: delete_agent is not exposed in the API yet
        # For benchmarks, we might need to manually clear data or use unique agent IDs
        return {"success": True, "message": "Delete agent not supported via API"}

    async def list_agents(self) -> List[str]:
        """
        List all agents.

        Returns:
            List of agent IDs
        """
        response = await self.client.get(f"{self.base_url}/api/agents")
        response.raise_for_status()
        result = response.json()
        return result.get("agents", [])

    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dict with statistics including total_nodes, total_links, and pending_operations
        """
        response = await self.client.get(f"{self.base_url}/api/stats/{agent_id}")
        response.raise_for_status()
        return response.json()

    async def wait_for_backlog_completion(
        self,
        agent_id: str,
        poll_interval: float = 1.0,
        timeout: float = 300.0,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Poll agent stats until pending_operations is zero or timeout is reached.

        Args:
            agent_id: Agent identifier
            poll_interval: Time to wait between polls in seconds (default: 1.0)
            timeout: Maximum time to wait in seconds (default: 300)
            verbose: Whether to print status updates

        Returns:
            Final stats dict

        Raises:
            TimeoutError: If pending_operations doesn't clear within timeout
        """
        import time
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Timeout waiting for pending operations to clear for agent '{agent_id}' "
                    f"after {timeout}s"
                )

            stats = await self.get_agent_stats(agent_id)
            pending_operations = stats.get("pending_operations", 0)

            if verbose:
                print(
                    f"Agent '{agent_id}' pending operations: {pending_operations} "
                    f"(elapsed: {elapsed:.1f}s)"
                )

            if pending_operations == 0:
                if verbose:
                    print(f"All operations completed for agent '{agent_id}' in {elapsed:.1f}s")
                return stats

            await asyncio.sleep(poll_interval)
