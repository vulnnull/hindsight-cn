"""add_agents_table

Revision ID: 1680fc9768b4
Revises: 8c55f5602451
Create Date: 2025-11-12 16:18:06.620862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1680fc9768b4'
down_revision: Union[str, Sequence[str], None] = '8c55f5602451'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create agents table
    op.execute("""
        CREATE TABLE agents (
            agent_id TEXT PRIMARY KEY,
            personality JSONB NOT NULL DEFAULT '{"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5, "bias_strength": 0.5}'::jsonb,
            background TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)

    # Create index on agent_id for fast lookups
    op.execute("""
        CREATE INDEX idx_agents_agent_id
        ON agents(agent_id)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_agents_agent_id")

    # Drop table
    op.execute("DROP TABLE IF EXISTS agents")
