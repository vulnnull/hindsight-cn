"""
Pytest configuration and shared fixtures.
"""
import pytest
import pytest_asyncio
import os
import filelock
from pathlib import Path
from dotenv import load_dotenv
from hindsight_api import MemoryEngine, LLMConfig, SentenceTransformersEmbeddings
import asyncpg
from testcontainers.postgres import PostgresContainer

from hindsight_api.engine.cross_encoder import SentenceTransformersCrossEncoder
from hindsight_api.engine.query_analyzer import TransformerQueryAnalyzer


# Load environment variables from .env at the start of test session
def pytest_configure(config):
    """Load environment variables before running tests."""
    # Look for .env in the workspace root (two levels up from tests dir)
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"Warning: {env_file} not found, tests may fail without proper configuration")


@pytest.fixture(scope="session")
def postgres_container(tmp_path_factory, worker_id):
    """
    Start a postgres container shared across all test workers.
    Uses filelock to ensure only one worker starts the container.

    - worker_id == "master": running without -n (single process)
    - worker_id == "gw0", "gw1", etc.: running with -n (parallel workers)
    """
    # Get shared temp dir (same for all workers)
    if worker_id == "master":
        root_tmp_dir = tmp_path_factory.getbasetemp()
    else:
        root_tmp_dir = tmp_path_factory.getbasetemp().parent

    db_url_file = root_tmp_dir / "postgres_url"
    lock_file = root_tmp_dir / "postgres.lock"
    container = None

    with filelock.FileLock(str(lock_file)):
        if db_url_file.exists():
            # Another worker already started the container
            db_url = db_url_file.read_text()
        else:
            # First worker - start the container
            container = PostgresContainer("pgvector/pgvector:pg16")
            container.start()
            db_url = container.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
            db_url_file.write_text(db_url)

            # Run migrations
            from hindsight_api.migrations import run_migrations
            run_migrations(db_url)

    os.environ["HINDSIGHT_API_DATABASE_URL"] = db_url
    yield db_url

    # Only the worker that started the container stops it
    if container is not None:
        container.stop()


@pytest.fixture(scope="session")
def llm_config():
    """
    Provide LLM configuration for tests.
    This can be used by tests that need to call LLM directly without memory system.
    """
    return LLMConfig.for_memory()


@pytest.fixture(scope="session")
def embeddings():

    return SentenceTransformersEmbeddings("BAAI/bge-small-en-v1.5")



@pytest.fixture(scope="session")
def cross_encoder():

    return SentenceTransformersCrossEncoder()

@pytest.fixture(scope="session")
def query_analyzer():
    return TransformerQueryAnalyzer()




@pytest_asyncio.fixture(scope="function")
async def memory(postgres_container, embeddings, cross_encoder, query_analyzer):
    """
    Provide a MemoryEngine instance for each test.

    Must be function-scoped because:
    1. pytest-xdist runs tests in separate processes with different event loops
    2. asyncpg pools are bound to the event loop that created them
    3. Each test needs its own pool in its own event loop

    Uses small pool sizes since tests run in parallel and share a single
    testcontainer PostgreSQL instance with limited resources.
    """
    mem = MemoryEngine(
        db_url=postgres_container,
        memory_llm_provider=os.getenv("HINDSIGHT_API_LLM_PROVIDER", "groq"),
        memory_llm_api_key=os.getenv("HINDSIGHT_API_LLM_API_KEY"),
        memory_llm_model=os.getenv("HINDSIGHT_API_LLM_MODEL", "openai/gpt-oss-120b"),
        memory_llm_base_url=os.getenv("HINDSIGHT_API_LLM_BASE_URL") or None,
        embeddings=embeddings,
        cross_encoder=cross_encoder,
        query_analyzer=query_analyzer,
        pool_min_size=1,
        pool_max_size=5,
    )
    await mem.initialize()
    yield mem
    try:
        if mem._pool and not mem._pool._closing:
            await mem.close()
    except Exception:
        pass