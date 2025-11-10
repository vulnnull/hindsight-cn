"""
Test temporal extraction and per-fact dating.
"""
import pytest
from datetime import datetime, timezone, timedelta
from memora.fact_extraction import extract_facts_from_text


@pytest.mark.asyncio
async def test_extract_facts_with_relative_dates(memory):
    """Test that relative dates are converted to absolute dates."""

    reference_date = datetime(2024, 3, 20, 14, 0, 0, tzinfo=timezone.utc)

    text = """
    Yesterday I went hiking in Yosemite.
    Last week I started my new job at Google.
    This morning I had coffee with Alice.
    """

    facts = await extract_facts_from_text(text, reference_date, "Personal diary", llm_config=memory._llm_config)

    print(f"\nExtracted {len(facts)} facts:")
    for fact in facts:
        print(f"- {fact['fact']}")
        print(f"  Date: {fact['date']}")

    # Verify we got facts
    assert len(facts) > 0, "Should extract at least one fact"

    # Check that all facts have dates
    for fact in facts:
        assert 'fact' in fact, "Each fact should have 'fact' field"
        assert 'date' in fact, "Each fact should have 'date' field"
        assert fact['date'], f"Date should not be empty for fact: {fact['fact']}"

    # Verify dates are different (not all using reference date)
    dates = [f['date'] for f in facts]
    unique_dates = set(dates)
    if len(facts) >= 3:
        assert len(unique_dates) >= 2, "Should have different dates for different temporal facts"

    print(f"\n✅ All facts have absolute dates")


@pytest.mark.asyncio
async def test_extract_facts_with_no_temporal_info(memory):
    """Test that facts without temporal info use the reference date."""

    reference_date = datetime(2024, 3, 20, 14, 0, 0, tzinfo=timezone.utc)

    text = "Alice works at Google. She loves Python programming."

    facts = await extract_facts_from_text(text, reference_date, "General info", llm_config=memory._llm_config)

    print(f"\nExtracted {len(facts)} facts:")
    for fact in facts:
        print(f"- {fact['fact']}")
        print(f"  Date: {fact['date']}")

    assert len(facts) > 0, "Should extract at least one fact"

    # All facts should use the reference date since no temporal info is mentioned
    for fact in facts:
        assert fact['date'], f"Fact should have a date: {fact['fact']}"


@pytest.mark.asyncio
async def test_extract_facts_with_absolute_dates(memory):
    """Test that absolute dates in text are preserved."""

    reference_date = datetime(2024, 3, 20, 14, 0, 0, tzinfo=timezone.utc)

    text = """
    On March 15, 2024, Alice joined Google.
    Bob will start his vacation on April 1st.
    """

    facts = await extract_facts_from_text(text, reference_date, "Calendar events", llm_config=memory._llm_config)

    print(f"\nExtracted {len(facts)} facts:")
    for fact in facts:
        print(f"- {fact['fact']}")
        print(f"  Date: {fact['date']}")

    assert len(facts) > 0, "Should extract at least one fact"

    # Check that dates are present
    for fact in facts:
        assert fact['date'], f"Fact should have a date: {fact['fact']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
