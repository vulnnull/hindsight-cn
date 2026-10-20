"""Repair: widen the columns that reference ``mental_models.id``.

``mental_models.id`` is ``TEXT`` on PostgreSQL since ``m8h9i0j1k2l3`` and
``VARCHAR2(256)`` on Oracle, but two columns pointing at it were created
narrower:

- ``mental_model_history.mental_model_id`` — ``VARCHAR(64)`` on PG
- ``knowledge_pages.mental_model_id`` — ``VARCHAR(64)`` on PG, ``VARCHAR2(64)``
  on Oracle

So a mental model with an id over 64 characters could be created but never
refreshed: every history-row insert failed with ``value too long``. See
https://github.com/vectorize-io/hindsight/issues/5788.

The original ``CREATE TABLE`` DDL is corrected for fresh installs; this widens
the columns on deployments that already ran it. Widening is a no-op on a column
that already has the target type, so every path converges.

Revision ID: f2a9c4e7b1d3
Revises: e8c1a4f7b2d9
Create Date: 2026-10-19
"""

from collections.abc import Sequence

from alembic import context, op

from hindsight_api.alembic._dialect import run_for_dialect

revision: str = "f2a9c4e7b1d3"
down_revision: str | Sequence[str] | None = "e8c1a4f7b2d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_schema_prefix() -> str:
    """Schema-qualifier for raw SQL on PG (multi-tenant search_path)."""
    schema = context.config.get_main_option("target_schema")
    return f'"{schema}".' if schema else ""


def _pg_upgrade() -> None:
    schema = _get_schema_prefix()
    op.execute(f"ALTER TABLE {schema}mental_model_history ALTER COLUMN mental_model_id TYPE TEXT")
    op.execute(f"ALTER TABLE {schema}knowledge_pages ALTER COLUMN mental_model_id TYPE TEXT")


def _oracle_upgrade() -> None:
    # mental_model_history.mental_model_id is already VARCHAR2(256) on Oracle.
    op.execute("ALTER TABLE knowledge_pages MODIFY (mental_model_id VARCHAR2(256))")


def _noop_downgrade() -> None:
    # Narrowing back could truncate real ids and would bring the bug back.
    pass


def upgrade() -> None:
    run_for_dialect(pg=_pg_upgrade, oracle=_oracle_upgrade)


def downgrade() -> None:
    run_for_dialect(pg=_noop_downgrade, oracle=_noop_downgrade)
