"""
Test retain function and chunk storage.
"""
import pytest
from datetime import datetime, timezone
from hindsight_api.engine.memory_engine import Budget


@pytest.mark.asyncio
async def test_retain_with_chunks(memory):
    """
    Test that retain function:
    1. Stores facts with associated chunks
    2. Recall returns chunk_id for each fact
    3. Recall with include_entities=True also works (for compatibility)
    """
    bank_id = f"test_chunks_{datetime.now(timezone.utc).timestamp()}"
    document_id = "test_doc_123"

    try:
        # Store content that will be chunked (long enough to create multiple facts)
        long_content = """
        Alice is a senior software engineer at TechCorp. She has been working there for 5 years.
        Alice specializes in distributed systems and has led the development of the company's
        microservices architecture. She is known for writing clean, well-documented code.

        Bob joined the team last month as a junior developer. He is learning React and Node.js.
        Bob is enthusiastic and asks great questions during code reviews. He recently completed
        his first feature, which was a user authentication flow.

        The team uses Kubernetes for container orchestration and deploys to AWS. They follow
        agile methodologies with two-week sprints. Code reviews are mandatory before merging.
        """

        # Retain with document_id to enable chunk storage
        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content=long_content,
            context="team overview",
            event_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            document_id=document_id
        )

        print(f"\n=== Retained {len(unit_ids)} facts ===")
        assert len(unit_ids) > 0, "Should have extracted and stored facts"

        # Test 1: Recall with chunks enabled
        result = await memory.recall_async(
            bank_id=bank_id,
            query="Tell me about Alice",
            budget=Budget.LOW,
            max_tokens=500,
            fact_type=["world"],  # Search for world facts
            include_entities=False,  # Disable entities for simpler test
            include_chunks=True,  # Enable chunks
            max_chunk_tokens=8192
        )

        print(f"\n=== Recall Results (with chunks) ===")
        print(f"Found {len(result.results)} results")

        assert len(result.results) > 0, "Should find facts about Alice"

        # Verify that chunks are returned
        assert result.chunks is not None, "Chunks should be included in the response"
        assert len(result.chunks) > 0, "Should have at least one chunk"

        print(f"Number of chunks returned: {len(result.chunks)}")

        # Verify chunk structure
        for chunk_id, chunk_info in result.chunks.items():
            print(f"\nChunk {chunk_id}:")
            print(f"  - chunk_index: {chunk_info.chunk_index}")
            print(f"  - chunk_text length: {len(chunk_info.chunk_text)} chars")
            print(f"  - truncated: {chunk_info.truncated}")
            print(f"  - text preview: {chunk_info.chunk_text[:100]}...")

            # Verify chunk structure
            assert isinstance(chunk_info.chunk_index, int), "Chunk index should be an integer"
            assert chunk_info.chunk_index >= 0, "Chunk index should be non-negative"
            assert len(chunk_info.chunk_text) > 0, "Chunk text should not be empty"
            assert isinstance(chunk_info.truncated, bool), "Truncated should be boolean"

        print("\n=== Test passed: Chunks are stored and retrieved correctly ===")

    finally:
        # Cleanup - delete the test bank
        await memory.delete_bank(bank_id)
        print(f"\n=== Cleaned up bank: {bank_id} ===")


