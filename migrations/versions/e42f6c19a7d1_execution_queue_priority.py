"""add execution queue priority and wait timestamp

Revision ID: e42f6c19a7d1
Revises: 9c31b2f4d802
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e42f6c19a7d1"
down_revision: str | None = "9c31b2f4d802"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "executions",
        sa.Column("priority", sa.String(), nullable=False, server_default="normal"),
    )
    op.add_column(
        "executions",
        sa.Column("queued_at", sa.DateTime(), nullable=True),
    )
    op.execute(
        "UPDATE executions SET queued_at = CURRENT_TIMESTAMP "
        "WHERE status = 'queued' AND queued_at IS NULL"
    )
    op.create_check_constraint(
        "ck_executions_priority",
        "executions",
        "priority IN ('low', 'normal', 'high', 'urgent')",
    )
    op.create_index("ix_executions_priority", "executions", ["priority"], unique=False)
    op.create_index("ix_executions_queued_at", "executions", ["queued_at"], unique=False)
    op.alter_column("executions", "priority", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_executions_queued_at", table_name="executions")
    op.drop_index("ix_executions_priority", table_name="executions")
    op.drop_constraint("ck_executions_priority", "executions", type_="check")
    op.drop_column("executions", "queued_at")
    op.drop_column("executions", "priority")
