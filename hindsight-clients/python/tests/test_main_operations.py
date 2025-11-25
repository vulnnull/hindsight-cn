"""

These tests require a running Hindsight API server.
"""

import os
import pytest
from datetime import datetime
from hindsight_client import Hindsight


# Test configuration
HINDSIGHT_API_URL = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")
TEST_AGENT_ID = "test_agent_" + datetime.now().strftime("%Y%m%d_%H%M%S")


@pytest.fixture
def client():
    """Create a Hindsight client for testing."""
    with Hindsight(base_url=HINDSIGHT_API_URL) as client:
        yield client


@pytest.fixture
def agent_id():
    """Provide a unique test agent ID."""
    return TEST_AGENT_ID


class TestStore:
    """Tests for storing memories."""

    def test_put_single_memory(self, client, agent_id):
        """Test storing a single memory."""
        response = client.put(
            agent_id=agent_id,
            content="Alice loves artificial intelligence and machine learning",
        )

        assert response is not None
        assert response.get("success") is True
        assert response.get("items_count") == 1

    def test_put_memory_with_context(self, client, agent_id):
        """Test storing a memory with context and event date."""
        response = client.put(
            agent_id=agent_id,
            content="Bob went hiking in the mountains",
            event_date=datetime(2024, 1, 15, 10, 30),
            context="outdoor activities",
        )

        assert response is not None
        assert response.get("success") is True

    def test_put_batch_memories(self, client, agent_id):
        """Test storing multiple memories in batch."""
        items = [
            {"content": "Charlie enjoys reading science fiction books"},
            {"content": "Diana is learning to play the guitar", "context": "hobbies"},
            {
                "content": "Eve completed a marathon last month",
                "event_date": datetime(2024, 10, 15),
            },
        ]

        response = client.put_batch(
            agent_id=agent_id,
            items=items,
        )

        assert response is not None
        assert response.get("success") is True
        assert response.get("items_count") == 3


class TestSearch:
    """Tests for searching memories."""

    @pytest.fixture(autouse=True)
    def setup_memories(self, client, agent_id):
        """Setup: Store some test memories before search tests."""
        client.put_batch(
            agent_id=agent_id,
            items=[
                {"content": "Alice loves programming in Python"},
                {"content": "Bob enjoys hiking and outdoor adventures"},
                {"content": "Charlie is interested in quantum physics"},
                {"content": "Diana plays the violin beautifully"},
            ],
        )

    def test_search_basic(self, client, agent_id):
        """Test basic memory search."""
        results = client.search(
            agent_id=agent_id,
            query="What does Alice like?",
        )

        assert results is not None
        assert len(results) > 0

        # Check that at least one result contains relevant information
        result_texts = [r.get("text", "") for r in results]
        assert any("Alice" in text or "Python" in text or "programming" in text for text in result_texts)

    def test_search_with_max_tokens(self, client, agent_id):
        """Test search with token limit."""
        results = client.search(
            agent_id=agent_id,
            query="outdoor activities",
            max_tokens=1024,
        )

        assert results is not None
        assert isinstance(results, list)

    def test_search_full_featured(self, client, agent_id):
        """Test search_memories with all features."""
        response = client.search_memories(
            agent_id=agent_id,
            query="What are people's hobbies?",
            fact_type=["world"],
            max_tokens=2048,
            trace=True,
        )

        assert response is not None
        assert "results" in response
        # Trace should be included when enabled
        if response.get("trace"):
            assert isinstance(response["trace"], dict)


class TestThink:
    """Tests for thinking/reasoning operations."""

    @pytest.fixture(autouse=True)
    def setup_memories(self, client, agent_id):
        """Setup: Store some test memories and agent background."""
        client.create_agent(
            agent_id=agent_id,
            name="Test Agent",
            background="I am a helpful AI assistant interested in technology and science.",
        )

        client.put_batch(
            agent_id=agent_id,
            items=[
                {"content": "The Python programming language is great for data science"},
                {"content": "Machine learning models can recognize patterns in data"},
                {"content": "Neural networks are inspired by biological neurons"},
            ],
        )

    def test_think_basic(self, client, agent_id):
        """Test basic think operation."""
        response = client.think(
            agent_id=agent_id,
            query="What do you think about artificial intelligence?",
        )

        assert response is not None
        assert "text" in response
        assert len(response["text"]) > 0

        # Should include facts that were used
        if "based_on" in response:
            assert isinstance(response["based_on"], list)

    def test_think_with_context(self, client, agent_id):
        """Test think with additional context."""
        response = client.think(
            agent_id=agent_id,
            query="Should I learn Python?",
            context="I'm interested in starting a career in data science",
            thinking_budget=100,
        )

        assert response is not None
        assert "text" in response
        assert len(response["text"]) > 0


class TestListMemories:
    """Tests for listing memories."""

    @pytest.fixture(autouse=True)
    def setup_memories(self, client, agent_id):
        """Setup: Store some test memories."""
        client.put_batch(
            agent_id=agent_id,
            items=[
                {"content": f"Test memory {i}"} for i in range(5)
            ],
        )

    def test_list_all_memories(self, client, agent_id):
        """Test listing all memories."""
        response = client.list_memories(agent_id=agent_id)

        assert response is not None
        assert "items" in response
        assert "total" in response
        assert len(response["items"]) > 0

    def test_list_with_pagination(self, client, agent_id):
        """Test listing with pagination."""
        response = client.list_memories(
            agent_id=agent_id,
            limit=2,
            offset=0,
        )

        assert response is not None
        assert "items" in response
        assert len(response["items"]) <= 2


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_complete_workflow(self, client):
        """Test a complete workflow: create agent, store, search, think."""
        workflow_agent_id = "workflow_test_" + datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Create agent
        client.create_agent(
            agent_id=workflow_agent_id,
            name="Alice",
            background="I am a software engineer who loves Python programming.",
        )

        # 2. Store memories
        store_response = client.put_batch(
            agent_id=workflow_agent_id,
            items=[
                {"content": "I completed a project using FastAPI"},
                {"content": "I learned about async programming in Python"},
                {"content": "I enjoy working on open source projects"},
            ],
        )
        assert store_response.get("success") is True

        # 3. Search for relevant memories
        search_results = client.search(
            agent_id=workflow_agent_id,
            query="What programming technologies do I use?",
        )
        assert len(search_results) > 0

        # 4. Generate contextual answer
        think_response = client.think(
            agent_id=workflow_agent_id,
            query="What are my professional interests?",
        )
        assert "text" in think_response
        assert len(think_response["text"]) > 0
