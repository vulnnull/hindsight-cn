"""Request/response interceptor for OpenAI API calls."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from hindsight_client import Hindsight

from .config import get_config, HindsightConfig


class HindsightInterceptor:
    """Intercepts OpenAI API calls to integrate with Hindsight."""

    def __init__(self):
        """Initialize the interceptor with a Hindsight client."""
        self._client: Optional[Hindsight] = None

    def get_client(self, config: HindsightConfig) -> Hindsight:
        """Get or create the Hindsight client."""
        if self._client is None:
            self._client = Hindsight(base_url=config.hindsight_api_url, timeout=30.0)
        return self._client

    def close(self):
        """Close the client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    async def inject_memories(
        self,
        messages: List[Dict[str, Any]],
        config: HindsightConfig,
    ) -> List[Dict[str, Any]]:
        """
        Inject relevant memories into messages before sending to OpenAI.
        """
        if not config.enabled:
            return messages

        try:
            # Extract user query from messages
            user_query = self._extract_user_query(messages)
            if not user_query:
                return messages

            # Get client
            client = self.get_client(config)

            # Search for relevant memories
            results = client.search(
                agent_id=config.agent_id,
                query=user_query,
                max_tokens=4096,
                thinking_budget=500,
            )

            if not results:
                return messages

            # Format memories and add to context
            memory_context = self._format_memories(results)

            # Add memory context to system message or create new one
            updated_messages = self._add_memory_context(messages, memory_context)

            return updated_messages

        except Exception as e:
            # Don't fail the request if memory retrieval fails
            print(f"Warning: Failed to inject memories: {e}")
            return messages

    async def process_request(
        self,
        messages: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Process request before sending to OpenAI.
        Retrieves relevant memories and adds them to the context.
        """
        config = get_config()
        return await self.inject_memories(messages, config)

    async def store_conversation(
        self,
        messages: List[Dict[str, Any]],
        response: Any,
        config: HindsightConfig,
    ) -> None:
        """
        Store conversation in Hindsight after receiving response from OpenAI.
        """
        if not config.enabled or not config.store_conversations:
            return

        try:
            # Extract conversation context
            conversation = self._extract_conversation_context(messages, response)
            if not conversation:
                return

            # Get client
            client = self.get_client(config)

            # Store conversation as memories
            items = [
                {
                    "content": msg["content"],
                    "context": f"role:{msg['role']}",
                    "event_date": datetime.now(),
                }
                for msg in conversation
            ]

            # Store to Hindsight (async)
            client.put_batch(
                agent_id=config.agent_id,
                items=items,
            )

        except Exception as e:
            # Don't fail the request if storage fails
            print(f"Warning: Failed to store conversation: {e}")

    async def process_response(
        self,
        messages: List[Dict[str, Any]],
        response: Any,
        **kwargs: Any,
    ) -> None:
        """
        Process response after receiving from OpenAI.
        Stores the conversation in Hindsight.
        """
        config = get_config()
        await self.store_conversation(messages, response, config)

    def _extract_user_query(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Extract the user's query from messages."""
        # Get the last user message
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content")
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Handle structured content
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            return item.get("text")
        return None

    def _format_memories(self, results: List[Dict[str, Any]]) -> str:
        """Format memory search results into context string."""
        if not results:
            return ""

        memory_lines = []
        for i, result in enumerate(results, 1):
            text = result.get("text", "")
            if text:
                memory_lines.append(f"{i}. {text}")

        if not memory_lines:
            return ""

        return (
            "# Relevant Memories\n"
            "The following memories may be relevant to this conversation:\n\n"
            + "\n".join(memory_lines)
        )

    def _add_memory_context(
        self,
        messages: List[Dict[str, Any]],
        memory_context: str
    ) -> List[Dict[str, Any]]:
        """Add memory context to messages."""
        if not memory_context:
            return messages

        # Check if there's already a system message
        updated_messages = messages.copy()

        for i, msg in enumerate(updated_messages):
            if msg.get("role") == "system":
                # Append to existing system message
                updated_messages[i] = {
                    **msg,
                    "content": f"{msg['content']}\n\n{memory_context}"
                }
                return updated_messages

        # No system message found, prepend one
        system_message = {
            "role": "system",
            "content": memory_context
        }
        return [system_message] + updated_messages

    def _extract_conversation_context(
        self,
        messages: List[Dict[str, Any]],
        response: Any,
    ) -> List[Dict[str, str]]:
        """Extract conversation context for storage."""
        conversation = []

        # Add recent user messages
        for msg in messages[-3:]:  # Last 3 messages
            if msg.get("role") in ("user", "assistant"):
                content = msg.get("content")
                if isinstance(content, str):
                    conversation.append({
                        "role": msg["role"],
                        "content": content,
                    })

        # Add assistant response
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message"):
                content = choice.message.content
                if content:
                    conversation.append({
                        "role": "assistant",
                        "content": content,
                    })

        return conversation


# Global interceptor instance
_interceptor = HindsightInterceptor()


def get_interceptor() -> HindsightInterceptor:
    """Get the global interceptor instance."""
    return _interceptor


def cleanup_interceptor() -> None:
    """Cleanup the global interceptor instance."""
    _interceptor.close()
