"""
Pytest configuration and fixtures for upgrade tests.
"""

import asyncio
import logging
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Reduce noise from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def pytest_configure(config):
    """Load environment variables before running tests."""
    # Look for .env in the workspace root
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)


_pg0_instance = None
_pg0_url = None


def _get_or_create_pg0():
    """Get or create the shared pg0 instance for upgrade tests."""
    global _pg0_instance, _pg0_url
    from hindsight_api.pg0 import EmbeddedPostgres

    if _pg0_instance is None:
        _pg0_instance = EmbeddedPostgres(name="hindsight-upgrade-test", port=5560)

    loop = asyncio.new_event_loop()
    try:
        _pg0_url = loop.run_until_complete(_pg0_instance.ensure_running())
    finally:
        loop.close()

    return _pg0_url


def _clean_database(db_url: str):
    """Drop all tables in the database to reset state for next test."""
    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Drop all tables in public schema (cascade to handle foreign keys)
        tables = conn.execute(
            text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename NOT LIKE 'pg_%'
            """)
        ).fetchall()
        for table in tables:
            conn.execute(text(f'DROP TABLE IF EXISTS public."{table[0]}" CASCADE'))
        conn.commit()
    engine.dispose()


@pytest.fixture(scope="function")
def db_url():
    """
    Provide a PostgreSQL connection URL for upgrade tests.

    Uses pg0 (embedded PostgreSQL) for a clean, isolated test database.
    The database is cleaned between tests to ensure fresh state for migrations.
    """
    url = _get_or_create_pg0()

    # Clean database before each test
    _clean_database(url)

    yield url

    # No cleanup after - database is cleaned at start of next test


@pytest.fixture(scope="module")
def llm_config():
    """
    Provide LLM configuration from environment.

    Returns a dict with provider, api_key, and model.
    """
    return {
        "provider": os.getenv("HINDSIGHT_API_LLM_PROVIDER", "groq"),
        "api_key": os.getenv("HINDSIGHT_API_LLM_API_KEY") or os.getenv("GROQ_API_KEY"),
        "model": os.getenv("HINDSIGHT_API_LLM_MODEL", "llama-3.3-70b-versatile"),
    }


@pytest.fixture
def unique_bank_id():
    """Generate a unique bank ID for each test."""
    import uuid

    return f"upgrade_test_{uuid.uuid4().hex[:8]}"
