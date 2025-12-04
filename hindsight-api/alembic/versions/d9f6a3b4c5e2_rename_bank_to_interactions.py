"""Rename fact_type 'bank' to 'interactions'

Revision ID: d9f6a3b4c5e2
Revises: c8e5f2a3b4d1
Create Date: 2024-12-04 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9f6a3b4c5e2'
down_revision = 'c8e5f2a3b4d1'
branch_labels = None
depends_on = None


def upgrade():
    # Update existing 'bank' values to 'interactions'
    op.execute("UPDATE memory_units SET fact_type = 'interactions' WHERE fact_type = 'bank'")

    # Drop old check constraint
    op.drop_constraint('memory_units_fact_type_check', 'memory_units', type_='check')

    # Create new check constraint with 'interactions' instead of 'bank'
    op.create_check_constraint(
        'memory_units_fact_type_check',
        'memory_units',
        "fact_type IN ('world', 'interactions', 'opinion', 'observation')"
    )


def downgrade():
    # Update 'interactions' back to 'bank'
    op.execute("UPDATE memory_units SET fact_type = 'bank' WHERE fact_type = 'interactions'")

    # Drop new check constraint
    op.drop_constraint('memory_units_fact_type_check', 'memory_units', type_='check')

    # Recreate old check constraint
    op.create_check_constraint(
        'memory_units_fact_type_check',
        'memory_units',
        "fact_type IN ('world', 'bank', 'opinion', 'observation')"
    )
