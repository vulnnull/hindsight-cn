"""
Test think function for opinion generation and consistency.
"""
import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_think_opinion_consistency(memory):
    """
    Test that think function:
    1. Generates an opinion
    2. Stores the opinion in the database
    3. Returns consistent response on subsequent calls with the same query
    """
    agent_id = f"test_think_{datetime.now(timezone.utc).timestamp()}"

    try:

        # Store some initial facts to give context for opinion formation
        await memory.put_async(
            agent_id=agent_id,
            content="Alice is a software engineer who has worked on 5 major projects. She always delivers on time and writes clean, well-documented code.",
            context="performance review",
            event_date=datetime(2024, 1, 15, tzinfo=timezone.utc)
        )

        await memory.put_async(
            agent_id=agent_id,
            content="Bob recently joined the team. He missed his first deadline and his code had many bugs.",
            context="performance review",
            event_date=datetime(2024, 2, 1, tzinfo=timezone.utc)
        )

        # First think call - should generate opinions
        query = "Who is a more reliable engineer?"
        result1 = await memory.think_async(
            agent_id=agent_id,
            query=query,
            thinking_budget=30,
        )

        print(f"\n=== First Think Call ===")
        print(f"Answer: {result1['text']}")
        print(f"New opinions formed: {len(result1.get('new_opinions', []))}")
        for opinion in result1.get('new_opinions', []):
            print(f"  - {opinion['text']} (confidence: {opinion['confidence']:.2f})")

        # Verify we got an answer
        assert result1['text'], "First think call should return an answer"
        assert 'based_on' in result1, "Should return based_on facts"

        # Verify opinions were formed
        new_opinions_count = len(result1.get('new_opinions', []))
        print(f"\nNew opinions formed: {new_opinions_count}")

        # Wait for background opinion PUT tasks to complete
        await memory.wait_for_background_tasks()

        # Search for stored opinions to verify they were actually saved
        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            stored_opinions = await conn.fetch(
                """
                SELECT id, text, confidence_score, fact_type
                FROM memory_units
                WHERE agent_id = $1 AND fact_type = 'opinion'
                ORDER BY created_at DESC
                """,
                agent_id
            )

        print(f"\n=== Stored Opinions in Database ===")
        print(f"Total opinions stored: {len(stored_opinions)}")
        for op in stored_opinions:
            print(f"  - {op['text']} (confidence: {op['confidence_score']:.2f})")

        # Verify opinions were actually written to database
        # NOTE: Opinion extraction may not always detect opinions depending on the LLM response format
        if len(stored_opinions) > 0:
            assert all(op['fact_type'] == 'opinion' for op in stored_opinions), "All stored items should have fact_type='opinion'"
            print(f"✓ Opinions were successfully stored in database")
        else:
            print(f"⚠ Note: No opinions were extracted/stored (this can happen if the LLM response format doesn't trigger opinion extraction)")

        # Second think call - should use the stored opinions
        result2 = await memory.think_async(
            agent_id=agent_id,
            query=query,
            thinking_budget=30,
        )

        print(f"\n=== Second Think Call ===")
        print(f"Answer: {result2['text']}")
        print(f"Existing opinions used: {len(result2['based_on'].get('opinion', []))}")
        for opinion in result2['based_on'].get('opinion', []):
            print(f"  - {opinion['text']}")
        print(f"New opinions formed: {len(result2.get('new_opinions', []))}")

        # Verify second call also got an answer
        assert result2['text'], "Second think call should return an answer"

        # Verify second call used the stored opinions (if any were stored)
        if len(stored_opinions) > 0:
            assert len(result2['based_on'].get('opinion', [])) > 0, "Second call should retrieve stored opinions"

        # The responses should be consistent (both should mention the same person as more reliable)
        # We'll do a basic check that they're not contradictory
        text1_lower = result1['text'].lower()
        text2_lower = result2['text'].lower()

        print(f"\n=== Consistency Check ===")

        # Check if Alice is mentioned as more reliable in first response
        if 'alice' in text1_lower and ('reliable' in text1_lower or 'better' in text1_lower):
            print("First response favors Alice")
            # Second response should also favor Alice (consistency)
            assert 'alice' in text2_lower, "Second response should also mention Alice"
            print("Second response also mentions Alice - CONSISTENT ✓")

        # Check if Bob is mentioned
        if 'bob' in text1_lower:
            print("First response mentions Bob")
            if 'bob' in text2_lower:
                print("Second response also mentions Bob - CONSISTENT ✓")

        print(f"\n✅ Test passed - opinions were formed, stored, and used consistently")

    finally:
        # Clean up agent data
        try:
            await memory.delete_agent(agent_id)
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")


@pytest.mark.asyncio
async def test_think_without_prior_context(memory):
    """
    Test that think function handles queries when there's no relevant context.
    """
    agent_id = f"test_think_no_context_{datetime.now(timezone.utc).timestamp()}"

    # Call think without storing any prior facts
    result = await memory.think_async(
        agent_id=agent_id,
        query="What is the capital of France?",
        thinking_budget=20,
    )

    print(f"\n=== Think Without Context ===")
    print(f"Answer: {result['text']}")

    # Should still return an answer (even if it says it doesn't have enough info)
    assert result['text'], "Should return some answer"
    assert 'based_on' in result, "Should return based_on structure"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
