"""Fix memory_links entity_id to be nullable

Revision ID: 01f989db9079
Revises: af0413383b3e
Create Date: 2025-11-03 14:43:18.721430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01f989db9079'
down_revision: Union[str, Sequence[str], None] = 'af0413383b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing primary key
    op.execute('ALTER TABLE memory_links DROP CONSTRAINT memory_links_pkey')

    # Change entity_id to nullable
    op.alter_column('memory_links', 'entity_id',
                   existing_type=sa.UUID(),
                   nullable=True)

    # Create a unique index with COALESCE expression to handle NULL entity_id
    op.execute("""
        CREATE UNIQUE INDEX idx_memory_links_unique
        ON memory_links (from_unit_id, to_unit_id, link_type, COALESCE(entity_id, '00000000-0000-0000-0000-000000000000'::uuid))
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
