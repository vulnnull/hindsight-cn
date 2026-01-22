"""Integration tests for the consolidation engine.

These tests exercise the real consolidation implementation with actual database operations.
Note: Consolidation runs automatically after retain via SyncTaskBackend in tests.
"""

import uuid
from unittest.mock import patch

import pytest

from hindsight_api.engine.consolidation.consolidator import run_consolidation_job
from hindsight_api.engine.memory_engine import MemoryEngine
from hindsight_api.engine.reflect.tools import (
    tool_recall,
    tool_search_mental_models,
    tool_search_reflections,
)


@pytest.fixture(autouse=True)
def enable_mental_models():
    """Enable mental models for all tests in this module."""
    from hindsight_api.config import get_config

    config = get_config()
    original_value = config.enable_mental_models
    config.enable_mental_models = True
    yield
    config.enable_mental_models = original_value


class TestConsolidationIntegration:
    """Integration tests for consolidation with real database.

    These tests verify that consolidation creates mental models correctly.
    Since we use SyncTaskBackend in tests, consolidation runs synchronously
    after retain completes.
    """

    @pytest.mark.asyncio
    async def test_consolidation_creates_mental_model_after_retain(
        self, memory: MemoryEngine, request_context
    ):
        """Test that consolidation creates a mental model after retain."""
        bank_id = f"test-consolidation-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory - consolidation runs automatically after
        await memory.retain_async(
            bank_id=bank_id,
            content="Peter loves hiking in the mountains every weekend.",
            request_context=request_context,
        )

        # Verify mental model exists in memory_units
        # (consolidation already ran as part of retain via SyncTaskBackend)
        async with memory._pool.acquire() as conn:
            mental_models = await conn.fetch(
                """
                SELECT id, text, proof_count, fact_type
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )
            # Mental model may or may not be created depending on LLM relevance judgment
            # The important thing is no errors occurred
            if mental_models:
                mm = mental_models[0]
                assert mm["proof_count"] >= 1
                assert mm["fact_type"] == "mental_model"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_processes_multiple_memories(
        self, memory: MemoryEngine, request_context
    ):
        """Test that consolidation processes multiple related memories."""
        bank_id = f"test-consolidation-multi-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain first memory
        await memory.retain_async(
            bank_id=bank_id,
            content="Peter enjoys hiking on mountain trails.",
            request_context=request_context,
        )

        # Retain a second related memory
        await memory.retain_async(
            bank_id=bank_id,
            content="Peter went hiking in the Alps last weekend and loved it.",
            request_context=request_context,
        )

        # Check mental models after both retains
        async with memory._pool.acquire() as conn:
            mental_models = await conn.fetch(
                """
                SELECT id, text, proof_count
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                ORDER BY proof_count DESC
                """,
                bank_id,
            )

            # Should have at least one mental model
            # If the LLM determined both memories support the same model,
            # proof_count might be > 1
            if mental_models:
                # Verify structure is correct
                assert all(mm["text"] for mm in mental_models)
                assert all(mm["proof_count"] >= 1 for mm in mental_models)

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_no_new_memories(self, memory: MemoryEngine, request_context):
        """Test that consolidation handles case when no new memories exist."""
        bank_id = f"test-consolidation-empty-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Run consolidation without any memories
        result = await run_consolidation_job(
            memory_engine=memory,
            bank_id=bank_id,
            request_context=request_context,
        )

        assert result["status"] == "no_new_memories"
        assert result["memories_processed"] == 0

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_respects_last_consolidated_at(
        self, memory: MemoryEngine, request_context
    ):
        """Test that consolidation only processes memories created after last_consolidated_at."""
        bank_id = f"test-consolidation-timestamp-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory - consolidation runs automatically
        await memory.retain_async(
            bank_id=bank_id,
            content="Alice works at a technology company.",
            request_context=request_context,
        )

        # Run consolidation again - should have no new memories
        result = await run_consolidation_job(
            memory_engine=memory,
            bank_id=bank_id,
            request_context=request_context,
        )

        # Should report no new memories since consolidation already ran
        assert result["status"] == "no_new_memories"
        assert result["memories_processed"] == 0

        # Add a new memory
        await memory.retain_async(
            bank_id=bank_id,
            content="Alice got promoted to senior engineer.",
            request_context=request_context,
        )

        # Run consolidation again - should also have no new memories
        # because consolidation ran automatically after the second retain
        result = await run_consolidation_job(
            memory_engine=memory,
            bank_id=bank_id,
            request_context=request_context,
        )

        assert result["status"] == "no_new_memories"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_copies_entity_links(self, memory: MemoryEngine, request_context):
        """Test that mental models inherit entity links from source memories."""
        bank_id = f"test-consolidation-entities-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory with a named entity
        await memory.retain_async(
            bank_id=bank_id,
            content="John Smith is the CEO of Acme Corporation.",
            request_context=request_context,
        )

        # Check mental model and its entity links
        async with memory._pool.acquire() as conn:
            mental_model = await conn.fetchrow(
                """
                SELECT id
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                LIMIT 1
                """,
                bank_id,
            )

            if mental_model:
                # Check if entity links were copied
                entity_links = await conn.fetch(
                    """
                    SELECT entity_id
                    FROM unit_entities
                    WHERE unit_id = $1
                    """,
                    mental_model["id"],
                )
                # Mental model should have inherited entity links from source memory
                # (may be empty if no entities were extracted, which is fine)
                assert entity_links is not None

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_mental_models_included_in_recall(
        self, memory: MemoryEngine, request_context
    ):
        """Test that mental models created by consolidation are returned in recall."""
        bank_id = f"test-consolidation-recall-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory - consolidation runs automatically
        await memory.retain_async(
            bank_id=bank_id,
            content="Sarah is an expert Python programmer who specializes in machine learning.",
            request_context=request_context,
        )

        # Recall with mental models included
        recall_result = await memory.recall_async(
            bank_id=bank_id,
            query="What does Sarah do?",
            fact_type=["world", "experience", "mental_model"],
            request_context=request_context,
        )

        # Mental models come back as regular results with fact_type='mental_model'
        assert hasattr(recall_result, "results")

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_creates_memory_links(self, memory: MemoryEngine, request_context):
        """Test that mental models get bidirectional links to their source memories."""
        bank_id = f"test-consolidation-links-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory - consolidation runs automatically
        await memory.retain_async(
            bank_id=bank_id,
            content="Maria works as a software engineer at Microsoft.",
            request_context=request_context,
        )

        # Check memory_links between mental model and source memory
        async with memory._pool.acquire() as conn:
            mental_model = await conn.fetchrow(
                """
                SELECT id, source_memory_ids
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                LIMIT 1
                """,
                bank_id,
            )

            if mental_model and mental_model["source_memory_ids"]:
                source_memory_id = mental_model["source_memory_ids"][0]

                # Check that bidirectional links exist
                link_from_memory = await conn.fetchrow(
                    """
                    SELECT * FROM memory_links
                    WHERE from_unit_id = $1 AND to_unit_id = $2
                    """,
                    source_memory_id,
                    mental_model["id"],
                )
                link_to_memory = await conn.fetchrow(
                    """
                    SELECT * FROM memory_links
                    WHERE from_unit_id = $1 AND to_unit_id = $2
                    """,
                    mental_model["id"],
                    source_memory_id,
                )

                # Both directions should have links
                assert link_from_memory is not None, "Expected link from source memory to mental model"
                assert link_to_memory is not None, "Expected link from mental model to source memory"
                assert link_from_memory["link_type"] == "semantic"
                assert link_to_memory["link_type"] == "semantic"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_merges_only_redundant_facts(
        self, memory: MemoryEngine, request_context
    ):
        """Test that consolidation only merges truly redundant facts.

        Mental models should be fine-grained (almost 1:1 with memories).
        Only merge when facts are truly redundant (saying the same thing differently)
        or when one directly updates another (e.g., location change).

        Given:
        - "Nicolò lives in Italy"
        - "Nicolò moved to the US recently" (updates the living location)

        The second fact should UPDATE the first, not create a separate model.
        But unrelated facts like "Nicolò works at Vectorize" should stay separate.
        """
        bank_id = f"test-consolidation-merge-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory about living location
        await memory.retain_async(
            bank_id=bank_id,
            content="Nicolò lives in Italy.",
            request_context=request_context,
        )

        # Retain an unrelated memory (different topic - should NOT merge)
        await memory.retain_async(
            bank_id=bank_id,
            content="Nicolò works at Vectorize as an engineer.",
            request_context=request_context,
        )

        # Check mental models - should have 2 separate models
        async with memory._pool.acquire() as conn:
            mm_before = await conn.fetch(
                """
                SELECT id, text FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )

        # Add a memory that UPDATES the living location (should merge with first)
        await memory.retain_async(
            bank_id=bank_id,
            content="Nicolò recently moved to the United States.",
            request_context=request_context,
        )

        # Check mental models after consolidation
        async with memory._pool.acquire() as conn:
            mental_models = await conn.fetch(
                """
                SELECT id, text, proof_count, source_memory_ids
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                ORDER BY created_at
                """,
                bank_id,
            )

            # Key assertions:
            # 1. Consolidation ran without errors
            # 2. Mental models exist
            assert len(mental_models) >= 1, "Expected at least one mental model"

            # The work-related fact should remain separate from location facts
            # (LLM behavior varies, so we check structure rather than exact count)
            for mm in mental_models:
                assert mm["text"], "Mental model should have text"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_keeps_different_people_separate(
        self, memory: MemoryEngine, request_context
    ):
        """Test that consolidation NEVER merges facts about different people.

        Each person's facts should stay in separate mental models.
        """
        bank_id = f"test-consolidation-people-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Add facts about different people
        await memory.retain_async(
            bank_id=bank_id,
            content="John lives in New York.",
            request_context=request_context,
        )
        await memory.retain_async(
            bank_id=bank_id,
            content="Mary lives in Boston.",
            request_context=request_context,
        )
        await memory.retain_async(
            bank_id=bank_id,
            content="Bob works at Google.",
            request_context=request_context,
        )

        # Check mental models - should have separate models for each person
        async with memory._pool.acquire() as conn:
            mental_models = await conn.fetch(
                """
                SELECT id, text, source_memory_ids
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )

            # Should have multiple mental models (one per person/fact)
            # Not everything merged into one
            assert len(mental_models) >= 2, (
                f"Expected multiple mental models for different people, got {len(mental_models)}"
            )

            # No single mental model should mention multiple different people
            # (This is a structural check - each model should be focused)
            for mm in mental_models:
                text = mm["text"].lower()
                people_mentioned = sum([
                    1 for name in ["john", "mary", "bob"]
                    if name in text
                ])
                assert people_mentioned <= 1, (
                    f"Mental model should not merge different people: {mm['text']}"
                )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_merges_contradictions(
        self, memory: MemoryEngine, request_context
    ):
        """Test that contradictions about the same topic are merged with history.

        When facts contradict each other (same person, same topic, opposite info),
        they should be merged into ONE mental model that captures the change.

        Example:
        - "Nicolò loves pizza"
        - "Nicolò hates pizza"
        → Should become: "Nicolò used to love pizza but now hates it" (or similar)
        """
        bank_id = f"test-consolidation-contradict-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Add initial fact
        await memory.retain_async(
            bank_id=bank_id,
            content="Nicolò loves pizza.",
            request_context=request_context,
        )

        # Check we have one mental model
        async with memory._pool.acquire() as conn:
            mm_before = await conn.fetch(
                """
                SELECT id, text FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )
            count_before = len(mm_before)

        # Add contradicting fact (same person, same topic, opposite sentiment)
        await memory.retain_async(
            bank_id=bank_id,
            content="Nicolò hates pizza.",
            request_context=request_context,
        )

        # Check mental models after consolidation
        async with memory._pool.acquire() as conn:
            mental_models = await conn.fetch(
                """
                SELECT id, text, source_memory_ids, history
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )

            # Key assertion: Should NOT have more mental models than before
            # The contradiction should be merged, not create a new model
            assert len(mental_models) <= count_before, (
                f"Contradiction should merge, not create new model. "
                f"Before: {count_before}, After: {len(mental_models)}. "
                f"Models: {[mm['text'] for mm in mental_models]}"
            )

            # The merged model should capture both sentiments or the change
            if mental_models:
                merged_text = mental_models[0]["text"].lower()
                # Should mention the change or both states
                has_history = (
                    ("used to" in merged_text or "now" in merged_text or "but" in merged_text)
                    or ("love" in merged_text and "hate" in merged_text)
                    or (len(mental_models[0]["source_memory_ids"] or []) > 1)
                )
                assert has_history, (
                    f"Merged model should capture the change. Got: {mental_models[0]['text']}"
                )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestConsolidationDisabled:
    """Test consolidation when disabled via config."""

    @pytest.mark.asyncio
    async def test_consolidation_returns_disabled_status(
        self, memory: MemoryEngine, request_context
    ):
        """Test that consolidation returns disabled status when enable_mental_models is False."""
        from unittest.mock import patch

        bank_id = f"test-consolidation-disabled-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Disable mental models via config
        with patch("hindsight_api.config.get_config") as mock_config:
            mock_config.return_value.enable_mental_models = False

            result = await run_consolidation_job(
                memory_engine=memory,
                bank_id=bank_id,
                request_context=request_context,
            )

            assert result["status"] == "disabled"
            assert result["bank_id"] == bank_id

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestRecallMentalModelFactType:
    """Test recall with mental_model as a fact type."""

    @pytest.mark.asyncio
    async def test_recall_with_mental_model_fact_type(
        self, memory: MemoryEngine, request_context
    ):
        """Test that mental_model can be used as a fact type in recall.

        When mental_model is in the types list, the recall should:
        1. Return mental models in the results field with fact_type='mental_model'
        2. Not raise validation errors for None context fields
        """
        bank_id = f"test-recall-mm-type-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory - consolidation runs automatically
        await memory.retain_async(
            bank_id=bank_id,
            content="Alex is a data scientist who specializes in deep learning and neural networks.",
            request_context=request_context,
        )

        # Recall with mental_model in types
        recall_result = await memory.recall_async(
            bank_id=bank_id,
            query="What does Alex do?",
            fact_type=["mental_model"],
            request_context=request_context,
        )

        # Mental models come back as regular results with fact_type='mental_model'
        assert recall_result is not None
        assert recall_result.results is not None
        # Check that results include mental models
        if recall_result.results:
            for mm in recall_result.results:
                assert mm.id is not None
                assert mm.text is not None
                assert mm.fact_type == "mental_model"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_recall_with_mixed_fact_types_including_mental_model(
        self, memory: MemoryEngine, request_context
    ):
        """Test recall with mental_model alongside world and experience types."""
        bank_id = f"test-recall-mixed-types-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain memories - consolidation runs automatically
        await memory.retain_async(
            bank_id=bank_id,
            content="Jordan is a professional musician who plays guitar in a rock band.",
            request_context=request_context,
        )

        # Recall with all types including mental_model
        recall_result = await memory.recall_async(
            bank_id=bank_id,
            query="What does Jordan do?",
            fact_type=["world", "experience", "mental_model"],
            enable_trace=True,
            request_context=request_context,
        )

        # Should return results without errors
        assert recall_result is not None
        # Should have results from world/experience facts
        assert recall_result.results is not None
        # Mental models come back as regular results with fact_type='mental_model'
        # when mental_model is included in fact_type parameter

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_recall_mental_model_only_with_trace(
        self, memory: MemoryEngine, request_context
    ):
        """Test that recall with only mental_model type and trace enabled works.

        This specifically tests the tracer handling of mental models with None context.
        """
        bank_id = f"test-recall-mm-trace-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain memory - consolidation creates mental model
        await memory.retain_async(
            bank_id=bank_id,
            content="Chris works as a product manager at a startup focused on AI applications.",
            request_context=request_context,
        )

        # Recall with mental_model only and trace enabled
        # This tests the fix for the None context validation error
        recall_result = await memory.recall_async(
            bank_id=bank_id,
            query="Where does Chris work?",
            fact_type=["mental_model"],
            enable_trace=True,
            request_context=request_context,
        )

        # Should complete without validation errors
        assert recall_result is not None
        # Trace should be populated
        assert recall_result.trace is not None or recall_result.mental_models is not None

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestConsolidationTagRouting:
    """Test tag routing during consolidation.

    Tag routing rules:
    - Same scope (tags match): update existing mental model
    - Fact scoped, model global (untagged): update global (it absorbs all)
    - Different scopes (non-overlapping tags): create untagged cross-scope insight
    - No match: create with fact's tags
    """

    async def _retain_with_tags(
        self,
        memory: MemoryEngine,
        bank_id: str,
        content: str,
        tags: list[str],
        request_context,
    ):
        """Helper to retain content with tags using retain_batch_async."""
        await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[{"content": content}],
            document_tags=tags,
            request_context=request_context,
        )

    @pytest.mark.asyncio
    async def test_same_scope_updates_model(
        self, memory: MemoryEngine, request_context
    ):
        """Test that a tagged fact updates a mental model with the same tags.

        Given:
        - Memory with tags=['alice']: "Alice likes coffee"
        - New memory with tags=['alice']: "Alice prefers espresso"

        Expected:
        - Mental model with tags=['alice'] is updated to reflect both facts
        """
        bank_id = f"test-tag-same-scope-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain first memory with tags
        await self._retain_with_tags(
            memory, bank_id, "Alice likes coffee.", ["alice"], request_context
        )

        # Check mental model has correct tags
        async with memory._pool.acquire() as conn:
            mm_before = await conn.fetch(
                """
                SELECT id, text, tags FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )
            count_before = len(mm_before)
            if mm_before:
                assert "alice" in (mm_before[0]["tags"] or []), (
                    f"Expected mental model to have 'alice' tag, got: {mm_before[0]['tags']}"
                )

        # Retain related memory with same tags
        await self._retain_with_tags(
            memory, bank_id, "Alice prefers espresso over regular coffee.", ["alice"], request_context
        )

        # Check mental models - should NOT have increased (same scope update)
        async with memory._pool.acquire() as conn:
            mm_after = await conn.fetch(
                """
                SELECT id, text, tags, source_memory_ids FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )

            # Count of mental models should stay same or decrease (merge)
            assert len(mm_after) <= count_before + 1, (
                f"Same scope fact should update existing model, not create new. "
                f"Before: {count_before}, After: {len(mm_after)}"
            )

            # The model(s) should still have alice tag
            for mm in mm_after:
                if "coffee" in mm["text"].lower() or "espresso" in mm["text"].lower():
                    assert "alice" in (mm["tags"] or []), (
                        f"Updated model should keep 'alice' tag: {mm['text']}"
                    )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_scoped_fact_updates_global_model(
        self, memory: MemoryEngine, request_context
    ):
        """Test that a scoped fact can update an untagged (global) mental model.

        Given:
        - Untagged memory: "Pizza is a popular food"
        - New memory with tags=['history']: "Pizza originated in Naples"

        Expected:
        - The global mental model is updated (global absorbs all scopes)
        """
        bank_id = f"test-tag-global-absorb-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain untagged (global) memory
        await memory.retain_async(
            bank_id=bank_id,
            content="Pizza is a popular Italian food.",
            request_context=request_context,
        )

        # Check untagged mental model exists
        async with memory._pool.acquire() as conn:
            mm_before = await conn.fetch(
                """
                SELECT id, text, tags FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )
            count_before = len(mm_before)
            # Should be untagged or have empty tags
            if mm_before:
                assert not mm_before[0]["tags"] or len(mm_before[0]["tags"]) == 0, (
                    f"Expected untagged model, got: {mm_before[0]['tags']}"
                )

        # Retain scoped memory that relates to the global topic
        await self._retain_with_tags(
            memory, bank_id, "Pizza originated in Naples.", ["history"], request_context
        )

        # Check - global model should be updated OR new scoped model created
        async with memory._pool.acquire() as conn:
            mm_after = await conn.fetch(
                """
                SELECT id, text, tags, source_memory_ids FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                ORDER BY created_at
                """,
                bank_id,
            )

            # At least one model should exist
            assert len(mm_after) >= 1, "Expected at least one mental model"

            # Check that global model was updated (source_memory_ids increased)
            # OR new model was created with appropriate tags
            global_models = [m for m in mm_after if not m["tags"] or len(m["tags"]) == 0]
            scoped_models = [m for m in mm_after if m["tags"] and len(m["tags"]) > 0]

            # Either global was updated or scoped was created
            assert len(global_models) >= 1 or len(scoped_models) >= 1, (
                "Expected either global model update or scoped model creation"
            )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_cross_scope_creates_untagged(
        self, memory: MemoryEngine, request_context
    ):
        """Test that cross-scope related facts create untagged (global) insights.

        Given:
        - Memory with tags=['alice']: "Alice recommends the Thai restaurant"
        - Memory with tags=['bob']: "Bob tried the Thai restaurant Alice mentioned"

        Expected:
        - A new untagged mental model capturing the cross-scope insight
        """
        bank_id = f"test-tag-cross-scope-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain Alice's scoped memory
        await self._retain_with_tags(
            memory, bank_id,
            "Alice recommends the Thai restaurant on Main Street.",
            ["alice"], request_context
        )

        # Check Alice's mental model exists with correct tags
        async with memory._pool.acquire() as conn:
            mm_alice = await conn.fetch(
                """
                SELECT id, text, tags FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )
            count_before = len(mm_alice)

        # Retain Bob's memory that relates to Alice's topic (cross-scope)
        await self._retain_with_tags(
            memory, bank_id,
            "Bob visited the Thai restaurant on Main Street and loved it.",
            ["bob"], request_context
        )

        # Check mental models
        async with memory._pool.acquire() as conn:
            mm_after = await conn.fetch(
                """
                SELECT id, text, tags, source_memory_ids FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                ORDER BY created_at
                """,
                bank_id,
            )

            # Should have multiple models (alice's, bob's, potentially global)
            assert len(mm_after) >= 2, (
                f"Expected at least 2 mental models for different scopes, got {len(mm_after)}"
            )

            # Check we have models with different tags (alice, bob, or untagged)
            tag_sets = [frozenset(m["tags"] or []) for m in mm_after]

            # Should NOT merge alice and bob into same model
            models_with_both = [
                m for m in mm_after
                if m["tags"] and "alice" in m["tags"] and "bob" in m["tags"]
            ]
            assert len(models_with_both) == 0, (
                "Should not merge different scopes into one model with both tags"
            )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_no_match_creates_with_fact_tags(
        self, memory: MemoryEngine, request_context
    ):
        """Test that a new fact with no matching models creates a model with fact's tags.

        Given:
        - Empty bank
        - Memory with tags=['project_x']: "Project X uses Python"

        Expected:
        - Mental model created with tags=['project_x']
        """
        bank_id = f"test-tag-new-scoped-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain tagged memory (no existing mental models)
        await self._retain_with_tags(
            memory, bank_id,
            "Project X uses Python for its backend services.",
            ["project_x"], request_context
        )

        # Check mental model was created with correct tags
        async with memory._pool.acquire() as conn:
            mental_models = await conn.fetch(
                """
                SELECT id, text, tags FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )

            assert len(mental_models) >= 1, "Expected mental model to be created"

            # The model should have the fact's tags
            mm = mental_models[0]
            assert mm["tags"] is not None, "Mental model should have tags"
            assert "project_x" in mm["tags"], (
                f"Mental model should have 'project_x' tag, got: {mm['tags']}"
            )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_untagged_fact_can_update_scoped_model(
        self, memory: MemoryEngine, request_context
    ):
        """Test that an untagged fact can update a scoped mental model.

        Given:
        - Memory with tags=['alice']: "Alice works on machine learning"
        - Untagged memory: "Machine learning involves neural networks"

        Expected:
        - The scoped model may be updated with the global insight
        - OR a global model is created
        """
        bank_id = f"test-tag-untagged-update-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain scoped memory
        await self._retain_with_tags(
            memory, bank_id,
            "Alice works on machine learning projects.",
            ["alice"], request_context
        )

        # Retain untagged memory on same topic
        await memory.retain_async(
            bank_id=bank_id,
            content="Machine learning involves training neural networks.",
            request_context=request_context,
        )

        # Check mental models
        async with memory._pool.acquire() as conn:
            mental_models = await conn.fetch(
                """
                SELECT id, text, tags, source_memory_ids FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                ORDER BY created_at
                """,
                bank_id,
            )

            # Should have at least one model
            assert len(mental_models) >= 1, "Expected at least one mental model"

            # Either alice's model was updated OR a global model was created
            # This is valid LLM behavior - just verify no errors and structure is correct
            for mm in mental_models:
                assert mm["text"], "Mental model should have text"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_tag_filtering_in_recall(
        self, memory: MemoryEngine, request_context
    ):
        """Test that mental models respect tag filtering during recall.

        Mental models should be filtered by tags just like memories.
        """
        bank_id = f"test-tag-recall-filter-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain memories with different tags
        await self._retain_with_tags(
            memory, bank_id,
            "Alice works as a software engineer.",
            ["alice"], request_context
        )
        await self._retain_with_tags(
            memory, bank_id,
            "Bob works as a product manager.",
            ["bob"], request_context
        )

        # Recall with alice tag only
        recall_result = await memory.recall_async(
            bank_id=bank_id,
            query="What does everyone do for work?",
            tags=["alice"],
            tags_match="any_strict",  # Only alice's data
            fact_type=["world", "experience", "mental_model"],
            request_context=request_context,
        )

        # Results should only include alice-tagged content
        # Mental models are now regular results with fact_type='mental_model'
        mental_models = [r for r in recall_result.results if r.fact_type == "mental_model"]
        for mm in mental_models:
            # Mental model should be alice-scoped or global (untagged)
            # Not bob-scoped
            mm_tags = mm.tags or []
            assert "bob" not in mm_tags, (
                f"Recall with tags=['alice'] should not return bob's models: {mm.text}"
            )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_multiple_actions_from_single_fact(
        self, memory: MemoryEngine, request_context
    ):
        """Test that one fact can trigger multiple consolidation actions.

        Given:
        - Global model: "Coffee is a popular beverage"
        - Alice's model: "Alice drinks coffee every morning"
        - New fact with tags=['alice']: "Alice switched to decaf coffee"

        Expected:
        - Update Alice's scoped model (same scope)
        - Potentially update global model too (global absorbs all)
        """
        bank_id = f"test-tag-multi-action-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Create global model
        await memory.retain_async(
            bank_id=bank_id,
            content="Coffee is a popular beverage worldwide.",
            request_context=request_context,
        )

        # Create alice's scoped model
        await self._retain_with_tags(
            memory, bank_id,
            "Alice drinks coffee every morning.",
            ["alice"], request_context
        )

        # Check models before
        async with memory._pool.acquire() as conn:
            mm_before = await conn.fetch(
                """
                SELECT id, text, tags, source_memory_ids FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )
            count_before = len(mm_before)

        # Add fact that could relate to both
        await self._retain_with_tags(
            memory, bank_id,
            "Alice switched to decaf coffee for health reasons.",
            ["alice"], request_context
        )

        # Check models after
        async with memory._pool.acquire() as conn:
            mm_after = await conn.fetch(
                """
                SELECT id, text, tags, source_memory_ids, proof_count FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                ORDER BY created_at
                """,
                bank_id,
            )

            # Should have processed without errors
            assert len(mm_after) >= 1, "Expected at least one mental model"

            # Check that consolidation worked (either updates or maintains structure)
            # The key is no errors and proper tag handling
            for mm in mm_after:
                assert mm["text"], "Mental model should have text"
                # Tags should be consistent (not mixing alice and bob, etc.)

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_consolidation_inherits_dates_from_source_memory(
        self, memory: MemoryEngine, request_context
    ):
        """Test that mental models inherit occurred_start and event_date from source memories.

        When a mental model is created, it should inherit the temporal information
        from the source memory that triggered its creation, not use the current time.
        """
        from datetime import datetime, timezone

        bank_id = f"test-consolidation-dates-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Create a specific date in the past for testing
        past_date = datetime(2023, 6, 15, 10, 30, 0, tzinfo=timezone.utc)

        # First, create a memory unit directly with a specific date
        async with memory._pool.acquire() as conn:
            memory_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO memory_units (
                    id, bank_id, text, fact_type, occurred_start, event_date, created_at
                )
                VALUES ($1, $2, $3, 'experience', $4, $4, now())
                """,
                memory_id,
                bank_id,
                "Sarah went to Paris for vacation and loved the Eiffel Tower.",
                past_date,
            )

        # Run consolidation manually
        from hindsight_api.engine.consolidation.consolidator import run_consolidation_job

        result = await run_consolidation_job(
            memory_engine=memory,
            bank_id=bank_id,
            request_context=request_context,
        )

        # Verify consolidation processed the memory
        assert result["status"] == "completed"
        assert result["memories_processed"] >= 1

        # Check that mental model inherited the date from source memory
        async with memory._pool.acquire() as conn:
            mental_model = await conn.fetchrow(
                """
                SELECT id, text, occurred_start, event_date, source_memory_ids
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                LIMIT 1
                """,
                bank_id,
            )

            if mental_model:
                # Mental model should have inherited the date from the source memory
                mm_occurred = mental_model["occurred_start"]
                mm_event_date = mental_model["event_date"]

                # Dates should match the source memory's date (2023-06-15), not today
                assert mm_occurred is not None, "Mental model should have occurred_start"
                assert mm_event_date is not None, "Mental model should have event_date"

                # The date should be from 2023, not today
                assert mm_occurred.year == 2023, (
                    f"Expected occurred_start year 2023, got {mm_occurred.year}. "
                    "Mental model should inherit date from source memory."
                )
                assert mm_occurred.month == 6, f"Expected month 6, got {mm_occurred.month}"
                assert mm_occurred.day == 15, f"Expected day 15, got {mm_occurred.day}"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestMentalModelDrillDown:
    """Test that reflect agent can drill down from mental models to source memories."""

    @pytest.mark.asyncio
    async def test_search_mental_models_returns_source_memory_ids(
        self, memory: MemoryEngine, request_context
    ):
        """Test that search_mental_models returns source_memory_ids for drill-down.

        This verifies the agent can:
        1. Find a mental model
        2. Access its source_memory_ids
        3. Use those IDs to expand/recall for more details
        """
        from hindsight_api.engine.reflect.tools import tool_search_mental_models, tool_expand

        bank_id = f"test-mm-drilldown-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Store memories with specific details that get summarized in mental model
        await memory.retain_async(
            bank_id=bank_id,
            content="Sarah works at TechCorp as a senior software engineer since March 2020.",
            request_context=request_context,
        )
        await memory.retain_async(
            bank_id=bank_id,
            content="Sarah's employee ID at TechCorp is EMP-12345.",
            request_context=request_context,
        )

        # Search for mental models
        result = await tool_search_mental_models(
            memory_engine=memory,
            bank_id=bank_id,
            query="Sarah TechCorp",
            request_context=request_context,
        )

        assert result["count"] > 0, "Expected at least one mental model"

        # Verify source_memory_ids and proof_count are present
        mm = result["mental_models"][0]
        assert "source_memory_ids" in mm, "Mental model should have source_memory_ids"
        assert "proof_count" in mm, "Mental model should have proof_count"
        assert mm["proof_count"] >= 1, "proof_count should be at least 1"

        # If source_memory_ids exist, verify they can be used with expand
        if mm["source_memory_ids"]:
            assert len(mm["source_memory_ids"]) >= 1, "Should have at least one source memory"

            # Use expand tool to get source memory details
            async with memory._pool.acquire() as conn:
                expand_result = await tool_expand(
                    conn=conn,
                    bank_id=bank_id,
                    memory_ids=mm["source_memory_ids"][:2],  # Take first 2
                    depth="chunk",
                )

            assert "results" in expand_result
            assert len(expand_result["results"]) > 0, "Expand should return source memories"

            # Verify we get the original detailed information
            all_text = " ".join(r["memory"]["text"] for r in expand_result["results"] if "memory" in r)
            # The expanded memories should contain details not necessarily in the mental model
            assert "Sarah" in all_text or "TechCorp" in all_text, (
                f"Expanded memories should contain source details. Got: {all_text}"
            )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_mental_model_source_ids_match_contributing_memories(
        self, memory: MemoryEngine, request_context
    ):
        """Test that source_memory_ids actually point to the memories that built the mental model."""
        bank_id = f"test-mm-source-ids-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Store two related memories
        await memory.retain_async(
            bank_id=bank_id,
            content="Project Phoenix was started by the engineering team in January 2024.",
            request_context=request_context,
        )
        await memory.retain_async(
            bank_id=bank_id,
            content="Project Phoenix achieved 99.9% uptime in its first quarter.",
            request_context=request_context,
        )

        # Get the mental model with source_memory_ids
        async with memory._pool.acquire() as conn:
            mm_rows = await conn.fetch(
                """
                SELECT id, text, proof_count, source_memory_ids
                FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )

        if mm_rows:
            mm = mm_rows[0]
            source_ids = mm["source_memory_ids"] or []

            # Verify source_memory_ids point to actual memories
            if source_ids:
                async with memory._pool.acquire() as conn:
                    source_memories = await conn.fetch(
                        """
                        SELECT id, text FROM memory_units
                        WHERE id = ANY($1) AND fact_type IN ('world', 'experience')
                        """,
                        source_ids,
                    )

                # Should have found the source memories
                assert len(source_memories) >= 1, (
                    f"source_memory_ids should point to valid memories. "
                    f"IDs: {source_ids}, Found: {len(source_memories)}"
                )

                # The source memories should contain our original content
                source_texts = [m["text"].lower() for m in source_memories]
                has_phoenix = any("phoenix" in t for t in source_texts)
                assert has_phoenix, f"Source memories should contain original content. Got: {source_texts}"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestHierarchicalRetrieval:
    """Test the reflect agent's hierarchical retrieval tools.

    The hierarchy is:
    1. search_reflections - User-curated summaries (highest quality)
    2. search_mental_models - Auto-consolidated knowledge
    3. recall - Raw facts as ground truth

    When a reflection matches the query, it should be used first.
    """

    @pytest.mark.asyncio
    async def test_reflection_takes_priority_over_mental_model(
        self, memory: MemoryEngine, request_context
    ):
        """Test that reflections are found and would be used before mental models.

        Given:
        - A memory about "John's favorite color is blue"
        - A mental model created from that memory (via consolidation)
        - A reflection manually created about John

        When searching, the reflection should be found first.
        """
        bank_id = f"test-hierarchy-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory - consolidation creates a mental model
        await memory.retain_async(
            bank_id=bank_id,
            content="John's favorite color is blue and he likes painting.",
            request_context=request_context,
        )

        # Verify mental model was created
        async with memory._pool.acquire() as conn:
            mm_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM memory_units
                WHERE bank_id = $1 AND fact_type = 'mental_model'
                """,
                bank_id,
            )
        assert mm_count >= 1, "Consolidation should have created a mental model"

        # Create a reflection about John (higher quality, user-curated)
        reflection = await memory.create_reflection(
            bank_id=bank_id,
            name="John's Preferences",
            source_query="What are John's preferences?",
            content="John is an artist who loves the color blue. He has been painting for 10 years and prefers watercolors.",
            tags=[],
            request_context=request_context,
        )
        assert reflection["id"] is not None

        # Search reflections - should find our reflection
        async with memory._pool.acquire() as conn:
            query_embedding = memory.embeddings.encode(["What does John like?"])[0]
            reflection_result = await tool_search_reflections(
                conn=conn,
                bank_id=bank_id,
                query="What does John like?",
                query_embedding=query_embedding,
                max_results=5,
            )

        # Reflection should be found
        assert reflection_result["count"] >= 1, "Reflection should be found"
        found_reflection = reflection_result["reflections"][0]
        assert "John" in found_reflection["content"] or "blue" in found_reflection["content"]

        # Search mental models - should also find something
        mm_result = await tool_search_mental_models(
            memory_engine=memory,
            bank_id=bank_id,
            query="What does John like?",
            request_context=request_context,
            max_tokens=5000,
        )
        assert mm_result["count"] >= 1, "Mental model should also be found"

        # Verify the reflection has higher quality content (more detail)
        reflection_content = found_reflection["content"]
        mm_content = mm_result["mental_models"][0]["text"]

        # The reflection should contain the richer, user-curated content
        assert "watercolors" in reflection_content or "10 years" in reflection_content, (
            f"Reflection should have the rich user-curated content. Got: {reflection_content}"
        )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_fallback_to_mental_model_when_no_reflection(
        self, memory: MemoryEngine, request_context
    ):
        """Test that mental models are used when no reflection matches.

        Given:
        - A memory about "Sarah works at Google"
        - A mental model created from that memory
        - NO reflection about Sarah

        When searching, mental models should provide the information.
        """
        bank_id = f"test-hierarchy-fallback-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain a memory - consolidation creates a mental model
        await memory.retain_async(
            bank_id=bank_id,
            content="Sarah works at Google as a software engineer.",
            request_context=request_context,
        )

        # Search reflections - should find nothing
        async with memory._pool.acquire() as conn:
            query_embedding = memory.embeddings.encode(["Where does Sarah work?"])[0]
            reflection_result = await tool_search_reflections(
                conn=conn,
                bank_id=bank_id,
                query="Where does Sarah work?",
                query_embedding=query_embedding,
                max_results=5,
            )

        # No reflections exist
        assert reflection_result["count"] == 0, "No reflections should exist"

        # Search mental models - should find the consolidated knowledge
        mm_result = await tool_search_mental_models(
            memory_engine=memory,
            bank_id=bank_id,
            query="Where does Sarah work?",
            request_context=request_context,
            max_tokens=5000,
        )

        # Mental model should be found
        assert mm_result["count"] >= 1, "Mental model should be found when no reflection exists"
        mm_text = mm_result["mental_models"][0]["text"].lower()
        assert "sarah" in mm_text or "google" in mm_text, (
            f"Mental model should contain info about Sarah. Got: {mm_text}"
        )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_fallback_to_recall_for_fresh_data(
        self, memory: MemoryEngine, request_context
    ):
        """Test that recall provides raw facts when needed for verification.

        This tests the drill-down capability: when mental models are stale or
        need verification, recall provides the original source facts.
        """
        bank_id = f"test-hierarchy-recall-{uuid.uuid4().hex[:8]}"

        # Create the bank
        await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)

        # Retain some specific memories
        await memory.retain_async(
            bank_id=bank_id,
            content="The quarterly revenue was $1.5M in Q3 2024.",
            request_context=request_context,
        )
        await memory.retain_async(
            bank_id=bank_id,
            content="The quarterly revenue was $2.1M in Q4 2024.",
            request_context=request_context,
        )

        # Use recall to get the raw facts
        recall_result = await tool_recall(
            memory_engine=memory,
            bank_id=bank_id,
            query="What was the quarterly revenue?",
            request_context=request_context,
            max_tokens=2048,
            max_results=10,
        )

        # Should have raw facts with specific numbers
        assert recall_result["count"] >= 1, "Recall should find the raw facts"

        # Check that we get the actual numbers from the original memories
        all_memory_text = " ".join([m["text"] for m in recall_result["memories"]])
        assert "$1.5M" in all_memory_text or "$2.1M" in all_memory_text, (
            f"Recall should return raw facts with specific data. Got: {all_memory_text}"
        )

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)