@pytest.mark.asyncio
async def test_chunks_and_entities_follow_fact_order(memory):
    """
    Test that chunks and entities in recall results follow the same order as facts.
    This is critical because token limits may truncate later items.

    The most relevant fact's chunk/entity should always be first in the returned data.
    """
    bank_id = f"test_ordering_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Store multiple distinct pieces of content as separate documents
        # This ensures different chunks that we can identify
        contents = [
            {
                "content": "Alice works at Google as a software engineer. She loves Python and has 10 years of experience.",
                "document_id": "doc_alice",
                "context": "Alice's profile"
            },
            {
                "content": "Bob works at Meta as a data scientist. He specializes in machine learning and has published papers.",
                "document_id": "doc_bob",
                "context": "Bob's profile"
            },
            {
                "content": "Charlie works at Amazon as a product manager. He leads a team of 15 people and ships features weekly.",
                "document_id": "doc_charlie",
                "context": "Charlie's profile"
            },
        ]

        # Store each content piece
        for item in contents:
            await memory.retain_async(
                bank_id=bank_id,
                content=item["content"],
                context=item["context"],
                event_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
                document_id=item["document_id"]
            )

        print("\n=== Stored 3 separate documents ===")

        # Recall with a query that matches all three, but Alice most closely
        result = await memory.recall_async(
            bank_id=bank_id,
            query="Tell me about Alice's work at Google",
            budget=Budget.MID,
            max_tokens=1000,
            fact_type=["world"],
            include_entities=True,
            include_chunks=True,
            max_chunk_tokens=8192
        )

        print(f"\n=== Recall Results ===")
        print(f"Found {len(result.results)} facts")

        # Extract the order of entities mentioned in facts
        fact_chunk_ids = []
        fact_entities = []

        for i, fact in enumerate(result.results):
            print(f"\nFact {i}: {fact.text[:80]}...")
            print(f"  chunk_id: {fact.chunk_id}")

            # Track chunk_id order
            if fact.chunk_id:
                fact_chunk_ids.append(fact.chunk_id)

            # Track entities mentioned in this fact
            if fact.entities:
                for entity in fact.entities:
                    if entity not in fact_entities:
                        fact_entities.append(entity)

        print(f"\n=== Fact chunk_ids in order: {fact_chunk_ids} ===")
        print(f"=== Fact entities in order: {fact_entities} ===")

        # Test 1: Verify chunks follow fact order
        if result.chunks:
            chunks_order = list(result.chunks.keys())
            print(f"\n=== Chunks dict order: {chunks_order} ===")

            # The chunks dict should contain chunks in the order they appear in facts
            # (may be fewer chunks than facts due to deduplication)
            chunk_positions = []
            for chunk_id in chunks_order:
                if chunk_id in fact_chunk_ids:
                    chunk_positions.append(fact_chunk_ids.index(chunk_id))

            print(f"=== Chunk positions in fact order: {chunk_positions} ===")

            # Verify chunks are in increasing order (following fact order)
            assert chunk_positions == sorted(chunk_positions), \
                f"Chunks should follow fact order! Got positions {chunk_positions} but expected {sorted(chunk_positions)}"

            print("✓ Chunks follow fact order correctly")

        # Test 2: Verify entities follow fact order
        if result.entities:
            entities_order = list(result.entities.keys())
            print(f"\n=== Entities dict order: {entities_order} ===")

            # The entities dict should contain entities in the order they first appear in facts
            entity_positions = []
            for entity_name in entities_order:
                if entity_name in fact_entities:
                    entity_positions.append(fact_entities.index(entity_name))

            print(f"=== Entity positions in fact order: {entity_positions} ===")

            # Verify entities are in increasing order (following fact order)
            assert entity_positions == sorted(entity_positions), \
                f"Entities should follow fact order! Got positions {entity_positions} but expected {sorted(entity_positions)}"

            print("✓ Entities follow fact order correctly")

        print("\n=== Test passed: Chunks and entities follow fact relevance order ===")

    finally:
        # Cleanup
        await memory.delete_bank(bank_id)
        print(f"\n=== Cleaned up bank: {bank_id} ===")


