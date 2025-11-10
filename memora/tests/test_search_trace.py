"""
Test search tracing functionality.
"""
import pytest
from memora.search_trace import SearchTrace
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_search_with_trace(memory):
    """Test that search with enable_trace=True returns a valid SearchTrace."""
    # Generate a unique agent ID for this test
    agent_id = f"test_trace_{datetime.now(timezone.utc).timestamp()}"

    try:

        # Store some test memories
        await memory.put_async(
            agent_id=agent_id,
            content="Alice works at Google in Mountain View",
            context="test context",
        )
        await memory.put_async(
            agent_id=agent_id,
            content="Bob also works at Google but in New York",
            context="test context",
        )
        await memory.put_async(
            agent_id=agent_id,
            content="Charlie founded a startup called TechCorp",
            context="test context",
        )

        # Search with tracing enabled
        results, trace = await memory.search_async(
            agent_id=agent_id,
            query="Who works at Google?",
            fact_type=["world"],
            thinking_budget=20,
            max_tokens=512,
            enable_trace=True,
        )

        # Verify results
        assert len(results) > 0, "Should have search results"

        # Verify trace object
        assert trace is not None, "Trace should not be None when enable_trace=True"
        assert isinstance(trace, SearchTrace), "Trace should be SearchTrace instance"

        # Verify query info
        assert trace.query.query_text == "Who works at Google?"
        assert trace.query.thinking_budget == 20
        assert trace.query.max_tokens == 512
        assert len(trace.query.query_embedding) > 0, "Query embedding should be populated"

        # Verify entry points
        assert len(trace.entry_points) > 0, "Should have entry points"
        for ep in trace.entry_points:
            assert ep.node_id, "Entry point should have node_id"
            assert ep.text, "Entry point should have text"
            assert 0.0 <= ep.similarity_score <= 1.0, "Similarity should be in [0, 1]"

        # Verify visits
        assert len(trace.visits) > 0, "Should have visited nodes"
        for visit in trace.visits:
            assert visit.node_id, "Visit should have node_id"
            assert visit.text, "Visit should have text"
            assert visit.weights.final_weight >= 0, "Weight should be non-negative"
            # Entry points should have no parent
            if visit.is_entry_point:
                assert visit.parent_node_id is None
                assert visit.link_type is None
            else:
                # Non-entry points should have parent info (unless they're isolated)
                # But we allow None parent if the node was reached differently
                pass

        # Verify summary
        assert trace.summary.total_nodes_visited == len(trace.visits)
        assert trace.summary.results_returned == len(results)
        assert trace.summary.budget_used <= trace.query.thinking_budget
        assert trace.summary.total_duration_seconds > 0

        # Verify phase metrics
        assert len(trace.summary.phase_metrics) > 0, "Should have phase metrics"
        phase_names = {pm.phase_name for pm in trace.summary.phase_metrics}
        assert "generate_query_embedding" in phase_names
        assert "parallel_retrieval" in phase_names  # New modular architecture
        assert "rrf_merge" in phase_names  # New modular architecture
        assert "reranking" in phase_names  # New modular architecture

        # Test JSON export
        json_str = trace.to_json()
        assert json_str, "Should be able to export to JSON"
        assert "query" in json_str
        assert "visits" in json_str
        assert "summary" in json_str

        # Test dict export
        trace_dict = trace.to_dict()
        assert isinstance(trace_dict, dict)
        assert "query" in trace_dict
        assert "visits" in trace_dict

        # Test helper methods
        if len(trace.visits) > 0:
            first_visit = trace.visits[0]
            found_visit = trace.get_visit_by_node_id(first_visit.node_id)
            assert found_visit is not None
            assert found_visit.node_id == first_visit.node_id

        # Test get_entry_point_nodes
        entry_point_visits = trace.get_entry_point_nodes()
        assert len(entry_point_visits) > 0
        for epv in entry_point_visits:
            assert epv.is_entry_point

        print("\n✓ Search trace test passed!")
        print(f"  - Query: {trace.query.query_text}")
        print(f"  - Entry points: {len(trace.entry_points)}")
        print(f"  - Nodes visited: {trace.summary.total_nodes_visited}")
        print(f"  - Nodes pruned: {trace.summary.total_nodes_pruned}")
        print(f"  - Results returned: {trace.summary.results_returned}")
        print(f"  - Duration: {trace.summary.total_duration_seconds:.3f}s")

    finally:
        # Cleanup
        await memory.delete_agent(agent_id)


@pytest.mark.asyncio
async def test_search_without_trace(memory):
    """Test that search with enable_trace=False returns None for trace."""
    agent_id = f"test_no_trace_{datetime.now(timezone.utc).timestamp()}"

    try:

        # Store a test memory
        await memory.put_async(
            agent_id=agent_id,
            content="Test memory without trace",
            context="test",
        )

        # Search without tracing
        results, trace = await memory.search_async(
            agent_id=agent_id,
            query="test",
            fact_type=["world"],
            thinking_budget=10,
            max_tokens=512,
            enable_trace=False,
        )

        # Verify trace is None
        assert trace is None, "Trace should be None when enable_trace=False"
        assert isinstance(results, list), "Results should still be a list"

        print("\n✓ Search without trace test passed!")

    finally:
        # Cleanup
        await memory.delete_agent(agent_id)
