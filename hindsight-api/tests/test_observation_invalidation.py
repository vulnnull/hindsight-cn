"""
Tests for observation invalidation when source memories are deleted.

These tests verify that:
1. Observations are deleted (not just updated) when their source memories are removed
2. Remaining source memories are reset for re-consolidation (consolidated_at=NULL)
3. The clear_observations_for_memory method correctly clears observations and
   resets the target memory itself for re-consolidation
4. delete_bank(fact_type=...) also cleans up affected observations
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from hindsight_api import RequestContext
from hindsight_api.engine.memory_engine import MemoryEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _insert_memory(conn, bank_id: str, text: str, fact_type: str = "experience") -> uuid.UUID:
    """Insert a memory unit directly, bypassing LLM retain pipeline."""
    mem_id = uuid.uuid4()
    await conn.execute(
        """
        INSERT INTO memory_units (id, bank_id, text, fact_type, event_date, created_at, updated_at, consolidated_at)
        VALUES ($1, $2, $3, $4, NOW(), NOW(), NOW(), NOW())
        """,
        mem_id,
        bank_id,
        text,
        fact_type,
    )
    return mem_id


async def _insert_observation(
    conn, bank_id: str, text: str, source_memory_ids: list[uuid.UUID]
) -> uuid.UUID:
    """Insert an observation unit directly."""
    obs_id = uuid.uuid4()
    await conn.execute(
        """
        INSERT INTO memory_units (
            id, bank_id, text, fact_type, event_date, source_memory_ids, proof_count, created_at, updated_at
        ) VALUES ($1, $2, $3, 'observation', NOW(), $4, $5, NOW(), NOW())
        """,
        obs_id,
        bank_id,
        text,
        source_memory_ids,
        len(source_memory_ids),
    )
    return obs_id


async def _get_observation_ids(conn, bank_id: str) -> list[str]:
    rows = await conn.fetch(
        "SELECT id FROM memory_units WHERE bank_id = $1 AND fact_type = 'observation'",
        bank_id,
    )
    return [str(r["id"]) for r in rows]


async def _get_consolidated_at(conn, memory_id: uuid.UUID):
    return await conn.fetchval(
        "SELECT consolidated_at FROM memory_units WHERE id = $1",
        memory_id,
    )


async def _ensure_bank(memory: MemoryEngine, bank_id: str, request_context: RequestContext):
    await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)


# ---------------------------------------------------------------------------
# Tests: delete_memory_unit
# ---------------------------------------------------------------------------

class TestDeleteMemoryUnitObservationCleanup:

    @pytest.mark.asyncio
    async def test_deleting_source_memory_removes_observation(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Deleting a source memory removes observations derived from it."""
        bank_id = f"test-invalidate-del-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            m2 = await _insert_memory(conn, bank_id, "Alice goes hiking every weekend.")
            obs_id = await _insert_observation(conn, bank_id, "Alice enjoys hiking regularly.", [m1, m2])

        await memory.delete_memory_unit(str(m1), request_context=request_context)

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) not in obs_ids, "Observation should have been deleted"

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_deleting_source_memory_resets_remaining_source_consolidated_at(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """After deleting a source memory, remaining source memories are reset for re-consolidation."""
        bank_id = f"test-invalidate-reset-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            m2 = await _insert_memory(conn, bank_id, "Alice goes hiking every weekend.")
            await _insert_observation(conn, bank_id, "Alice enjoys hiking regularly.", [m1, m2])

            # Verify m2 starts with consolidated_at set
            assert await _get_consolidated_at(conn, m2) is not None

        # Patch out consolidation so it doesn't re-set consolidated_at before we can check it
        with patch.object(memory, "submit_async_consolidation", new=AsyncMock()):
            await memory.delete_memory_unit(str(m1), request_context=request_context)

        async with pool.acquire() as conn:
            # m2 should have consolidated_at reset to NULL
            consolidated_at = await _get_consolidated_at(conn, m2)
            assert consolidated_at is None, "Remaining source memory should be reset for re-consolidation"

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_deleting_non_source_memory_leaves_observations_intact(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Deleting a memory that is not a source of any observation leaves observations unchanged."""
        bank_id = f"test-invalidate-noop-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            m2 = await _insert_memory(conn, bank_id, "Alice goes hiking every weekend.")
            unrelated = await _insert_memory(conn, bank_id, "Bob likes cycling.")
            obs_id = await _insert_observation(conn, bank_id, "Alice enjoys hiking regularly.", [m1, m2])

        await memory.delete_memory_unit(str(unrelated), request_context=request_context)

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) in obs_ids, "Observation should remain untouched"
            # m1 and m2 should still be consolidated
            assert await _get_consolidated_at(conn, m1) is not None
            assert await _get_consolidated_at(conn, m2) is not None

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_deleting_sole_source_memory_removes_observation_no_remaining_reset(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """When an observation has only one source and it's deleted, observation is removed with no remaining memories to reset."""
        bank_id = f"test-invalidate-sole-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            obs_id = await _insert_observation(conn, bank_id, "Alice enjoys hiking.", [m1])

        await memory.delete_memory_unit(str(m1), request_context=request_context)

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) not in obs_ids, "Observation should have been deleted"

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_deleting_observation_type_memory_does_not_trigger_invalidation(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Deleting a memory with fact_type='observation' directly does not trigger invalidation logic."""
        bank_id = f"test-invalidate-obstype-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            obs_id = await _insert_observation(conn, bank_id, "Alice enjoys hiking.", [m1])

        # Delete the observation directly (not the source memory)
        await memory.delete_memory_unit(str(obs_id), request_context=request_context)

        async with pool.acquire() as conn:
            # Source memory should still be consolidated (not reset)
            assert await _get_consolidated_at(conn, m1) is not None
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) not in obs_ids

        await memory.delete_bank(bank_id, request_context=request_context)


# ---------------------------------------------------------------------------
# Tests: delete_document
# ---------------------------------------------------------------------------

class TestDeleteDocumentObservationCleanup:

    @pytest.mark.asyncio
    async def test_deleting_document_removes_observations(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Deleting a document removes observations derived from its memory units."""
        bank_id = f"test-invalidate-doc-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()

        # Create a document and attach memories to it
        async with pool.acquire() as conn:
            doc_id = str(uuid.uuid4())  # documents.id is TEXT
            await conn.execute(
                """
                INSERT INTO documents (id, bank_id, original_text, content_hash, created_at, updated_at)
                VALUES ($1, $2, 'some doc', 'hash123', NOW(), NOW())
                """,
                doc_id,
                bank_id,
            )
            m1 = uuid.uuid4()
            m2 = uuid.uuid4()
            for mem_id, text in [(m1, "Alice loves hiking."), (m2, "Alice goes hiking every weekend.")]:
                await conn.execute(
                    """
                    INSERT INTO memory_units (id, bank_id, text, fact_type, event_date, document_id, created_at, updated_at, consolidated_at)
                    VALUES ($1, $2, $3, 'experience', NOW(), $4, NOW(), NOW(), NOW())
                    """,
                    mem_id,
                    bank_id,
                    text,
                    doc_id,
                )

            # Standalone memory (not in document)
            m3 = await _insert_memory(conn, bank_id, "Alice is an avid outdoor person.")

            # Observation referencing both doc memories and the standalone memory
            obs_id = await _insert_observation(
                conn, bank_id, "Alice enjoys outdoor activities.", [m1, m2, m3]
            )

        # Patch out consolidation so it doesn't re-set consolidated_at before we can check it
        with patch.object(memory, "submit_async_consolidation", new=AsyncMock()):
            await memory.delete_document(str(doc_id), bank_id, request_context=request_context)

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) not in obs_ids, "Observation should have been deleted"

            # m3 (remaining source) should be reset for re-consolidation
            consolidated_at = await _get_consolidated_at(conn, m3)
            assert consolidated_at is None, "Remaining source memory should be reset"

        await memory.delete_bank(bank_id, request_context=request_context)


# ---------------------------------------------------------------------------
# Tests: delete_bank with fact_type filter
# ---------------------------------------------------------------------------

class TestDeleteBankByTypeObservationCleanup:

    @pytest.mark.asyncio
    async def test_clearing_experience_memories_removes_affected_observations(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Clearing all experience memories removes observations sourced from them."""
        bank_id = f"test-invalidate-banktype-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            exp1 = await _insert_memory(conn, bank_id, "Alice went hiking last week.", "experience")
            world1 = await _insert_memory(conn, bank_id, "Alice is a hiker.", "world")
            obs_id = await _insert_observation(
                conn, bank_id, "Alice is a regular hiker.", [exp1, world1]
            )

        # Patch out consolidation so it doesn't re-set consolidated_at before we can check it
        with patch.object(memory, "submit_async_consolidation", new=AsyncMock()):
            await memory.delete_bank(bank_id, fact_type="experience", request_context=request_context)

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) not in obs_ids, "Observation should have been deleted"

            # world1 (remaining source) should be reset for re-consolidation
            consolidated_at = await _get_consolidated_at(conn, world1)
            assert consolidated_at is None, "World memory should be reset for re-consolidation"

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_clearing_unrelated_type_leaves_observations_intact(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Clearing memories of a type that is not a source of any observation leaves observations untouched."""
        bank_id = f"test-invalidate-banktype-noop-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            world1 = await _insert_memory(conn, bank_id, "Alice is a hiker.", "world")
            obs_id = await _insert_observation(conn, bank_id, "Alice is a regular hiker.", [world1])

        # Deleting 'experience' type should not affect observations sourced only from 'world'
        await memory.delete_bank(bank_id, fact_type="experience", request_context=request_context)

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) in obs_ids, "Observation should remain untouched"

        await memory.delete_bank(bank_id, request_context=request_context)


# ---------------------------------------------------------------------------
# Tests: clear_observations_for_memory
# ---------------------------------------------------------------------------

class TestClearObservationsForMemory:

    @pytest.mark.asyncio
    async def test_clears_observations_and_resets_all_source_memories(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Clearing observations for a memory deletes them and resets all related source memories."""
        bank_id = f"test-clear-obs-mem-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            m2 = await _insert_memory(conn, bank_id, "Alice hikes every weekend.")
            obs_id = await _insert_observation(conn, bank_id, "Alice is an avid hiker.", [m1, m2])

        # Patch out consolidation so it doesn't re-set consolidated_at before we can check it
        with patch.object(memory, "submit_async_consolidation", new=AsyncMock()):
            result = await memory.clear_observations_for_memory(
                bank_id, str(m1), request_context=request_context
            )

        assert result["deleted_count"] == 1

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs_id) not in obs_ids, "Observation should be deleted"

            # Both m1 (target) and m2 (remaining source) should be reset
            assert await _get_consolidated_at(conn, m1) is None, "Target memory should be reset"
            assert await _get_consolidated_at(conn, m2) is None, "Remaining source should be reset"

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_no_observations_returns_zero(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Returns 0 when the memory has no associated observations."""
        bank_id = f"test-clear-obs-noop-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")

        result = await memory.clear_observations_for_memory(
            bank_id, str(m1), request_context=request_context
        )

        assert result["deleted_count"] == 0

        async with pool.acquire() as conn:
            # Memory should still be consolidated (no observations were cleared)
            assert await _get_consolidated_at(conn, m1) is not None

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_only_clears_observations_referencing_target_memory(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """Clearing observations for m1 does not affect observations that only reference m2."""
        bank_id = f"test-clear-obs-selective-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            m2 = await _insert_memory(conn, bank_id, "Alice hikes every weekend.")
            m3 = await _insert_memory(conn, bank_id, "Alice climbed a mountain.")

            obs1_id = await _insert_observation(conn, bank_id, "Alice is an avid hiker.", [m1, m2])
            obs2_id = await _insert_observation(conn, bank_id, "Alice is a mountaineer.", [m3])

        result = await memory.clear_observations_for_memory(
            bank_id, str(m1), request_context=request_context
        )

        assert result["deleted_count"] == 1

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs1_id) not in obs_ids, "obs1 (references m1) should be deleted"
            assert str(obs2_id) in obs_ids, "obs2 (does not reference m1) should remain"

            # m3 should still be consolidated
            assert await _get_consolidated_at(conn, m3) is not None

        await memory.delete_bank(bank_id, request_context=request_context)

    @pytest.mark.asyncio
    async def test_multiple_observations_for_same_memory_all_cleared(
        self, memory: MemoryEngine, request_context: RequestContext
    ):
        """All observations referencing the target memory are cleared in one call."""
        bank_id = f"test-clear-obs-multi-{uuid.uuid4().hex[:8]}"
        await _ensure_bank(memory, bank_id, request_context)

        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            m1 = await _insert_memory(conn, bank_id, "Alice loves hiking.")
            m2 = await _insert_memory(conn, bank_id, "Alice hikes every weekend.")

            obs1_id = await _insert_observation(conn, bank_id, "Alice hikes often.", [m1])
            obs2_id = await _insert_observation(conn, bank_id, "Alice is outdoorsy.", [m1, m2])

        # Patch out consolidation so it doesn't re-set consolidated_at before we can check it
        with patch.object(memory, "submit_async_consolidation", new=AsyncMock()):
            result = await memory.clear_observations_for_memory(
                bank_id, str(m1), request_context=request_context
            )

        assert result["deleted_count"] == 2

        async with pool.acquire() as conn:
            obs_ids = await _get_observation_ids(conn, bank_id)
            assert str(obs1_id) not in obs_ids
            assert str(obs2_id) not in obs_ids

            # m1 and m2 should both be reset
            assert await _get_consolidated_at(conn, m1) is None
            assert await _get_consolidated_at(conn, m2) is None

        await memory.delete_bank(bank_id, request_context=request_context)
