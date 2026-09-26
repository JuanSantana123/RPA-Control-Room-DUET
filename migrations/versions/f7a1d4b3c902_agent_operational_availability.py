"""add agent operational availability

Revision ID: f7a1d4b3c902
Revises: e42f6c19a7d1
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f7a1d4b3c902"
down_revision: str | None = "e42f6c19a7d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("accepting_work", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "agents",
        sa.Column("maintenance_reason", sa.String(length=240), nullable=True),
    )
    op.add_column(
        "agents",
        sa.Column("availability_updated_at", sa.DateTime(), nullable=True),
    )
    op.create_check_constraint(
        "ck_agents_operational_availability",
        "agents",
        "(accepting_work AND maintenance_reason IS NULL) OR "
        "(NOT accepting_work AND maintenance_reason IS NOT NULL "
        "AND length(btrim(maintenance_reason)) > 0)",
    )
    op.create_index(
        "ix_agents_accepting_work",
        "agents",
        ["accepting_work"],
        unique=False,
    )
    op.alter_column("agents", "accepting_work", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_agents_accepting_work", table_name="agents")
    op.drop_constraint(
        "ck_agents_operational_availability",
        "agents",
        type_="check",
    )
    op.drop_column("agents", "availability_updated_at")
    op.drop_column("agents", "maintenance_reason")
    op.drop_column("agents", "accepting_work")
