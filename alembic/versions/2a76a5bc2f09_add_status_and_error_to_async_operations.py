"""add_status_and_error_to_async_operations

Revision ID: 2a76a5bc2f09
Revises: 0e96398aae9e
Create Date: 2025-11-07 16:03:19.078561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a76a5bc2f09'
down_revision: Union[str, Sequence[str], None] = '0e96398aae9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add status column (default 'pending' for existing rows)
    op.execute("""
        ALTER TABLE async_operations
        ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'
    """)

    # Add error_message column
    op.execute("""
        ALTER TABLE async_operations
        ADD COLUMN error_message TEXT
    """)

    # Add index on status for filtering failed/pending operations
    op.execute("""
        CREATE INDEX idx_async_operations_status
        ON async_operations(status)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_async_operations_status")

    # Drop columns
    op.execute("ALTER TABLE async_operations DROP COLUMN IF EXISTS error_message")
    op.execute("ALTER TABLE async_operations DROP COLUMN IF EXISTS status")
