"""Request/response interceptor for OpenAI API calls."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from agent_memory_api_client.client import Client
from agent_memory_api_client.models.search_request import SearchRequest
from agent_memory_api_client.models.batch_put_request import BatchPutRequest
from agent_memory_api_client.models.memory_item import MemoryItem
from agent_memory_api_client.api.memory_operations import (
    api_search_api_v1_agents_agent_id_memories_search_post as search_api,
    api_batch_put_async_api_v1_agents_agent_id_memories_async_post as batch_put_async_api,
)

from .config import get_config, MemoraConfig


class MemoraInterceptor:
    """Intercepts OpenAI API calls to integrate with Memora."""

    def __init__(self):
        """Initialize the interceptor with a Memora client."""
        self._client: Optional[Client] = None

    def get_client(self, config: MemoraConfig) -> Client:
        """Get or create the Memora client."""
        if self._client is None:
            self._client = Client(base_url=config.memora_api_url, timeout=30.0)
        return self._client

    async def close(self):
        """Close the client."""
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    def _extract_user_query(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Extract the most recent user message as a query.

        Args:
            messages: List of chat messages

        Returns:
            The last user message content, or None if not found
        """
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content")
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Handle structured content (e.g., with images)
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            return item.get("text")
        return None

    def _extract_conversation_context(
        self, messages: List[Dict[str, Any]], window: int = 10
    ) -> str:
        """Extract recent conversation context.

        Args:
            messages: List of chat messages
            window: Number of recent messages to include

        Returns:
            Formatted conversation context
        """
        recent_messages = messages[-window:] if len(messages) > window else messages
        context_parts = []

        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if isinstance(content, str):
                context_parts.append(f"{role}: {content}")
            elif isinstance(content, list):
                # Handle structured content
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                if text_parts:
                    context_parts.append(f"{role}: {' '.join(text_parts)}")

        return "\n".join(context_parts)

    async def inject_memories(
        self, messages: List[Dict[str, Any]], config: MemoraConfig
    ) -> List[Dict[str, Any]]:
        """Inject relevant memories into the conversation.

        Args:
            messages: Original chat messages
            config: Memora configuration

        Returns:
            Modified messages with injected memories
        """
        if not config.agent_id:
            return messages

        # Extract query from last user message
        query = self._extract_user_query(messages)
        if not query:
            return messages

        # Search for relevant memories
        try:
            client = self.get_client(config)

            # Create search request
            search_request = SearchRequest(
                query=query,
                thinking_budget=config.memory_search_budget,
                max_tokens=2048,
                trace=False,
                reranker="heuristic",
            )

            # Perform search
            search_response = await search_api.asyncio(
                agent_id=config.agent_id,
                client=client,
                body=search_request,
            )

            if not search_response or not search_response.results:
                return messages

            # Format memories as context
            memory_context = self._format_memories(
                [result.to_dict() for result in search_response.results]
            )

            # Inject memories into the conversation
            # We'll add it as a system message before the conversation
            memory_message = {
                "role": "system",
                "content": f"Relevant context from your memory:\n\n{memory_context}",
            }

            # Insert after any existing system messages but before the conversation
            insert_index = 0
            for i, msg in enumerate(messages):
                if msg.get("role") != "system":
                    insert_index = i
                    break

            modified_messages = (
                messages[:insert_index] + [memory_message] + messages[insert_index:]
            )
            return modified_messages

        except Exception as e:
            # Don't fail the request if memory injection fails
            print(f"Warning: Failed to inject memories: {e}")
            return messages

    def _format_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Format memory search results as context.

        Args:
            memories: List of memory results from Memora API

        Returns:
            Formatted context string
        """
        parts = []
        for i, memory in enumerate(memories, 1):
            text = memory.get("text", "")
            event_date = memory.get("event_date")
            fact_type = memory.get("fact_type", "")

            parts.append(f"{i}. {text}")
            if event_date:
                parts.append(f"   (Date: {event_date})")
            if fact_type:
                parts.append(f"   (Type: {fact_type})")

        return "\n".join(parts)

    async def store_conversation(
        self,
        messages: List[Dict[str, Any]],
        response: Any,
        config: MemoraConfig,
    ) -> None:
        """Store conversation to Memora.

        Args:
            messages: Chat messages sent to OpenAI
            response: Response from OpenAI
            config: Memora configuration
        """
        if not config.agent_id:
            return

        try:
            # Extract conversation context
            conversation_text = self._extract_conversation_context(
                messages, config.context_window
            )

            # Extract assistant response
            assistant_response = ""
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    assistant_response = choice.message.content or ""

            # Combine into a single memory item
            if conversation_text and assistant_response:
                full_conversation = (
                    f"{conversation_text}\nassistant: {assistant_response}"
                )

                # Determine event timestamp
                event_date = config.event_timestamp or datetime.utcnow().isoformat()

                # Create memory item
                memory_item = MemoryItem(
                    content=full_conversation,
                    event_date=event_date,
                    context="openai_conversation",
                )

                # Create batch put request
                batch_request = BatchPutRequest(
                    items=[memory_item],
                    document_id=config.document_id,
                )

                # Get client
                client = self.get_client(config)

                # Store to Memora
                await batch_put_async_api.asyncio(
                    agent_id=config.agent_id,
                    client=client,
                    body=batch_request,
                )

        except Exception as e:
            # Don't fail the request if storage fails
            print(f"Warning: Failed to store conversation: {e}")


# Global interceptor instance
_interceptor: Optional[MemoraInterceptor] = None


def get_interceptor() -> MemoraInterceptor:
    """Get or create the global interceptor instance."""
    global _interceptor
    if _interceptor is None:
        _interceptor = MemoraInterceptor()
    return _interceptor


async def cleanup_interceptor():
    """Cleanup the global interceptor instance."""
    global _interceptor
    if _interceptor is not None:
        await _interceptor.close()
        _interceptor = None
