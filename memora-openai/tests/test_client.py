"""Tests for Memora-OpenAI client wrapper."""

import os
import pytest
from memora_openai import (
    configure,
    reset_config,
    OpenAI,
    AsyncOpenAI,
    is_configured,
)


@pytest.fixture(autouse=True)
def cleanup():
    """Reset configuration after each test."""
    yield
    reset_config()


@pytest.fixture
def groq_api_key():
    """Get Groq API key from environment."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        pytest.skip("GROQ_API_KEY environment variable not set")
    return api_key


@pytest.fixture
def memora_api_url():
    """Get Memora API URL from environment."""
    return os.getenv("MEMORA_API_URL", "http://localhost:8000")


class TestConfiguration:
    """Test configuration management."""

    def test_configure_basic(self):
        """Test basic configuration."""
        config = configure(
            memora_api_url="http://test:8000",
            agent_id="test-agent",
        )

        assert config.memora_api_url == "http://test:8000"
        assert config.agent_id == "test-agent"
        assert config.store_conversations is True
        assert config.inject_memories is True
        assert is_configured()

    def test_configure_custom_options(self):
        """Test configuration with custom options."""
        config = configure(
            memora_api_url="http://test:8000",
            agent_id="test-agent",
            store_conversations=False,
            inject_memories=False,
            memory_search_budget=20,
            context_window=5,
            document_id="test-doc",
        )

        assert config.store_conversations is False
        assert config.inject_memories is False
        assert config.memory_search_budget == 20
        assert config.context_window == 5
        assert config.document_id == "test-doc"

    def test_reset_config(self):
        """Test resetting configuration."""
        configure(memora_api_url="http://test:8000", agent_id="test-agent")
        assert is_configured()

        reset_config()
        assert not is_configured()


class TestSyncClient:
    """Test synchronous OpenAI client wrapper."""

    def test_client_creation(self, groq_api_key):
        """Test that client can be created."""
        configure(memora_api_url="http://test:8000", agent_id="test-agent")

        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        assert client is not None
        assert hasattr(client.chat.completions, "_original")

    def test_chat_completion_without_config(self, groq_api_key):
        """Test that chat completion works without Memora configuration."""
        reset_config()

        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'test' and nothing else"}],
            max_tokens=10,
        )

        assert response is not None
        assert len(response.choices) > 0
        assert response.choices[0].message.content is not None

    def test_wrapper_passthrough(self, groq_api_key, memora_api_url):
        """Test that wrapper passes through when features disabled."""
        configure(
            memora_api_url=memora_api_url,
            agent_id="test-sync-passthrough",
            inject_memories=False,
            store_conversations=False,
        )

        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'hello' and nothing else"}],
            max_tokens=10,
        )

        assert response is not None
        assert len(response.choices) > 0


class TestAsyncClient:
    """Test asynchronous OpenAI client wrapper."""

    def test_client_creation(self, groq_api_key):
        """Test that async client can be created."""
        configure(memora_api_url="http://test:8000", agent_id="test-agent")

        client = AsyncOpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        assert client is not None
        assert hasattr(client.chat.completions, "_original")

    async def test_chat_completion_without_config(self, groq_api_key):
        """Test that async chat completion works without Memora configuration."""
        reset_config()

        client = AsyncOpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'test' and nothing else"}],
            max_tokens=10,
        )

        assert response is not None
        assert len(response.choices) > 0
        assert response.choices[0].message.content is not None

    async def test_wrapper_passthrough(self, groq_api_key, memora_api_url):
        """Test that async wrapper passes through when features disabled."""
        configure(
            memora_api_url=memora_api_url,
            agent_id="test-async-passthrough",
            inject_memories=False,
            store_conversations=False,
        )

        client = AsyncOpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'hello' and nothing else"}],
            max_tokens=10,
        )

        assert response is not None
        assert len(response.choices) > 0


class TestInterceptor:
    """Test interceptor functionality."""

    def test_extract_user_query_simple(self):
        """Test extracting user query from simple messages."""
        from memora_openai.interceptor import MemoraInterceptor

        interceptor = MemoraInterceptor()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
        ]

        query = interceptor._extract_user_query(messages)
        assert query == "What is Python?"

    def test_extract_user_query_structured(self):
        """Test extracting user query from structured content."""
        from memora_openai.interceptor import MemoraInterceptor

        interceptor = MemoraInterceptor()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://..."}},
                ],
            }
        ]

        query = interceptor._extract_user_query(messages)
        assert query == "What's in this image?"

    def test_extract_conversation_context(self):
        """Test extracting conversation context."""
        from memora_openai.interceptor import MemoraInterceptor

        interceptor = MemoraInterceptor()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"},
            {"role": "user", "content": "Tell me about AI"},
        ]

        context = interceptor._extract_conversation_context(messages)
        assert "user: Hello" in context
        assert "assistant: Hi! How can I help?" in context
        assert "user: Tell me about AI" in context

    def test_format_memories(self):
        """Test formatting memories."""
        from memora_openai.interceptor import MemoraInterceptor

        interceptor = MemoraInterceptor()
        memories = [
            {
                "text": "User likes Python",
                "event_date": "2024-01-01",
                "fact_type": "opinion",
            },
            {"text": "Working on AI project", "event_date": None, "fact_type": "world"},
        ]

        formatted = interceptor._format_memories(memories)
        assert "1. User likes Python" in formatted
        assert "2. Working on AI project" in formatted
        assert "Date: 2024-01-01" in formatted
