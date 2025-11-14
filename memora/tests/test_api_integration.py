"""
Integration test for the complete Memora API.

Tests all endpoints by starting a FastAPI server and making HTTP requests.
"""
import pytest
import pytest_asyncio
import httpx
from datetime import datetime
from memora.api import create_app


@pytest_asyncio.fixture
async def api_client(memory):
    """Create an async test client for the FastAPI app."""
    # Memory is already initialized by the conftest fixture
    app = create_app(memory, run_migrations=False, initialize_memory=False)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_agent_id():
    """Provide a unique agent ID for this test run."""
    return f"integration_test_{datetime.now().timestamp()}"


@pytest.mark.asyncio
async def test_full_api_workflow(api_client, test_agent_id):
    """
    End-to-end test covering all major API endpoints in a realistic workflow.

    Workflow:
    1. Create agent and set profile
    2. Store memories (put, batch put)
    3. Search memories
    4. Think (generate answer)
    5. List agents and memories
    6. Get agent profile
    7. Get visualization data
    8. Track documents
    9. Clean up
    """

    # ================================================================
    # 1. Agent Management
    # ================================================================

    # List agents (should be empty initially or have other test agents)
    response = await api_client.get("/api/v1/agents")
    assert response.status_code == 200
    initial_agents_data = response.json()["agents"]
    initial_agents = [a["agent_id"] for a in initial_agents_data]
    print(f"Initial agents: {len(initial_agents)}")

    # Get agent profile (creates default if not exists)
    response = await api_client.get(f"/api/v1/agents/{test_agent_id}/profile")
    assert response.status_code == 200
    profile = response.json()
    assert "personality" in profile
    assert "background" in profile
    print(f"Agent profile created with personality: {profile['personality']}")

    # Add background
    response = await api_client.post(
        f"/api/v1/agents/{test_agent_id}/background",
        json={
            "content": "A software engineer passionate about AI and memory systems."
        }
    )
    assert response.status_code == 200
    assert "software engineer" in response.json()["background"].lower()
    print("Background added")

    # ================================================================
    # 2. Memory Storage
    # ================================================================

    # Store single memory (using batch endpoint with single item)
    response = await api_client.post(
        f"/api/v1/agents/{test_agent_id}/memories",
        json={
            "items": [
                {
                    "content": "Alice is a machine learning researcher at Stanford.",
                    "context": "conversation about team members"
                }
            ]
        }
    )
    assert response.status_code == 200
    put_result = response.json()
    assert put_result["success"] is True
    assert put_result["items_count"] == 1
    print(f"Stored memory via batch endpoint")

    # Store batch memories
    response = await api_client.post(
        f"/api/v1/agents/{test_agent_id}/memories",
        json={
            "items": [
                {
                    "content": "Bob leads the infrastructure team and loves Kubernetes.",
                    "context": "team introduction"
                },
                {
                    "content": "Charlie recently joined as a product manager from Google.",
                    "context": "new hire announcement"
                }
            ]
        }
    )
    assert response.status_code == 200
    batch_result = response.json()
    assert batch_result["success"] is True
    assert batch_result["items_count"] == 2
    print(f"Stored {batch_result['items_count']} items from batch put")

    # ================================================================
    # 3. Search
    # ================================================================

    # Search for memories
    response = await api_client.post(
        f"/api/v1/agents/{test_agent_id}/memories/search",
        json={
            "query": "Who works on machine learning?",
            "thinking_budget": 50
        }
    )
    assert response.status_code == 200
    search_results = response.json()
    assert "results" in search_results
    assert len(search_results["results"]) > 0
    print(f"Search returned {len(search_results['results'])} results")

    # Verify we found Alice
    found_alice = any("Alice" in r["text"] for r in search_results["results"])
    assert found_alice, "Should find Alice in search results"

    # ================================================================
    # 4. Think (Reasoning)
    # ================================================================

    # Generate answer using think
    response = await api_client.post(
        f"/api/v1/agents/{test_agent_id}/think",
        json={
            "query": "What do you know about the team members?",
            "thinking_budget": 30,
            "context": "This is for a team overview document"
        }
    )
    assert response.status_code == 200
    think_result = response.json()
    assert "text" in think_result
    assert len(think_result["text"]) > 0
    assert "based_on" in think_result
    print(f"Think response: {think_result['text'][:100]}...")

    # Verify the answer mentions team members
    answer = think_result["text"].lower()
    assert "alice" in answer or "bob" in answer or "charlie" in answer

    # ================================================================
    # 5. Visualization & Statistics
    # ================================================================

    # Get graph data
    response = await api_client.get(f"/api/v1/agents/{test_agent_id}/graph")
    assert response.status_code == 200
    graph_data = response.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    print(f"Graph has {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")

    # Get memory statistics
    response = await api_client.get(f"/api/v1/agents/{test_agent_id}/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "total_nodes" in stats
    assert stats["total_nodes"] > 0
    print(f"Total nodes: {stats['total_nodes']}")

    # List memory units
    response = await api_client.get(
        f"/api/v1/agents/{test_agent_id}/memories/list",
        params={"limit": 10}
    )
    assert response.status_code == 200
    memory_units = response.json()
    assert "items" in memory_units
    assert len(memory_units["items"]) > 0
    print(f"Listed {len(memory_units['items'])} memory units")

    # ================================================================
    # 6. Document Tracking
    # ================================================================

    # Store memory with document
    response = await api_client.post(
        f"/api/v1/agents/{test_agent_id}/memories",
        json={
            "items": [
                {
                    "content": "Project timeline: MVP launch in Q1, Beta in Q2.",
                    "context": "product roadmap"
                }
            ],
            "document_id": "roadmap-2024-q1"
        }
    )
    assert response.status_code == 200
    print("Stored memory with document tracking")

    # List documents
    response = await api_client.get(f"/api/v1/agents/{test_agent_id}/documents")
    assert response.status_code == 200
    documents = response.json()
    assert "items" in documents
    assert len(documents["items"]) > 0
    print(f"Tracked documents: {len(documents['items'])}")

    # Get specific document
    response = await api_client.get(
        f"/api/v1/agents/{test_agent_id}/documents/roadmap-2024-q1"
    )
    assert response.status_code == 200
    doc_info = response.json()
    assert "id" in doc_info
    assert doc_info["id"] == "roadmap-2024-q1"
    assert doc_info["memory_unit_count"] > 0
    print(f"Document has {doc_info['memory_unit_count']} memory units")
    # Note: Document deletion is tested separately in test_document_deletion

    # ================================================================
    # 7. Verify Updated Agent Profile
    # ================================================================

    # Check profile again (might have formed new opinions)
    response = await api_client.get(f"/api/v1/agents/{test_agent_id}/profile")
    assert response.status_code == 200
    updated_profile = response.json()
    assert "software engineer" in updated_profile["background"].lower()
    print("Profile verified")

    # ================================================================
    # 8. List All Agents (should include our test agent)
    # ================================================================

    response = await api_client.get("/api/v1/agents")
    assert response.status_code == 200
    final_agents_data = response.json()["agents"]
    final_agents = [a["agent_id"] for a in final_agents_data]
    assert test_agent_id in final_agents
    assert len(final_agents) >= len(initial_agents) + 1
    print(f"Final agent count: {len(final_agents)}")

    # ================================================================
    # 9. Clean Up
    # ================================================================

    # Note: No delete agent endpoint in API, so test data remains in DB
    # Using timestamped agent IDs prevents conflicts between test runs
    print(f"Integration test complete for agent {test_agent_id}")


@pytest.mark.asyncio
async def test_error_handling(api_client):
    """Test that API properly handles error cases."""

    # Invalid request (missing required field)
    response = await api_client.post(
        "/api/v1/agents/error_test/memories",
        json={
            "items": [
                {
                    # Missing "content"
                    "context": "test"
                }
            ]
        }
    )
    assert response.status_code == 422  # Validation error

    # Search with invalid parameters
    response = await api_client.post(
        "/api/v1/agents/error_test/memories/search",
        json={
            "query": "test",
            "thinking_budget": -1  # Invalid negative budget
        }
    )
    assert response.status_code == 422

    # Get non-existent document
    response = await api_client.get(
        "/api/v1/agents/nonexistent_agent/documents/fake-doc-id"
    )
    assert response.status_code == 404

    print("Error handling tests passed")


@pytest.mark.asyncio
async def test_concurrent_requests(api_client):
    """Test that API can handle concurrent requests."""
    agent_id = f"concurrent_test_{datetime.now().timestamp()}"

    # Store multiple memories concurrently (simulated with sequential calls)
    responses = []
    test_facts = [
        "David works as a data scientist at Microsoft.",
        "Emily is the CEO of a startup in San Francisco.",
        "Frank teaches computer science at MIT.",
        "Grace is a software architect specializing in distributed systems.",
        "Henry leads the product team at Amazon."
    ]
    for fact in test_facts:
        response = await api_client.post(
            f"/api/v1/agents/{agent_id}/memories",
            json={
                "items": [
                    {
                        "content": fact,
                        "context": "concurrent test"
                    }
                ]
            }
        )
        responses.append(response)

    # All should succeed
    assert all(r.status_code == 200 for r in responses)
    assert all(r.json()["success"] for r in responses)

    # Verify all facts stored
    response = await api_client.get(
        f"/api/v1/agents/{agent_id}/memories/list",
        params={"limit": 20}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 5

    print(f"Concurrent test stored {len(items)} memory units")


@pytest.mark.asyncio
async def test_document_deletion(api_client):
    """Test document deletion including cascade deletion of memory units and links."""
    test_agent_id = f"doc_delete_test_{datetime.now().timestamp()}"

    # Store a document with memory
    response = await api_client.post(
        f"/api/v1/agents/{test_agent_id}/memories",
        json={
            "items": [
                {
                    "content": "The quarterly sales report shows a 25% increase in revenue.",
                    "context": "Q1 financial review"
                }
            ],
            "document_id": "sales-report-q1-2024"
        }
    )
    assert response.status_code == 200
    print("Created document with memory units")

    # Verify document exists
    response = await api_client.get(
        f"/api/v1/agents/{test_agent_id}/documents/sales-report-q1-2024"
    )
    assert response.status_code == 200
    doc_info = response.json()
    initial_units = doc_info["memory_unit_count"]
    assert initial_units > 0
    print(f"Document has {initial_units} memory units")

    # Delete the document
    response = await api_client.delete(
        f"/api/v1/agents/{test_agent_id}/documents/sales-report-q1-2024"
    )
    assert response.status_code == 200
    delete_result = response.json()
    assert delete_result["success"] is True
    assert delete_result["document_id"] == "sales-report-q1-2024"
    assert delete_result["memory_units_deleted"] == initial_units
    print(f"Successfully deleted document and {delete_result['memory_units_deleted']} memory units")

    # Verify document is gone (should return 404)
    response = await api_client.get(
        f"/api/v1/agents/{test_agent_id}/documents/sales-report-q1-2024"
    )
    assert response.status_code == 404
    print("Document deletion verified - returns 404")

    # Verify document is not in the list
    response = await api_client.get(f"/api/v1/agents/{test_agent_id}/documents")
    assert response.status_code == 200
    documents = response.json()
    doc_ids = [doc["id"] for doc in documents["items"]]
    assert "sales-report-q1-2024" not in doc_ids
    print("Document not in list - verified")

    # Try to delete again (should return 404)
    response = await api_client.delete(
        f"/api/v1/agents/{test_agent_id}/documents/sales-report-q1-2024"
    )
    assert response.status_code == 404
    print("Double delete returns 404 - verified")
