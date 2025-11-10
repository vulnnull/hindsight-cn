"""remove_entity_type_column

Revision ID: 8c55f5602451
Revises: 2a76a5bc2f09
Create Date: 2025-11-07 17:08:07.329740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c55f5602451'
down_revision: Union[str, Sequence[str], None] = '2a76a5bc2f09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove entity_type column from entities table
    op.execute("ALTER TABLE entities DROP COLUMN IF EXISTS entity_type")


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add entity_type column (default to 'OTHER' for existing rows)
    op.execute("ALTER TABLE entities ADD COLUMN entity_type TEXT DEFAULT 'OTHER'")
