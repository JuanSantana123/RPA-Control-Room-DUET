"""library checkout global lock

Revision ID: b7e41d8c9a52
Revises: c6a9f4d2e781
Create Date: 2026-10-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e41d8c9a52"
down_revision: Union[str, None] = "c6a9f4d2e781"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "library_checkouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("library_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("checked_out_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["library_id"],
            ["libraries.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["automation_projects.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "library_id",
            name="uq_library_checkouts_library",
        ),
    )
    op.create_index(
        op.f("ix_library_checkouts_id"),
        "library_checkouts",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkouts_library_id"),
        "library_checkouts",
        ["library_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkouts_project_id"),
        "library_checkouts",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkouts_user_id"),
        "library_checkouts",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "library_checkout_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("library_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["library_id"],
            ["libraries.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["automation_projects.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_library_checkout_history_id"),
        "library_checkout_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkout_history_library_id"),
        "library_checkout_history",
        ["library_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkout_history_project_id"),
        "library_checkout_history",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkout_history_user_id"),
        "library_checkout_history",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkout_history_action"),
        "library_checkout_history",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_checkout_history_created_at"),
        "library_checkout_history",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_library_checkout_history_created_at"),
        table_name="library_checkout_history",
    )
    op.drop_index(
        op.f("ix_library_checkout_history_action"),
        table_name="library_checkout_history",
    )
    op.drop_index(
        op.f("ix_library_checkout_history_user_id"),
        table_name="library_checkout_history",
    )
    op.drop_index(
        op.f("ix_library_checkout_history_project_id"),
        table_name="library_checkout_history",
    )
    op.drop_index(
        op.f("ix_library_checkout_history_library_id"),
        table_name="library_checkout_history",
    )
    op.drop_index(
        op.f("ix_library_checkout_history_id"),
        table_name="library_checkout_history",
    )
    op.drop_table("library_checkout_history")

    op.drop_index(
        op.f("ix_library_checkouts_user_id"),
        table_name="library_checkouts",
    )
    op.drop_index(
        op.f("ix_library_checkouts_project_id"),
        table_name="library_checkouts",
    )
    op.drop_index(
        op.f("ix_library_checkouts_library_id"),
        table_name="library_checkouts",
    )
    op.drop_index(
        op.f("ix_library_checkouts_id"),
        table_name="library_checkouts",
    )
    op.drop_table("library_checkouts")
