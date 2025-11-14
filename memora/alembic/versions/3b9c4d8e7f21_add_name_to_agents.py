"""add_name_to_agents

Revision ID: 3b9c4d8e7f21
Revises: 1680fc9768b4
Create Date: 2025-11-13 14:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b9c4d8e7f21'
down_revision: Union[str, Sequence[str], None] = '1680fc9768b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add name column to agents table
    op.execute("""
        ALTER TABLE agents
        ADD COLUMN name TEXT NOT NULL DEFAULT ''
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove name column from agents table
    op.execute("""
        ALTER TABLE agents
        DROP COLUMN name
    """)
