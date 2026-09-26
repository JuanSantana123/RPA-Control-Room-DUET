"""add explicit schedule misfire policy

Revision ID: 9c31b2f4d802
Revises: 5e3799a70fb6
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9c31b2f4d802"
down_revision: str | None = "5e3799a70fb6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "schedules",
        sa.Column("misfire_policy", sa.String(), nullable=False, server_default="run_once"),
    )
    op.add_column(
        "schedules",
        sa.Column("misfire_grace_seconds", sa.Integer(), nullable=False, server_default="300"),
    )
    op.add_column(
        "schedules",
        sa.Column("ultima_ocorrencia_perdida", sa.DateTime(), nullable=True),
    )
    op.create_check_constraint(
        "ck_schedules_misfire_policy",
        "schedules",
        "misfire_policy IN ('run_once', 'skip')",
    )
    op.create_check_constraint(
        "ck_schedules_misfire_grace_seconds",
        "schedules",
        "misfire_grace_seconds BETWEEN 30 AND 86400",
    )
    op.alter_column("schedules", "misfire_policy", server_default=None)
    op.alter_column("schedules", "misfire_grace_seconds", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_schedules_misfire_grace_seconds", "schedules", type_="check")
    op.drop_constraint("ck_schedules_misfire_policy", "schedules", type_="check")
    op.drop_column("schedules", "ultima_ocorrencia_perdida")
    op.drop_column("schedules", "misfire_grace_seconds")
    op.drop_column("schedules", "misfire_policy")
