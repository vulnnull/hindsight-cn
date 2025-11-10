"""add_async_operations_table

Revision ID: 0e96398aae9e
Revises: 1a35a4fa1950
Create Date: 2025-11-07 14:54:21.224968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e96398aae9e'
down_revision: Union[str, Sequence[str], None] = '1a35a4fa1950'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create async_operations table
    op.execute("""
        CREATE TABLE async_operations (
            id UUID PRIMARY KEY,
            agent_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            items_count INTEGER NOT NULL,
            document_id TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)

    # Create index on agent_id for fast lookups by agent
    op.execute("""
        CREATE INDEX idx_async_operations_agent_id
        ON async_operations(agent_id)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_async_operations_agent_id")

    # Drop table
    op.execute("DROP TABLE IF EXISTS async_operations")
