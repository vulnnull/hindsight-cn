"""Configuration management for Memora MCP Server."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """MCP Server configuration."""

    agent_id: str
    api_url: str = "http://localhost:8080"
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        agent_id = os.getenv("MEMORA_AGENT_ID")
        if not agent_id:
            raise ValueError("MEMORA_AGENT_ID environment variable is required")

        return cls(
            agent_id=agent_id,
            api_url=os.getenv("MEMORA_API_URL", "http://localhost:8080"),
            api_key=os.getenv("MEMORA_API_KEY"),
        )
