"""rename_personality_to_disposition

Revision ID: rename_personality
Revises: d9f6a3b4c5e2
Create Date: 2024-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rename_personality'
down_revision: Union[str, Sequence[str], None] = 'd9f6a3b4c5e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename personality column to disposition in banks table (if it exists)."""
    # Check if 'personality' column exists before renaming
    # This handles both old databases (with personality) and new databases (with disposition)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'banks' AND column_name = 'personality'
    """))
    if result.fetchone():
        op.alter_column('banks', 'personality', new_column_name='disposition')


def downgrade() -> None:
    """Revert disposition column back to personality."""
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'banks' AND column_name = 'disposition'
    """))
    if result.fetchone():
        op.alter_column('banks', 'disposition', new_column_name='personality')
