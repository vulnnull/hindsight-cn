"""
Tests for admin backup and restore functionality.

Note: These tests run sequentially (not in parallel) because they all
manipulate the same database and do full backup/restore operations.
"""

import tempfile
import uuid
import zipfile
from pathlib import Path

import pytest

from hindsight_api import RequestContext
from hindsight_api.admin.cli import _backup, _restore, BACKUP_TABLES


# Run these tests sequentially since they do full DB backup/restore
pytestmark = pytest.mark.xdist_group(name="backup_restore")


@pytest.mark.asyncio
async def test_backup_restore_roundtrip(memory, pg0_db_url, request_context):
    """Test that backup and restore preserves all data correctly."""
    # Use unique bank ID to avoid conflicts
    bank_id = f"test-backup-{uuid.uuid4().hex[:8]}"

    # Create some test data
    await memory.retain_batch_async(
        bank_id=bank_id,
        contents=[
            {"content": "Alice is a software engineer who loves Python."},
            {"content": "Bob works with Alice on the backend team."},
            {"content": "The team uses PostgreSQL for their database."},
        ],
        request_context=request_context,
    )

    # Get counts before backup
    async with memory._pool.acquire() as conn:
        counts_before = {}
        for table in BACKUP_TABLES:
            counts_before[table] = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")

    # Verify we have data
    assert counts_before["banks"] > 0
    assert counts_before["memory_units"] > 0

    # Backup to a temp file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        backup_path = Path(f.name)

    try:
        manifest = await _backup(pg0_db_url, backup_path)

        # Verify backup file exists and is valid
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0

        # Verify manifest
        assert manifest["version"] == "1"
        assert "created_at" in manifest
        for table in BACKUP_TABLES:
            assert table in manifest["tables"]
            assert manifest["tables"][table]["rows"] == counts_before[table]

        # Verify zip contents
        with zipfile.ZipFile(backup_path, "r") as zf:
            assert "manifest.json" in zf.namelist()
            for table in BACKUP_TABLES:
                assert f"{table}.bin" in zf.namelist()

        # Clear all data
        async with memory._pool.acquire() as conn:
            for table in reversed(BACKUP_TABLES):
                await conn.execute(f"TRUNCATE TABLE {table} CASCADE")

        # Verify data is gone
        async with memory._pool.acquire() as conn:
            for table in BACKUP_TABLES:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                assert count == 0, f"Table {table} should be empty after truncate"

        # Restore from backup
        await _restore(pg0_db_url, backup_path)

        # Verify counts match original
        async with memory._pool.acquire() as conn:
            for table in BACKUP_TABLES:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                assert count == counts_before[table], f"Table {table} count mismatch after restore"

        # Verify data content is preserved
        async with memory._pool.acquire() as conn:
            texts = await conn.fetch(
                "SELECT text FROM memory_units WHERE bank_id = $1",
                bank_id,
            )
            text_content = " ".join(r["text"] for r in texts)
            assert "Alice" in text_content or "software" in text_content

    finally:
        # Cleanup
        if backup_path.exists():
            backup_path.unlink()


@pytest.mark.asyncio
async def test_backup_restore_preserves_all_column_types(memory, pg0_db_url, request_context):
    """Test that all column types are preserved: vectors, UUIDs, timestamps, JSONB."""
    # Use unique bank ID
    bank_id = f"test-types-{uuid.uuid4().hex[:8]}"

    # Create data with meaningful content that will produce facts
    await memory.retain_batch_async(
        bank_id=bank_id,
        contents=[
            {"content": "John Smith is a senior engineer at Acme Corp since 2020."},
            {"content": "The project deadline is December 15th 2024."},
        ],
        request_context=request_context,
    )

    # Get original data with all important column types
    async with memory._pool.acquire() as conn:
        # memory_units: UUID (id), Vector (embedding), Timestamp (event_date, created_at), JSONB (metadata)
        original_unit = await conn.fetchrow(
            """SELECT id, embedding, event_date, created_at, metadata, text
               FROM memory_units WHERE bank_id = $1 LIMIT 1""",
            bank_id,
        )

        # entities: UUID (id), Timestamp (first_seen, last_seen), JSONB (metadata)
        original_entity = await conn.fetchrow(
            """SELECT id, first_seen, last_seen, metadata, canonical_name
               FROM entities WHERE bank_id = $1 LIMIT 1""",
            bank_id,
        )

        # banks: JSONB (personality/disposition)
        original_bank = await conn.fetchrow(
            "SELECT bank_id, created_at, updated_at FROM banks WHERE bank_id = $1",
            bank_id,
        )

    assert original_unit is not None, "Should have created memory units"
    assert original_unit["embedding"] is not None, "Should have embedding"
    assert original_unit["id"] is not None, "Should have UUID"
    assert original_entity is not None, "Should have created entities"

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        backup_path = Path(f.name)

    try:
        await _backup(pg0_db_url, backup_path)

        # Clear all data
        async with memory._pool.acquire() as conn:
            for table in reversed(BACKUP_TABLES):
                await conn.execute(f"TRUNCATE TABLE {table} CASCADE")

        await _restore(pg0_db_url, backup_path)

        # Verify all column types are preserved exactly
        async with memory._pool.acquire() as conn:
            restored_unit = await conn.fetchrow(
                """SELECT id, embedding, event_date, created_at, metadata, text
                   FROM memory_units WHERE bank_id = $1 LIMIT 1""",
                bank_id,
            )

            restored_entity = await conn.fetchrow(
                """SELECT id, first_seen, last_seen, metadata, canonical_name
                   FROM entities WHERE bank_id = $1 LIMIT 1""",
                bank_id,
            )

            restored_bank = await conn.fetchrow(
                "SELECT bank_id, created_at, updated_at FROM banks WHERE bank_id = $1",
                bank_id,
            )

        # Verify memory_units
        assert restored_unit is not None, "Should have restored memory unit"
        assert restored_unit["id"] == original_unit["id"], "UUID should match exactly"
        assert restored_unit["text"] == original_unit["text"], "Text should match"
        assert list(restored_unit["embedding"]) == list(original_unit["embedding"]), "Vector embedding should match exactly"
        assert restored_unit["event_date"] == original_unit["event_date"], "Timestamp should match exactly"
        assert restored_unit["created_at"] == original_unit["created_at"], "Created timestamp should match"
        assert restored_unit["metadata"] == original_unit["metadata"], "JSONB metadata should match"

        # Verify entities
        assert restored_entity is not None, "Should have restored entity"
        assert restored_entity["id"] == original_entity["id"], "Entity UUID should match"
        assert restored_entity["canonical_name"] == original_entity["canonical_name"], "Entity name should match"
        assert restored_entity["first_seen"] == original_entity["first_seen"], "Entity first_seen should match"
        assert restored_entity["last_seen"] == original_entity["last_seen"], "Entity last_seen should match"
        assert restored_entity["metadata"] == original_entity["metadata"], "Entity metadata should match"

        # Verify banks
        assert restored_bank is not None, "Should have restored bank"
        assert restored_bank["bank_id"] == original_bank["bank_id"], "Bank ID should match"
        assert restored_bank["created_at"] == original_bank["created_at"], "Bank created_at should match"

    finally:
        if backup_path.exists():
            backup_path.unlink()