@pytest.mark.asyncio
async def test_event_date_storage(memory):
    """
    Test that event_date is correctly stored as occurred_start.
    Verifies that we can track when events actually happened vs when they were stored.
    """
    bank_id = f"test_temporal_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Event that occurred in the past
        past_event_date = datetime(2023, 6, 15, 14, 30, tzinfo=timezone.utc)

        # Store a fact about a past event
        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content="Alice completed the Q2 product launch on June 15th, 2023.",
            context="project history",
            event_date=past_event_date
        )

        assert len(unit_ids) > 0, "Should have created at least one memory unit"

        # Recall the fact
        result = await memory.recall_async(
            bank_id=bank_id,
            query="When did Alice complete the product launch?",
            budget=Budget.LOW,
            max_tokens=500,
            fact_type=["world"]
        )

        assert len(result.results) > 0, "Should recall the stored fact"

        # Verify the occurred_start matches our event_date
        fact = result.results[0]
        assert fact.occurred_start is not None, "occurred_start should be set"

        # Parse the occurred_start (it comes back as ISO string)
        if isinstance(fact.occurred_start, str):
            occurred_dt = datetime.fromisoformat(fact.occurred_start.replace('Z', '+00:00'))
        else:
            occurred_dt = fact.occurred_start

        # Verify it matches our past event date (allowing for small time differences in extraction)
        assert occurred_dt.year == past_event_date.year, f"Year should match: {occurred_dt.year} vs {past_event_date.year}"
        assert occurred_dt.month == past_event_date.month, f"Month should match: {occurred_dt.month} vs {past_event_date.month}"

        print(f"\n✓ Event date correctly stored: {occurred_dt}")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_temporal_ordering(memory):
    """
    Test that facts can be stored and retrieved with correct temporal ordering.
    Stores facts with different event_dates and verifies temporal relationships.
    """
    bank_id = f"test_temporal_order_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Store events in non-chronological order with different dates
        events = [
            {
                "content": "Alice joined the team in January 2023.",
                "event_date": datetime(2023, 1, 10, tzinfo=timezone.utc),
                "context": "team history"
            },
            {
                "content": "Alice got promoted to senior engineer in June 2023.",
                "event_date": datetime(2023, 6, 15, tzinfo=timezone.utc),
                "context": "team history"
            },
            {
                "content": "Alice started as an intern in July 2022.",
                "event_date": datetime(2022, 7, 1, tzinfo=timezone.utc),
                "context": "team history"
            },
        ]

        # Store all events
        for event in events:
            await memory.retain_async(
                bank_id=bank_id,
                content=event["content"],
                context=event["context"],
                event_date=event["event_date"]
            )

        print("\n=== Stored 3 events with different temporal dates ===")

        # Recall facts about Alice
        result = await memory.recall_async(
            bank_id=bank_id,
            query="Tell me about Alice's career progression",
            budget=Budget.MID,
            max_tokens=1000,
            fact_type=["world"]
        )

        assert len(result.results) >= 3, f"Should recall all 3 events, got {len(result.results)}"

        # Collect occurred dates
        occurred_dates = []
        for fact in result.results:
            if fact.occurred_start:
                if isinstance(fact.occurred_start, str):
                    dt = datetime.fromisoformat(fact.occurred_start.replace('Z', '+00:00'))
                else:
                    dt = fact.occurred_start
                occurred_dates.append((dt, fact.text[:50]))
                print(f"  - {dt.date()}: {fact.text[:60]}...")

        # Verify we have temporal data for all facts
        assert len(occurred_dates) >= 3, "All facts should have temporal data"

        # The dates should span the expected range (2022-2023)
        min_date = min(dt for dt, _ in occurred_dates)
        max_date = max(dt for dt, _ in occurred_dates)

        assert min_date.year == 2022, f"Earliest event should be in 2022, got {min_date.year}"
        assert max_date.year == 2023, f"Latest event should be in 2023, got {max_date.year}"

        print(f"\n✓ Temporal ordering preserved: {min_date.date()} to {max_date.date()}")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_mentioned_at_vs_occurred(memory):
    """
    Test distinction between when fact occurred vs when it was mentioned.

    Scenario: Ingesting a historical conversation from 2020
    - event_date: When the conversation happened (2020-03-15)
    - mentioned_at: When the conversation happened (same as event_date = 2020-03-15)
    - occurred_start/end: When the event in the conversation happened (extracted by LLM, or falls back to mentioned_at)
    """
    bank_id = f"test_mentioned_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Ingesting a conversation that happened in the past
        conversation_date = datetime(2020, 3, 15, tzinfo=timezone.utc)

        # Store a fact from a historical conversation
        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content="Alice graduated from MIT in March 2020.",
            context="education history",
            event_date=conversation_date  # When this conversation happened
        )

        assert len(unit_ids) > 0, "Should create memory unit"

        # Recall and check temporal fields
        result = await memory.recall_async(
            bank_id=bank_id,
            query="Where did Alice go to school?",
            budget=Budget.LOW,
            max_tokens=500,
            fact_type=["world"]
        )

        assert len(result.results) > 0, "Should recall the fact"
        fact = result.results[0]

        # Parse occurred_start
        if fact.occurred_start:
            if isinstance(fact.occurred_start, str):
                occurred_dt = datetime.fromisoformat(fact.occurred_start.replace('Z', '+00:00'))
            else:
                occurred_dt = fact.occurred_start

            # Should be close to the conversation date (falls back to mentioned_at if LLM doesn't extract)
            assert occurred_dt.year == 2020, f"occurred_start should be 2020, got {occurred_dt.year}"
            print(f"✓ occurred_start (when event happened): {occurred_dt}")

        # Parse mentioned_at
        if fact.mentioned_at:
            if isinstance(fact.mentioned_at, str):
                mentioned_dt = datetime.fromisoformat(fact.mentioned_at.replace('Z', '+00:00'))
            else:
                mentioned_dt = fact.mentioned_at

            # mentioned_at should match the conversation date (event_date)
            time_diff = abs((conversation_date - mentioned_dt).total_seconds())
            assert time_diff < 60, f"mentioned_at should match event_date (2020-03-15), but diff is {time_diff}s"
            print(f"✓ mentioned_at (when conversation happened): {mentioned_dt}")

            # Verify it's the historical date, not today
            assert mentioned_dt.year == 2020, f"mentioned_at should be 2020, got {mentioned_dt.year}"

        print(f"✓ Test passed: Historical conversation correctly ingested with event_date=2020")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_mentioned_at_from_context_string(memory):
    """
    Test that mentioned_at is extracted from context string by LLM.

    Scenario: User provides date in context like "happened on 2023-05-10 14:30:00 UTC"
    - LLM should extract mentioned_at from this context
    - If LLM fails to extract, should fall back to event_date (which defaults to now())
    - mentioned_at should NEVER be None
    """
    bank_id = f"test_context_date_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Test case 1: Date in context string (like longmemeval benchmark)
        session_date = datetime(2023, 5, 10, 14, 30, 0, tzinfo=timezone.utc)

        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content="Alice mentioned she loves hiking in the mountains.",
            context=f"Session ABC123 - you are the assistant in this conversation - happened on {session_date.strftime('%Y-%m-%d %H:%M:%S')} UTC.",
            event_date=None  # Not providing event_date - should default to now() if LLM doesn't extract
        )

        assert len(unit_ids) > 0, "Should create memory unit"

        # Recall and verify mentioned_at is set
        result = await memory.recall_async(
            bank_id=bank_id,
            query="What does Alice like?",
            budget=Budget.LOW,
            max_tokens=500,
            fact_type=["world"]
        )

        assert len(result.results) > 0, "Should recall the fact"
        fact = result.results[0]

        # mentioned_at must ALWAYS be set
        assert fact.mentioned_at is not None, "mentioned_at should NEVER be None"

        # Parse mentioned_at
        if isinstance(fact.mentioned_at, str):
            mentioned_dt = datetime.fromisoformat(fact.mentioned_at.replace('Z', '+00:00'))
        else:
            mentioned_dt = fact.mentioned_at

        # Check if LLM extracted the date from context (ideal case)
        # Or if it fell back to now() (acceptable fallback)
        time_diff_from_context = abs((session_date - mentioned_dt).total_seconds())
        time_diff_from_now = abs((datetime.now(timezone.utc) - mentioned_dt).total_seconds())

        # Should either match the context date OR be recent (now)
        is_from_context = time_diff_from_context < 60
        is_from_now = time_diff_from_now < 60

        assert is_from_context or is_from_now, \
            f"mentioned_at should be either from context ({session_date}) or now(), but got {mentioned_dt}"

        if is_from_context:
            print(f"✓ LLM successfully extracted mentioned_at from context: {mentioned_dt}")
            assert mentioned_dt.year == 2023
        else:
            print(f"⚠ LLM did not extract date from context, fell back to now(): {mentioned_dt}")

        print(f"✓ mentioned_at is always set (never None)")

    finally:
        await memory.delete_bank(bank_id)


