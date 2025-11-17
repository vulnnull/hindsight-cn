"""add_temporal_ranges_to_memory_units

Revision ID: 9d42e6f91234
Revises: 8c55f5602451
Create Date: 2025-11-17 00:00:00.000000

This migration adds temporal range support to memory_units table:
- occurred_start: When the fact/event started
- occurred_end: When the fact/event ended
- mentioned_at: When the fact was mentioned/learned

For existing rows, these are initialized from event_date (point events).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision: str = '9d42e6f91234'
down_revision: Union[str, Sequence[str], None] = '8c55f5602451'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add temporal range columns to memory_units."""

    # Add new temporal range columns (nullable initially)
    op.add_column(
        'memory_units',
        sa.Column('occurred_start', TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column(
        'memory_units',
        sa.Column('occurred_end', TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column(
        'memory_units',
        sa.Column('mentioned_at', TIMESTAMP(timezone=True), nullable=True)
    )

    # Populate new columns from existing event_date for backward compatibility
    # For existing facts, treat them as point events (start = end = event_date)
    # and assume they were mentioned at the same time
    op.execute("""
        UPDATE memory_units
        SET
            occurred_start = event_date,
            occurred_end = event_date,
            mentioned_at = event_date
        WHERE occurred_start IS NULL
    """)

    # Optional: Make columns non-nullable after populating
    # Uncomment if you want to enforce NOT NULL constraint
    # op.alter_column('memory_units', 'occurred_start', nullable=False)
    # op.alter_column('memory_units', 'occurred_end', nullable=False)
    # op.alter_column('memory_units', 'mentioned_at', nullable=False)


def downgrade() -> None:
    """Downgrade schema: remove temporal range columns from memory_units."""

    # Remove the temporal range columns
    op.drop_column('memory_units', 'mentioned_at')
    op.drop_column('memory_units', 'occurred_end')
    op.drop_column('memory_units', 'occurred_start')
