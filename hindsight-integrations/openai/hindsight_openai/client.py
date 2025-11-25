"""Drop-in replacement for OpenAI client with Hindsight integration."""

import asyncio
from typing import Any, Optional, List, Dict

from openai import OpenAI as _OpenAI, AsyncOpenAI as _AsyncOpenAI

from .config import get_config, is_configured
from .interceptor import get_interceptor


class _CompletionsWrapper:
    """Wrapper for chat completions with Hindsight integration (sync)."""

    def __init__(self, original_completions):
        """Initialize wrapper with original completions object."""
        self._original = original_completions

    def create(self, *args, **kwargs):
        """Create a chat completion with Hindsight integration."""
        if not is_configured():
            return self._original.create(*args, **kwargs)

        config = get_config()
        if not config.enabled:
            return self._original.create(*args, **kwargs)

        messages = kwargs.get("messages", [])
        if not messages:
            return self._original.create(*args, **kwargs)

        # Check if an event loop is already running (e.g., in Jupyter)
        try:
            running_loop = asyncio.get_running_loop()
            # If we get here, a loop is already running
            print(
                "Warning: Detected running event loop (Jupyter/IPython). "
                "Hindsight features are disabled in sync mode. "
                "Please use AsyncOpenAI for full functionality in notebooks."
            )
            return self._original.create(*args, **kwargs)
        except RuntimeError:
            # No loop running, we can create our own
            pass

        # Run async operations in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Inject memories if configured
            if config.inject_memories:
                interceptor = get_interceptor()
                modified_messages = loop.run_until_complete(
                    interceptor.inject_memories(messages, config)
                )
                kwargs["messages"] = modified_messages

            # Call original OpenAI API
            response = self._original.create(*args, **kwargs)

            # Store conversation if configured
            if config.store_conversations:
                interceptor = get_interceptor()
                loop.run_until_complete(
                    interceptor.store_conversation(
                        kwargs["messages"], response, config
                    )
                )

            return response
        finally:
            loop.close()

    def __getattr__(self, name):
        """Delegate all other attributes to the original completions."""
        return getattr(self._original, name)


class _AsyncCompletionsWrapper:
    """Wrapper for chat completions with Hindsight integration (async)."""

    def __init__(self, original_completions):
        """Initialize wrapper with original completions object."""
        self._original = original_completions

    async def create(self, *args, **kwargs):
        """Create a chat completion with Hindsight integration."""
        if not is_configured():
            return await self._original.create(*args, **kwargs)

        config = get_config()
        if not config.enabled:
            return await self._original.create(*args, **kwargs)

        messages = kwargs.get("messages", [])
        if not messages:
            return await self._original.create(*args, **kwargs)

        # Inject memories if configured
        if config.inject_memories:
            interceptor = get_interceptor()
            modified_messages = await interceptor.inject_memories(messages, config)
            kwargs["messages"] = modified_messages

        # Call original OpenAI API
        response = await self._original.create(*args, **kwargs)

        # Store conversation if configured
        if config.store_conversations:
            interceptor = get_interceptor()
            await interceptor.store_conversation(
                kwargs["messages"], response, config
            )

        return response

    def __getattr__(self, name):
        """Delegate all other attributes to the original completions."""
        return getattr(self._original, name)


class OpenAI(_OpenAI):
    """Drop-in replacement for OpenAI client with Hindsight integration.

    Usage:
        >>> from hindsight_openai import configure, OpenAI
        >>> configure(
        ...     hindsight_api_url="http://localhost:8888",
        ...     agent_id="my-agent",
        ...     store_conversations=True,
        ...     inject_memories=True,
        ... )
        >>> client = OpenAI(api_key="sk-...")
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """

    def __init__(self, *args, **kwargs):
        """Initialize OpenAI client with Hindsight integration."""
        super().__init__(*args, **kwargs)
        # Wrap chat completions with our interceptor
        self.chat.completions = _CompletionsWrapper(self.chat.completions)


class AsyncOpenAI(_AsyncOpenAI):
    """Drop-in replacement for AsyncOpenAI client with Hindsight integration.

    Usage:
        >>> from hindsight_openai import configure, AsyncOpenAI
        >>> configure(
        ...     hindsight_api_url="http://localhost:8888",
        ...     agent_id="my-agent",
        ...     store_conversations=True,
        ...     inject_memories=True,
        ... )
        >>> client = AsyncOpenAI(api_key="sk-...")
        >>> response = await client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """

    def __init__(self, *args, **kwargs):
        """Initialize AsyncOpenAI client with Hindsight integration."""
        super().__init__(*args, **kwargs)
        # Wrap chat completions with our interceptor
        self.chat.completions = _AsyncCompletionsWrapper(self.chat.completions)