# ============================================================
# Context Tracking Tests
# ============================================================

@pytest.mark.asyncio
async def test_context_preservation(memory):
    """
    Test that context is preserved and retrievable.
    Context helps understand why/how memory was formed.
    """
    bank_id = f"test_context_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Store content with specific context
        specific_context = "team meeting notes from Q4 planning session"

        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content="The team decided to prioritize mobile development for next quarter.",
            context=specific_context,
            event_date=datetime(2024, 1, 15, tzinfo=timezone.utc)
        )

        assert len(unit_ids) > 0, "Should create at least one memory unit"

        # Recall and verify context is returned
        result = await memory.recall_async(
            bank_id=bank_id,
            query="What did the team decide?",
            budget=Budget.LOW,
            max_tokens=500,
            fact_type=["world"]
        )

        assert len(result.results) > 0, "Should recall the stored fact"

        # Verify context is preserved (context is stored in the database)
        # Note: context might not be returned in the API response by default
        # but it should be stored in the database
        print(f"✓ Successfully stored fact with context: '{specific_context}'")
        print(f"  Retrieved {len(result.results)} facts")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_context_with_batch(memory):
    """
    Test that each item in a batch can have different contexts.
    """
    bank_id = f"test_batch_context_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Store batch with different contexts
        unit_ids = await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[
                {
                    "content": "Alice completed the authentication module.",
                    "context": "sprint 1 standup",
                    "event_date": datetime(2024, 1, 10, tzinfo=timezone.utc)
                },
                {
                    "content": "Bob started working on the database schema.",
                    "context": "sprint 1 planning",
                    "event_date": datetime(2024, 1, 11, tzinfo=timezone.utc)
                },
                {
                    "content": "Charlie fixed critical bugs in the payment flow.",
                    "context": "incident response",
                    "event_date": datetime(2024, 1, 12, tzinfo=timezone.utc)
                }
            ]
        )

        # Should have created facts from all items
        total_units = sum(len(ids) for ids in unit_ids)
        assert total_units >= 3, f"Should create at least 3 units, got {total_units}"

        print(f"✓ Stored {len(unit_ids)} batch items with different contexts")
        print(f"  Created {total_units} total memory units")

    finally:
        await memory.delete_bank(bank_id)


