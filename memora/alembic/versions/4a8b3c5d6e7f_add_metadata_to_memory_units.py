"""add metadata to memory_units

Revision ID: 4a8b3c5d6e7f
Revises: 217b2227771f
Create Date: 2025-11-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4a8b3c5d6e7f'
down_revision: Union[str, Sequence[str], None] = '217b2227771f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add metadata column to memory_units table."""
    op.add_column(
        'memory_units',
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False)
    )


def downgrade() -> None:
    """Remove metadata column from memory_units table."""
    op.drop_column('memory_units', 'metadata')
