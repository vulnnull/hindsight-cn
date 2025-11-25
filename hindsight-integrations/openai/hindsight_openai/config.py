"""Global configuration for Hindsight-OpenAI integration."""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class HindsightConfig:
    """Configuration for Hindsight integration.

    Attributes:
        hindsight_api_url: URL of the Hindsight API server
        agent_id: Agent ID for memory operations
        api_key: Optional API key for Hindsight authentication
        store_conversations: Whether to store conversations to Hindsight
        inject_memories: Whether to inject relevant memories into prompts
        document_id: Optional document ID for stored conversations
        enabled: Master switch to enable/disable Hindsight integration
    """

    hindsight_api_url: str = "http://localhost:8888"
    agent_id: Optional[str] = None
    api_key: Optional[str] = None
    store_conversations: bool = True
    inject_memories: bool = True
    document_id: Optional[str] = None
    enabled: bool = True


# Global configuration instance
_global_config: Optional[HindsightConfig] = None


def configure(
    hindsight_api_url: str = "http://localhost:8888",
    agent_id: Optional[str] = None,
    api_key: Optional[str] = None,
    store_conversations: bool = True,
    inject_memories: bool = True,
    document_id: Optional[str] = None,
    enabled: bool = True,
) -> HindsightConfig:
    """Configure global Hindsight integration settings.

    Args:
        hindsight_api_url: URL of the Hindsight API server
        agent_id: Agent ID for memory operations (required)
        api_key: Optional API key for Hindsight authentication
        store_conversations: Whether to store conversations to Hindsight
        inject_memories: Whether to inject relevant memories into prompts
        document_id: Optional document ID for stored conversations
        enabled: Master switch to enable/disable Hindsight integration

    Returns:
        The configured HindsightConfig instance

    Example:
        >>> from hindsight_openai import configure, OpenAI
        >>> configure(
        ...     hindsight_api_url="http://localhost:8888",
        ...     agent_id="my-agent",
        ...     store_conversations=True,
        ...     inject_memories=True,
        ...     document_id="conversation-123",
        ... )
        >>> client = OpenAI(api_key="...")
    """
    global _global_config

    _global_config = HindsightConfig(
        hindsight_api_url=hindsight_api_url,
        agent_id=agent_id,
        api_key=api_key,
        store_conversations=store_conversations,
        inject_memories=inject_memories,
        document_id=document_id,
        enabled=enabled,
    )

    return _global_config


def get_config() -> Optional[HindsightConfig]:
    """Get the current global configuration.

    Returns:
        The current HindsightConfig instance, or None if not configured
    """
    return _global_config


def is_configured() -> bool:
    """Check if Hindsight has been configured.

    Returns:
        True if configure() has been called, False otherwise
    """
    return _global_config is not None and _global_config.enabled


def reset_config() -> None:
    """Reset the global configuration to None."""
    global _global_config
    _global_config = None
