"""
Pytest configuration and shared fixtures.
"""
import pytest
import pytest_asyncio
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from memora import TemporalSemanticMemory
from memora.llm_wrapper import LLMConfig
import asyncpg


# Force local database URL for all tests
LOCAL_DB_URL = "postgresql://memora:memora_dev@localhost:5432/memora"


# Load environment variables from .env.local at the start of test session
def pytest_configure(config):
    """Load environment variables before running tests."""
    # Look for .env.local in the workspace root (two levels up from tests dir)
    env_file = Path(__file__).parent.parent.parent / ".env.local"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"Warning: {env_file} not found, tests may fail without proper configuration")

    # Override DATABASE_URL to use local database
    os.environ["DATABASE_URL"] = LOCAL_DB_URL


@pytest.fixture(scope="session")
def llm_config():
    """
    Provide LLM configuration for tests.
    This can be used by tests that need to call LLM directly without memory system.
    """
    return LLMConfig.for_memory()


@pytest_asyncio.fixture(scope="function")
async def memory():
    """
    Provide a memory system instance for each test function.
    Forces the use of local database URL.

    Note: Using function scope to avoid event loop issues, but this means
    the embedding model will be loaded for each test (adds ~3 seconds per test).

    Tests should handle their own cleanup by calling memory.delete_agent(agent_id)
    in their finally blocks. The fixture will attempt cleanup as a safeguard.
    """
    mem = TemporalSemanticMemory(
        db_url=LOCAL_DB_URL,
        memory_llm_provider=os.getenv("MEMORY_LLM_PROVIDER", "groq"),
        memory_llm_api_key=os.getenv("MEMORY_LLM_API_KEY"),
        memory_llm_model=os.getenv("MEMORY_LLM_MODEL", "openai/gpt-oss-120b"),
        memory_llm_base_url=os.getenv("MEMORY_LLM_BASE_URL") or None,  # Use None to get provider defaults
    )
    await mem.initialize()
    yield mem
    # Attempt cleanup (tests should already have called close, but this is a safeguard)
    try:
        if mem._pool and not mem._pool._closing:
            await mem.close()
    except Exception as e:
        # Ignore errors during fixture cleanup since test may have already closed
        pass


@pytest_asyncio.fixture(scope="function")
async def clean_agent(memory):
    """
    Provide a clean agent ID and clean up data after test.
    Uses agent_id='test' for all tests (multi-tenant isolation).
    """
    agent_id = "test"

    # Clean up before test
    await memory.delete_agent(agent_id)

    yield agent_id

    # Clean up after test
    try:
        await memory.delete_agent(agent_id)
    except Exception as e:
        print(f"Warning: Error during agent cleanup: {e}")


@pytest_asyncio.fixture
async def db_connection():
    """
    Provide a database connection for direct DB queries in tests.
    Uses the forced local database URL.
    """
    conn = await asyncpg.connect(LOCAL_DB_URL, statement_cache_size=0)
    yield conn
    try:
        await conn.close()
    except Exception as e:
        print(f"Warning: Error closing connection: {e}")
