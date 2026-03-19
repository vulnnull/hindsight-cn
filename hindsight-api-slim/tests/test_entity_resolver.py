"""
Tests for EntityResolver edge cases.
"""

import uuid
from datetime import datetime, timezone

import asyncpg
import pytest

from hindsight_api.engine.entity_resolver import EntityResolver
from hindsight_api.pg0 import resolve_database_url


@pytest.mark.asyncio
async def test_resolve_entities_batch_handles_unicode_lower_conflicts(pg0_db_url):
    """
    Existing entities with PostgreSQL/Python lowercase mismatches should resolve
    to the conflicted row instead of leaving a missing entity_id.
    """
    resolved_url = await resolve_database_url(pg0_db_url)
    pool = await asyncpg.create_pool(resolved_url, min_size=1, max_size=2, command_timeout=30)
    bank_id = f"test-entity-resolver-{uuid.uuid4().hex[:8]}"
    event_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
    resolver = EntityResolver(pool=pool, entity_lookup="full")

    try:
        async with pool.acquire() as conn:
            existing_entity_id = await conn.fetchval(
                """
                INSERT INTO entities (bank_id, canonical_name, first_seen, last_seen, mention_count)
                VALUES ($1, $2, $3, $3, 1)
                RETURNING id
                """,
                bank_id,
                "İstanbul",
                event_date,
            )

            resolved_ids = await resolver.resolve_entities_batch(
                bank_id=bank_id,
                entities_data=[
                    {
                        "text": "istanbul",
                        "nearby_entities": [],
                        "event_date": event_date,
                    }
                ],
                context="unicode case mismatch",
                unit_event_date=event_date,
                conn=conn,
            )

            entity_rows = await conn.fetch(
                """
                SELECT id, canonical_name
                FROM entities
                WHERE bank_id = $1
                ORDER BY canonical_name
                """,
                bank_id,
            )

        assert resolved_ids == [existing_entity_id]
        assert len(entity_rows) == 1
        assert entity_rows[0]["id"] == existing_entity_id
        assert entity_rows[0]["canonical_name"] == "İstanbul"
    finally:
        await pool.execute("DELETE FROM entities WHERE bank_id = $1", bank_id)
        await pool.close()
