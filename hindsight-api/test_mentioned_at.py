"""Test to verify mentioned_at uses event_date, not now()"""
import asyncio
from datetime import datetime, timezone, timedelta
from hindsight_api.engine.memory_engine import MemoryEngine

async def test_mentioned_at_uses_event_date():
    """Verify that mentioned_at is set to event_date, not now()"""

    # Use a date that's clearly not "now"
    past_date = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    memory = MemoryEngine()
    await memory.initialize()

    try:
        bank_id = "test_mentioned_at_debug"

        # Store with explicit past event_date
        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content="Alex went to the store.",
            context="test",
            event_date=past_date
        )

        print(f"\n✅ Stored {len(unit_ids)} units")

        # Recall and check mentioned_at
        result = await memory.recall_async(
            bank_id=bank_id,
            query="store",
            max_tokens=500
        )

        print(f"✅ Found {len(result.results)} facts")

        for i, fact in enumerate(result.results, 1):
            print(f"\nFact {i}:")
            print(f"  Text: {fact.text[:80]}...")
            print(f"  mentioned_at: {fact.mentioned_at}")
            print(f"  occurred_start: {fact.occurred_start}")

            # Parse mentioned_at
            if isinstance(fact.mentioned_at, str):
                mentioned_dt = datetime.fromisoformat(fact.mentioned_at.replace('Z', '+00:00'))
            else:
                mentioned_dt = fact.mentioned_at

            # Check if mentioned_at matches our event_date
            time_diff = abs((mentioned_dt - past_date).total_seconds())

            if time_diff < 60:
                print(f"  ✅ mentioned_at correctly set to event_date")
            else:
                print(f"  ❌ mentioned_at is {mentioned_dt}, expected {past_date}")
                print(f"     Time difference: {time_diff} seconds")

                # Check if it's close to now()
                now_diff = abs((mentioned_dt - datetime.now(timezone.utc)).total_seconds())
                if now_diff < 60:
                    print(f"     ⚠️  mentioned_at is using now() instead of event_date!")

        await memory.delete_bank(bank_id)

    finally:
        await memory.close()

if __name__ == "__main__":
    asyncio.run(test_mentioned_at_uses_event_date())
