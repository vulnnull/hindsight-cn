"""merge agents and temporal ranges branches

Revision ID: 217b2227771f
Revises: 3b9c4d8e7f21, 9d42e6f91234
Create Date: 2025-11-17 14:59:01.254543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '217b2227771f'
down_revision: Union[str, Sequence[str], None] = ('3b9c4d8e7f21', '9d42e6f91234')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
