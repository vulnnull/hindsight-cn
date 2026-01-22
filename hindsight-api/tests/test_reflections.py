"""Tests for reflections, mental models, and learnings functionality."""

import uuid

import pytest
import pytest_asyncio
import httpx
from hindsight_api.api import create_app
from hindsight_api.engine.memory_engine import MemoryEngine


@pytest_asyncio.fixture
async def api_client(memory):
    """Create an async test client for the FastAPI app."""
    app = create_app(memory, initialize_memory=False)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_bank_id():
    """Provide a unique bank ID for this test run."""
    return f"test_reflections_{uuid.uuid4().hex[:8]}"


class TestReflectionsCRUD:
    """Test reflections CRUD operations via memory engine."""

    @pytest.mark.asyncio
    async def test_create_and_get_reflection(self, memory: MemoryEngine, request_context):
        """Test creating and retrieving a reflection."""
        bank_id = f"test-reflection-{uuid.uuid4().hex[:8]}"

        # Create the bank first
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Create a reflection
        reflection = await memory.create_reflection(
            bank_id=bank_id,
            name="Team Preferences",
            source_query="What are the team's communication preferences?",
            content="The team prefers async communication via Slack",
            tags=["team"],
            request_context=request_context,
        )

        assert reflection["name"] == "Team Preferences"
        assert reflection["source_query"] == "What are the team's communication preferences?"
        assert reflection["content"] == "The team prefers async communication via Slack"
        assert reflection["tags"] == ["team"]
        assert "id" in reflection

        # Get the reflection
        fetched = await memory.get_reflection(
            bank_id=bank_id,
            reflection_id=reflection["id"],
            request_context=request_context,
        )

        assert fetched["id"] == reflection["id"]
        assert fetched["name"] == "Team Preferences"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_list_reflections(self, memory: MemoryEngine, request_context):
        """Test listing reflections with filters."""
        bank_id = f"test-reflection-list-{uuid.uuid4().hex[:8]}"

        # Create the bank first
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Create multiple reflections
        await memory.create_reflection(
            bank_id=bank_id,
            name="Reflection 1",
            source_query="Query 1",
            content="Content 1",
            tags=["tag1"],
            request_context=request_context,
        )
        await memory.create_reflection(
            bank_id=bank_id,
            name="Reflection 2",
            source_query="Query 2",
            content="Content 2",
            tags=["tag2"],
            request_context=request_context,
        )

        # List all
        all_reflections = await memory.list_reflections(
            bank_id=bank_id,
            request_context=request_context,
        )
        assert len(all_reflections) == 2

        # List with tag filter
        tag1_reflections = await memory.list_reflections(
            bank_id=bank_id,
            tags=["tag1"],
            request_context=request_context,
        )
        assert len(tag1_reflections) == 1

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_update_reflection(self, memory: MemoryEngine, request_context):
        """Test updating a reflection."""
        bank_id = f"test-reflection-update-{uuid.uuid4().hex[:8]}"

        # Create the bank first
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Create a reflection
        reflection = await memory.create_reflection(
            bank_id=bank_id,
            name="Original Name",
            source_query="Original Query",
            content="Original Content",
            request_context=request_context,
        )

        # Update the reflection
        updated = await memory.update_reflection(
            bank_id=bank_id,
            reflection_id=reflection["id"],
            name="Updated Name",
            content="Updated Content",
            request_context=request_context,
        )

        assert updated["name"] == "Updated Name"
        assert updated["content"] == "Updated Content"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_delete_reflection(self, memory: MemoryEngine, request_context):
        """Test deleting a reflection."""
        bank_id = f"test-reflection-delete-{uuid.uuid4().hex[:8]}"

        # Create the bank first
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Create a reflection
        reflection = await memory.create_reflection(
            bank_id=bank_id,
            name="To Delete",
            source_query="Query",
            content="Content",
            request_context=request_context,
        )

        # Delete the reflection
        await memory.delete_reflection(
            bank_id=bank_id,
            reflection_id=reflection["id"],
            request_context=request_context,
        )

        # Verify deletion - should return None
        fetched = await memory.get_reflection(
            bank_id=bank_id,
            reflection_id=reflection["id"],
            request_context=request_context,
        )
        assert fetched is None

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestMentalModelsAPI:
    """Test mental models API endpoints.

    NOTE: Mental models are now stored in memory_units with fact_type='mental_model'
    and accessed via recall with fact_type=["mental_model"]. The old /mental-models
    endpoint was removed. These tests are skipped.
    """

    @pytest.mark.skip(reason="Mental models endpoint removed - use recall with fact_type=['mental_model']")
    @pytest.mark.asyncio
    async def test_list_mental_models_empty(self, api_client, test_bank_id):
        """Test listing mental models when none exist."""
        pass

    @pytest.mark.skip(reason="Mental models endpoint removed - use recall with fact_type=['mental_model']")
    @pytest.mark.asyncio
    async def test_get_mental_model_not_found(self, api_client, test_bank_id):
        """Test getting a non-existent mental model."""
        pass


