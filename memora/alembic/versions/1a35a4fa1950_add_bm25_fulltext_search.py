"""add_bm25_fulltext_search

Revision ID: 1a35a4fa1950
Revises: 01f989db9079
Create Date: 2025-11-06 11:19:48.627698

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a35a4fa1950'
down_revision: Union[str, Sequence[str], None] = '01f989db9079'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add tsvector column for full-text search
    op.execute("""
        ALTER TABLE memory_units
        ADD COLUMN search_vector tsvector
    """)

    # Populate tsvector with existing data (text + context combined)
    op.execute("""
        UPDATE memory_units
        SET search_vector =
            setweight(to_tsvector('english', COALESCE(text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(context, '')), 'B')
    """)

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX idx_memory_units_search_vector
        ON memory_units
        USING GIN(search_vector)
    """)

    # Create trigger to auto-update tsvector on INSERT/UPDATE
    op.execute("""
        CREATE OR REPLACE FUNCTION memory_units_search_vector_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.text, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.context, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_memory_units_search_vector
        BEFORE INSERT OR UPDATE ON memory_units
        FOR EACH ROW
        EXECUTE FUNCTION memory_units_search_vector_trigger();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_memory_units_search_vector ON memory_units")
    op.execute("DROP FUNCTION IF EXISTS memory_units_search_vector_trigger()")

    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_memory_units_search_vector")

    # Drop column
    op.execute("ALTER TABLE memory_units DROP COLUMN IF EXISTS search_vector")