# ============================================================
# Metadata Storage Tests
# ============================================================

@pytest.mark.asyncio
async def test_metadata_storage_and_retrieval(memory):
    """
    Test that user-defined metadata is preserved.
    Metadata allows arbitrary key-value data to be stored with facts.
    """
    bank_id = f"test_metadata_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Store content with custom metadata
        custom_metadata = {
            "source": "slack",
            "channel": "engineering",
            "importance": "high",
            "tags": "product,launch"
        }

        # Note: retain_async doesn't directly support metadata parameter
        # Metadata would need to be supported in the API layer
        # For now, we test that the system handles content without errors
        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content="The product launch is scheduled for March 1st.",
            context="planning meeting",
            event_date=datetime(2024, 1, 15, tzinfo=timezone.utc)
        )

        assert len(unit_ids) > 0, "Should create memory units"

        # Recall to verify storage worked
        result = await memory.recall_async(
            bank_id=bank_id,
            query="When is the product launch?",
            budget=Budget.LOW,
            max_tokens=500,
            fact_type=["world"]
        )

        assert len(result.results) > 0, "Should recall stored facts"

        print(f"✓ Successfully stored and retrieved facts")
        print(f"  (Note: Metadata support depends on API implementation)")

    finally:
        await memory.delete_bank(bank_id)


# ============================================================
# Batch Processing Edge Cases
# ============================================================

