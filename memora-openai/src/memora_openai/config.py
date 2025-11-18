"""Global configuration for Memora-OpenAI integration."""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class MemoraConfig:
    """Configuration for Memora integration.

    Attributes:
        memora_api_url: URL of the Memora API server
        agent_id: Agent ID for memory operations
        api_key: Optional API key for Memora authentication
        store_conversations: Whether to store conversations to Memora
        inject_memories: Whether to inject relevant memories into prompts
        memory_search_budget: Number of memories to retrieve for context
        auto_extract_facts: Whether to automatically extract facts from responses
        event_timestamp: Optional timestamp for memory events (defaults to current time)
        context_window: Number of recent conversation turns to consider
        document_id: Optional document ID for stored conversations
        enabled: Master switch to enable/disable Memora integration
    """

    memora_api_url: str = "http://localhost:8000"
    agent_id: Optional[str] = None
    api_key: Optional[str] = None
    store_conversations: bool = True
    inject_memories: bool = True
    memory_search_budget: int = 10
    auto_extract_facts: bool = False
    event_timestamp: Optional[str] = None
    context_window: int = 10
    document_id: Optional[str] = None
    enabled: bool = True


# Global configuration instance
_global_config: Optional[MemoraConfig] = None


def configure(
    memora_api_url: str = "http://localhost:8000",
    agent_id: Optional[str] = None,
    api_key: Optional[str] = None,
    store_conversations: bool = True,
    inject_memories: bool = True,
    memory_search_budget: int = 10,
    auto_extract_facts: bool = False,
    event_timestamp: Optional[str] = None,
    context_window: int = 10,
    document_id: Optional[str] = None,
    enabled: bool = True,
) -> MemoraConfig:
    """Configure global Memora integration settings.

    Args:
        memora_api_url: URL of the Memora API server
        agent_id: Agent ID for memory operations (required)
        api_key: Optional API key for Memora authentication
        store_conversations: Whether to store conversations to Memora
        inject_memories: Whether to inject relevant memories into prompts
        memory_search_budget: Number of memories to retrieve for context
        auto_extract_facts: Whether to automatically extract facts from responses
        event_timestamp: Optional timestamp for memory events
        context_window: Number of recent conversation turns to consider
        document_id: Optional document ID for stored conversations
        enabled: Master switch to enable/disable Memora integration

    Returns:
        The configured MemoraConfig instance

    Example:
        >>> from memora_openai import configure, OpenAI
        >>> configure(
        ...     memora_api_url="http://localhost:8000",
        ...     agent_id="my-agent",
        ...     store_conversations=True,
        ...     inject_memories=True,
        ...     document_id="conversation-123",
        ... )
        >>> client = OpenAI(api_key="...")
    """
    global _global_config

    _global_config = MemoraConfig(
        memora_api_url=memora_api_url,
        agent_id=agent_id,
        api_key=api_key,
        store_conversations=store_conversations,
        inject_memories=inject_memories,
        memory_search_budget=memory_search_budget,
        auto_extract_facts=auto_extract_facts,
        event_timestamp=event_timestamp,
        context_window=context_window,
        document_id=document_id,
        enabled=enabled,
    )

    return _global_config


def get_config() -> Optional[MemoraConfig]:
    """Get the current global configuration.

    Returns:
        The current MemoraConfig instance, or None if not configured
    """
    return _global_config


def is_configured() -> bool:
    """Check if Memora has been configured.

    Returns:
        True if configure() has been called, False otherwise
    """
    return _global_config is not None and _global_config.enabled


def reset_config() -> None:
    """Reset the global configuration to None."""
    global _global_config
    _global_config = None
