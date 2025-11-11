"""
Database migration management using Alembic.

This module provides programmatic access to run database migrations
on application startup. It is designed to be safe for concurrent
execution - Alembic uses PostgreSQL transactions to prevent
conflicts when multiple instances start simultaneously.

Important: All migrations must be backward-compatible to allow
safe rolling deployments.
"""
import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def run_migrations(database_url: str) -> None:
    """
    Run database migrations to the latest version.

    This function is safe to call on every application startup:
    - Alembic checks the current schema version in the database
    - Only missing migrations are applied
    - PostgreSQL transactions prevent concurrent migration conflicts
    - If schema is already up-to-date, this is a fast no-op

    Raises:
        RuntimeError: If migrations fail to complete
        FileNotFoundError: If alembic.ini is not found
    """
    try:
        # Find alembic.ini - it should be at the project root
        # This file is in: memora/memora/migrations.py
        # Project root is: memora/
        project_root = Path(__file__).parent.parent
        alembic_ini = project_root / "alembic.ini"

        if not alembic_ini.exists():
            raise FileNotFoundError(
                f"alembic.ini not found at {alembic_ini}. "
                "Database migrations cannot be run."
            )

        logger.info(f"Running database migrations to head...")
        logger.info(f"Database URL: {database_url}")

        # Create Alembic configuration from ini file
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        # Run migrations to head (latest version)
        # Note: Alembic may call sys.exit() on errors instead of raising exceptions
        # We rely on the outer try/except and logging to catch issues
        command.upgrade(alembic_cfg, "head")

        logger.info("Database migrations completed successfully")

    except FileNotFoundError:
        logger.error("alembic.ini not found, database migrations cannot be run")
        raise
    except SystemExit as e:
        # Catch sys.exit() calls from Alembic
        logger.error(f"Alembic called sys.exit() with code: {e.code}", exc_info=True)
        raise RuntimeError(f"Database migration failed with exit code {e.code}") from e
    except Exception as e:
        logger.error(f"Failed to run database migrations: {e}", exc_info=True)
        raise RuntimeError("Database migration failed") from e


def check_migration_status() -> tuple[str | None, str | None]:
    """
    Check current database schema version and latest available version.

    Returns:
        Tuple of (current_revision, head_revision)
        Returns (None, None) if unable to determine versions
    """
    try:
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
        from sqlalchemy import create_engine

        database_url = os.getenv("MEMORA_API_DATABASE_URL")
        if not database_url:
            logger.warning("MEMORA_API_DATABASE_URL not set, cannot check migration status")
            return None, None

        # Get current revision from database
        engine = create_engine(database_url)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        # Get head revision from migration scripts
        project_root = Path(__file__).parent.parent
        alembic_ini = project_root / "alembic.ini"

        if not alembic_ini.exists():
            return current_rev, None

        alembic_cfg = Config(str(alembic_ini))
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()

        return current_rev, head_rev

    except Exception as e:
        logger.warning(f"Unable to check migration status: {e}")
        return None, None