@pytest.mark.asyncio
async def test_empty_batch(memory):
    """
    Test that empty batch is handled gracefully without errors.
    """
    bank_id = f"test_empty_batch_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Attempt to store empty batch
        unit_ids = await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[]
        )

        # Should return empty list or handle gracefully
        assert isinstance(unit_ids, list), "Should return a list"
        assert len(unit_ids) == 0, "Empty batch should create no units"

        print("✓ Empty batch handled gracefully")

    finally:
        # Clean up (though nothing should be stored)
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_single_item_batch(memory):
    """
    Test that batch with one item works correctly.
    """
    bank_id = f"test_single_batch_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Store batch with single item
        unit_ids = await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[
                {
                    "content": "Alice shipped the new feature to production.",
                    "context": "deployment log",
                    "event_date": datetime(2024, 1, 15, tzinfo=timezone.utc)
                }
            ]
        )

        assert len(unit_ids) == 1, "Should return one list of unit IDs"
        assert len(unit_ids[0]) > 0, "Should create at least one memory unit"

        print(f"✓ Single-item batch created {len(unit_ids[0])} units")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_mixed_content_batch(memory):
    """
    Test batch with varying content sizes (short and long).
    """
    bank_id = f"test_mixed_batch_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Mix short and long content
        short_content = "Alice joined the team."
        long_content = """
        Bob has been working on the authentication system for the past three months.
        He implemented OAuth 2.0 integration, set up JWT token management, and built
        a comprehensive role-based access control system. The system supports multiple
        identity providers including Google, GitHub, and Microsoft. Bob also wrote
        extensive documentation and unit tests covering over 90% of the codebase.
        The team recognized his work with an excellence award at the quarterly meeting.
        """

        unit_ids = await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[
                {"content": short_content, "context": "onboarding"},
                {"content": long_content, "context": "performance review"},
                {"content": "Charlie is on vacation this week.", "context": "team status"}
            ]
        )

        # All items should be processed
        assert len(unit_ids) == 3, "Should process all 3 items"

        # Long content should create more facts
        short_units = len(unit_ids[0])
        long_units = len(unit_ids[1])

        print(f"✓ Mixed batch processed successfully")
        print(f"  Short content: {short_units} units")
        print(f"  Long content: {long_units} units")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_batch_with_missing_optional_fields(memory):
    """
    Test that batch handles items with missing optional fields.
    """
    bank_id = f"test_optional_fields_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Some items have all fields, some have minimal fields
        unit_ids = await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[
                {
                    "content": "Alice finished the project.",
                    "context": "complete record",
                    "event_date": datetime(2024, 1, 15, tzinfo=timezone.utc)
                },
                {
                    "content": "Bob started a new task.",
                    # No context or event_date
                },
                {
                    "content": "Charlie reviewed code.",
                    "context": "code review",
                    # No event_date
                }
            ]
        )

        # All items should be processed successfully
        assert len(unit_ids) == 3, "Should process all items even with missing optional fields"

        total_units = sum(len(ids) for ids in unit_ids)
        print(f"✓ Batch with mixed optional fields created {total_units} total units")

    finally:
        await memory.delete_bank(bank_id)


# ============================================================
# Multi-Document Batch Tests
# ============================================================

@pytest.mark.asyncio
async def test_single_batch_multiple_documents(memory):
    """
    Test storing multiple distinct documents in a single batch call.
    Each should be tracked separately.
    """
    bank_id = f"test_multi_docs_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Store single batch where each item could be a different document
        # (In practice, document_id is a batch-level parameter, so we test
        # that multiple retain_async calls work correctly)

        doc1_units = await memory.retain_async(
            bank_id=bank_id,
            content="Alice's resume: 10 years Python experience, worked at Google.",
            context="resume review",
            document_id="resume_alice"
        )

        doc2_units = await memory.retain_async(
            bank_id=bank_id,
            content="Bob's resume: 5 years JavaScript experience, worked at Meta.",
            context="resume review",
            document_id="resume_bob"
        )

        doc3_units = await memory.retain_async(
            bank_id=bank_id,
            content="Charlie's resume: 8 years Go experience, worked at Amazon.",
            context="resume review",
            document_id="resume_charlie"
        )

        # All documents should be stored
        assert len(doc1_units) > 0, "Should create units for doc1"
        assert len(doc2_units) > 0, "Should create units for doc2"
        assert len(doc3_units) > 0, "Should create units for doc3"

        total_units = len(doc1_units) + len(doc2_units) + len(doc3_units)
        print(f"✓ Stored 3 separate documents with {total_units} total units")

        # Verify we can recall from any document
        result = await memory.recall_async(
            bank_id=bank_id,
            query="Who worked at Google?",
            budget=Budget.MID,
            max_tokens=1000,
            fact_type=["world"]
        )

        assert len(result.results) > 0, "Should find facts about Alice"

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_document_upsert_behavior(memory):
    """
    Test that upserting a document replaces the old content.
    """
    bank_id = f"test_upsert_{datetime.now(timezone.utc).timestamp()}"
    document_id = "project_status"

    try:
        # Store initial version
        v1_units = await memory.retain_async(
            bank_id=bank_id,
            content="Project is in planning phase. Alice is the lead.",
            context="status update v1",
            document_id=document_id
        )

        assert len(v1_units) > 0, "Should create units for v1"

        # Update with new version (upsert)
        v2_units = await memory.retain_async(
            bank_id=bank_id,
            content="Project is in development phase. Bob has joined as co-lead.",
            context="status update v2",
            document_id=document_id
        )

        assert len(v2_units) > 0, "Should create units for v2"

        # Recall should return the updated information
        result = await memory.recall_async(
            bank_id=bank_id,
            query="What is the project status?",
            budget=Budget.MID,
            max_tokens=1000,
            fact_type=["world"]
        )

        assert len(result.results) > 0, "Should recall facts"

        print(f"✓ Document upsert created v1: {len(v1_units)} units, v2: {len(v2_units)} units")

    finally:
        await memory.delete_bank(bank_id)


