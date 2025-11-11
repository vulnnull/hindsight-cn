"""Memora API client wrapper."""

import httpx
from typing import Any


class MemoraClient:
    """Client for interacting with Memora API."""

    def __init__(self, api_url: str, agent_id: str, api_key: str | None = None):
        self.api_url = api_url.rstrip("/")
        self.agent_id = agent_id
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def remember(
        self, content: str, context: str
    ) -> dict[str, Any]:
        """Store a memory using batch endpoint."""
        async with httpx.AsyncClient() as client:
            payload = {
                "agent_id": self.agent_id,
                "items": [
                    {
                        "content": content,
                        "context": context,
                    }
                ]
            }

            response = await client.post(
                f"{self.api_url}/api/memories/batch",
                json=payload,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def search(
        self, query: str, max_tokens: int = 4096
    ) -> dict[str, Any]:
        """Search memories using search endpoint."""
        async with httpx.AsyncClient() as client:
            payload = {
                "agent_id": self.agent_id,
                "query": query,
                "thinking_budget": 100,
                "max_tokens": max_tokens,
                "reranker": "heuristic",
                "trace": False,
            }

            response = await client.post(
                f"{self.api_url}/api/search",
                json=payload,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
