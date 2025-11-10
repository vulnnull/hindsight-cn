"""
Alembic environment configuration for SQLAlchemy with pgvector.
Uses synchronous psycopg2 driver for migrations to avoid pgbouncer issues.
"""
import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection

from alembic import context
from dotenv import load_dotenv

# Import your models here
from memora.models import Base

# Load environment variables based on DATABASE_URL env var or default to local
def load_env():
    """Load environment variables from .env.local or .env.dev"""
    # Check if DATABASE_URL is already set (e.g., by CI/CD)
    if os.getenv("DATABASE_URL"):
        return

    # Look for .env files in the parent directory (root of the workspace)
    root_dir = Path(__file__).parent.parent.parent

    # Default to local environment
    env_file = root_dir / ".env.local"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Fallback to dev
        env_file = root_dir / ".env.dev"
        if env_file.exists():
            load_dotenv(env_file)

load_env()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")

# For migrations, use psycopg2 (sync driver) to avoid pgbouncer prepared statement issues
# The application uses asyncpg, but migrations work better with psycopg2
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
elif database_url.startswith("postgres+asyncpg://"):
    database_url = database_url.replace("postgres+asyncpg://", "postgresql://", 1)

# Override the sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with synchronous engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