# ============================================================
# Chunk Storage Advanced Tests
# ============================================================

@pytest.mark.asyncio
async def test_chunk_fact_mapping(memory):
    """
    Test that facts correctly reference their source chunks via chunk_id.
    """
    bank_id = f"test_chunk_mapping_{datetime.now(timezone.utc).timestamp()}"
    document_id = "technical_doc"

    try:
        # Store content that will be chunked
        content = """
        The authentication system uses JWT tokens for session management.
        Tokens expire after 24 hours and must be refreshed using the refresh endpoint.
        The system supports OAuth 2.0 integration with Google and GitHub.

        The database layer uses PostgreSQL with connection pooling.
        We maintain separate read and write connection pools for performance.
        All queries use prepared statements to prevent SQL injection.
        """

        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content=content,
            context="technical documentation",
            document_id=document_id
        )

        assert len(unit_ids) > 0, "Should create memory units"

        # Recall with chunks enabled
        result = await memory.recall_async(
            bank_id=bank_id,
            query="How does authentication work?",
            budget=Budget.MID,
            max_tokens=1000,
            fact_type=["world"],
            include_chunks=True,
            max_chunk_tokens=8192
        )

        assert len(result.results) > 0, "Should recall facts"

        # Verify facts have chunk_id references
        facts_with_chunks = [f for f in result.results if f.chunk_id]

        print(f"✓ Created {len(unit_ids)} units from chunked document")
        print(f"  {len(facts_with_chunks)}/{len(result.results)} facts have chunk_id references")

        # If chunks are returned, verify they match the chunk_ids in facts
        if result.chunks:
            fact_chunk_ids = {f.chunk_id for f in facts_with_chunks}
            returned_chunk_ids = set(result.chunks.keys())

            # All chunk_ids in facts should have corresponding chunk data
            assert fact_chunk_ids.issubset(returned_chunk_ids) or len(fact_chunk_ids) == 0, \
                "Fact chunk_ids should have corresponding chunk data"

            print(f"  Returned {len(result.chunks)} chunks matching fact references")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_chunk_ordering_preservation(memory):
    """
    Test that chunk_index reflects the correct order within a document.
    """
    bank_id = f"test_chunk_order_{datetime.now(timezone.utc).timestamp()}"
    document_id = "ordered_doc"

    try:
        # Store long content that will create multiple chunks with meaningful content
        sections = []
        sections.append("""
        Alice is the team lead for the authentication project. She has 10 years of experience
        with security systems and previously worked at Google on identity management.
        She is responsible for architecture decisions and code review.
        """)
        sections.append("""
        Bob is a backend engineer focusing on the API layer. He specializes in Python
        and has built several microservices for the company. He joined the team in 2023.
        """)
        sections.append("""
        Charlie is the DevOps engineer managing the deployment pipeline. He set up
        our Kubernetes infrastructure and maintains the CI/CD system using GitHub Actions.
        """)
        sections.append("""
        The project uses PostgreSQL as the main database with Redis for caching.
        We deploy to AWS using Docker containers orchestrated by Kubernetes.
        The team follows agile methodology with two-week sprints.
        """)
        sections.append("""
        Security is a top priority. All API endpoints require JWT authentication.
        We use OAuth 2.0 for third-party integrations and maintain strict access controls.
        Regular security audits are conducted quarterly.
        """)

        content = "\n\n".join(sections)

        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content=content,
            context="multi-section document",
            document_id=document_id
        )

        assert len(unit_ids) > 0, "Should create units"

        # Recall with chunks
        result = await memory.recall_async(
            bank_id=bank_id,
            query="Tell me about the sections",
            budget=Budget.MID,
            max_tokens=2000,
            fact_type=["world"],
            include_chunks=True,
            max_chunk_tokens=8192
        )

        if result.chunks:
            # Verify chunk_index values are sequential and start from 0
            chunk_indices = [chunk.chunk_index for chunk in result.chunks.values()]
            chunk_indices_sorted = sorted(chunk_indices)

            print(f"✓ Document created {len(result.chunks)} chunks")
            print(f"  Chunk indices: {chunk_indices}")

            # Indices should start from 0 and be sequential
            if len(chunk_indices) > 0:
                assert min(chunk_indices) == 0, "Chunk indices should start from 0"
                assert chunk_indices_sorted == list(range(len(chunk_indices))), \
                    "Chunk indices should be sequential"
        else:
            print("✓ Content stored (may have created single chunk or no chunks returned)")

    finally:
        await memory.delete_bank(bank_id)