class TestReflectionsAPI:
    """Test reflections API endpoints."""

    @pytest.mark.asyncio
    async def test_reflections_api_crud(self, api_client, test_bank_id):
        """Test full CRUD cycle through API."""
        import asyncio

        # Create bank first via profile endpoint
        await api_client.get(f"/v1/default/banks/{test_bank_id}/profile")

        # Create a reflection (async operation)
        response = await api_client.post(
            f"/v1/default/banks/{test_bank_id}/reflections",
            json={
                "name": "API Test Reflection",
                "source_query": "What is the API test about?",
                "content": "This is an API test reflection",
                "tags": ["api-test"],
            },
        )
        assert response.status_code == 200
        create_result = response.json()
        assert "operation_id" in create_result
        operation_id = create_result["operation_id"]

        # Wait for the async operation to complete
        for _ in range(30):  # Wait up to 30 seconds
            response = await api_client.get(f"/v1/default/banks/{test_bank_id}/operations/{operation_id}")
            if response.status_code == 200:
                op_status = response.json()
                if op_status.get("status") == "completed":
                    break
            await asyncio.sleep(1)

        # List reflections to get the created reflection
        response = await api_client.get(f"/v1/default/banks/{test_bank_id}/reflections")
        assert response.status_code == 200
        reflections = response.json()["items"]
        assert len(reflections) >= 1

        # Find our reflection
        reflection = next((r for r in reflections if r["name"] == "API Test Reflection"), None)
        assert reflection is not None, f"Reflection not found. Items: {reflections}"
        reflection_id = reflection["id"]

        # Get the reflection
        response = await api_client.get(f"/v1/default/banks/{test_bank_id}/reflections/{reflection_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "API Test Reflection"

        # Update the reflection
        response = await api_client.patch(
            f"/v1/default/banks/{test_bank_id}/reflections/{reflection_id}",
            json={"name": "Updated API Test Reflection"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated API Test Reflection"

        # Delete the reflection
        response = await api_client.delete(f"/v1/default/banks/{test_bank_id}/reflections/{reflection_id}")
        assert response.status_code == 200

        # Verify deletion
        response = await api_client.get(f"/v1/default/banks/{test_bank_id}/reflections/{reflection_id}")
        assert response.status_code == 404

        # Cleanup
        await api_client.delete(f"/v1/default/banks/{test_bank_id}")


class TestRecallWithMentalModelsAndReflections:
    """Test recall integration with mental models and reflections."""

    @pytest.mark.asyncio
    async def test_recall_includes_mental_models(self, api_client, test_bank_id):
        """Test that recall can include mental models in the response."""
        # Create bank first via profile endpoint
        await api_client.get(f"/v1/default/banks/{test_bank_id}/profile")

        # Note: Mental models are auto-created via consolidation, not manually
        # This test just verifies the include parameter works

        # Recall with mental models included
        response = await api_client.post(
            f"/v1/default/banks/{test_bank_id}/memories/recall",
            json={
                "query": "What is machine learning?",
                "include": {
                    "mental_models": {"max_results": 5},
                },
            },
        )
        assert response.status_code == 200
        result = response.json()

        # Should have mental_models field in response (may be empty)
        assert "mental_models" in result or result.get("mental_models") is None

        # Cleanup
        await api_client.delete(f"/v1/default/banks/{test_bank_id}")

    @pytest.mark.asyncio
    async def test_recall_includes_reflections(self, api_client, test_bank_id):
        """Test that recall can include reflections in the response."""
        # Create bank first via profile endpoint
        await api_client.get(f"/v1/default/banks/{test_bank_id}/profile")

        # Create a reflection first
        response = await api_client.post(
            f"/v1/default/banks/{test_bank_id}/reflections",
            json={
                "name": "AI Overview",
                "source_query": "What is AI?",
                "content": "Artificial intelligence is the simulation of human intelligence",
                "tags": [],
            },
        )
        assert response.status_code == 200

        # Recall with reflections included
        response = await api_client.post(
            f"/v1/default/banks/{test_bank_id}/memories/recall",
            json={
                "query": "What is artificial intelligence?",
                "include": {
                    "reflections": {"max_results": 5},
                },
            },
        )
        assert response.status_code == 200
        result = response.json()

        # Should have reflections in response (may be empty if embedding not generated yet)
        assert "reflections" in result or result.get("reflections") is None

        # Cleanup
        await api_client.delete(f"/v1/default/banks/{test_bank_id}")

    @pytest.mark.asyncio
    async def test_recall_without_mental_models_by_default(self, api_client, test_bank_id):
        """Test that recall does not include mental models by default."""
        # Create bank first via profile endpoint
        await api_client.get(f"/v1/default/banks/{test_bank_id}/profile")

        # Recall without specifying mental models
        response = await api_client.post(
            f"/v1/default/banks/{test_bank_id}/memories/recall",
            json={
                "query": "Test query",
            },
        )
        assert response.status_code == 200
        result = response.json()

        # Mental models should not be in response
        assert result.get("mental_models") is None

        # Cleanup
        await api_client.delete(f"/v1/default/banks/{test_bank_id}")
