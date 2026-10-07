"""project checkout audit history

Revision ID: c6a9f4d2e781
Revises: 8d4f7a91c2b6
Create Date: 2026-10-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6a9f4d2e781"
down_revision: Union[str, None] = "8d4f7a91c2b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_checkout_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_name", sa.String(length=255), nullable=False),
        sa.Column("checkout_owner_user_id", sa.Integer(), nullable=True),
        sa.Column("checkout_owner_user_name", sa.String(length=255), nullable=False),
        sa.Column("checkout_started_at", sa.DateTime(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["automation_projects.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["checkout_owner_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_project_checkout_history_id"),
        "project_checkout_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_checkout_history_project_id"),
        "project_checkout_history",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_checkout_history_event_type"),
        "project_checkout_history",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_checkout_history_actor_user_id"),
        "project_checkout_history",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_checkout_history_checkout_owner_user_id"),
        "project_checkout_history",
        ["checkout_owner_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_checkout_history_occurred_at"),
        "project_checkout_history",
        ["occurred_at"],
        unique=False,
    )

    # Preserva os Checkouts que já estavam ativos antes desta migration.
    # Assim a rastreabilidade não começa "vazia" para locks existentes.
    op.execute(
        sa.text(
            """
            INSERT INTO project_checkout_history (
                project_id,
                project_name,
                event_type,
                actor_user_id,
                actor_user_name,
                checkout_owner_user_id,
                checkout_owner_user_name,
                checkout_started_at,
                occurred_at
            )
            SELECT
                pc.project_id,
                ap.name,
                'checkout',
                pc.user_id,
                u.name,
                pc.user_id,
                u.name,
                pc.checked_out_at,
                pc.checked_out_at
            FROM project_checkouts pc
            JOIN automation_projects ap ON ap.id = pc.project_id
            JOIN users u ON u.id = pc.user_id
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_project_checkout_history_occurred_at"),
        table_name="project_checkout_history",
    )
    op.drop_index(
        op.f("ix_project_checkout_history_checkout_owner_user_id"),
        table_name="project_checkout_history",
    )
    op.drop_index(
        op.f("ix_project_checkout_history_actor_user_id"),
        table_name="project_checkout_history",
    )
    op.drop_index(
        op.f("ix_project_checkout_history_event_type"),
        table_name="project_checkout_history",
    )
    op.drop_index(
        op.f("ix_project_checkout_history_project_id"),
        table_name="project_checkout_history",
    )
    op.drop_index(
        op.f("ix_project_checkout_history_id"),
        table_name="project_checkout_history",
    )
    op.drop_table("project_checkout_history")