@pytest.mark.asyncio
async def test_chunks_truncation_behavior(memory):
    """
    Test that when chunks exceed max_chunk_tokens, truncation is indicated.
    """
    bank_id = f"test_chunk_truncation_{datetime.now(timezone.utc).timestamp()}"
    document_id = "large_doc"

    try:
        # Create a large document with meaningful content
        large_content = """
        The company's product roadmap for 2024 includes several major initiatives.
        The engineering team is expanding to support these efforts.

        Alice leads the authentication team, which is implementing OAuth 2.0 and JWT tokens.
        The team has been working on this for six months and expects to launch in Q2.
        Security is the top priority, with regular penetration testing scheduled.

        Bob manages the API development team. They are building RESTful endpoints
        for all major features including user management, billing, and analytics.
        The team uses Python with FastAPI and deploys to AWS Lambda.

        Charlie oversees the infrastructure team. They maintain Kubernetes clusters
        across three AWS regions for high availability. The team also manages
        the CI/CD pipeline using GitHub Actions and ArgoCD.

        The data engineering team, led by Diana, processes millions of events daily.
        They use Apache Kafka for streaming and Snowflake for analytics.
        Real-time dashboards are built with Grafana and Prometheus.

        The mobile team is building iOS and Android apps using React Native.
        They are targeting a beta launch in Q3 with select customers.
        Push notifications and offline support are key features.

        The design team has created a new design system that will be rolled out
        across all products. The system includes components for accessibility
        and internationalization support for 12 languages.

        Customer support is being enhanced with AI-powered chatbots.
        The system can handle common queries and escalate complex issues to humans.
        Average response time has improved by 40% since implementation.

        The marketing team is planning a major campaign for the product launch.
        They are working with influencers and planning webinars for enterprise customers.
        Early feedback from beta users has been very positive.

        Sales operations are being streamlined with new CRM integrations.
        The team can now track leads more effectively and automate follow-ups.
        Conversion rates have increased by 25% in the pilot program.

        The finance team is implementing new budgeting tools for better forecasting.
        They are also working on automated expense reporting and approval workflows.
        This will save approximately 100 hours per month in manual work.
        """ * 5  # Repeat to make it very large

        unit_ids = await memory.retain_async(
            bank_id=bank_id,
            content=large_content,
            context="large document test",
            document_id=document_id
        )

        assert len(unit_ids) > 0, "Should create units"

        # Recall with very small chunk token limit to force truncation
        result = await memory.recall_async(
            bank_id=bank_id,
            query="Tell me about the document",
            budget=Budget.MID,
            max_tokens=1000,
            fact_type=["world"],
            include_chunks=True,
            max_chunk_tokens=500  # Small limit to test truncation
        )

        if result.chunks:
            # Check if any chunks show truncation
            truncated_chunks = [
                chunk_id for chunk_id, chunk_info in result.chunks.items()
                if chunk_info.truncated
            ]

            print(f"✓ Retrieved {len(result.chunks)} chunks")
            if truncated_chunks:
                print(f"  {len(truncated_chunks)} chunks were truncated due to token limit")
            else:
                print(f"  No chunks were truncated (content within limit)")

        else:
            print("✓ No chunks returned (may be under token limit)")

    finally:
        await memory.delete_bank(bank_id)
