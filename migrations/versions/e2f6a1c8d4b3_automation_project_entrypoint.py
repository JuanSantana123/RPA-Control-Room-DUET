"""automation project configurable entrypoint

Revision ID: e2f6a1c8d4b3
Revises: b7e41d8c9a52
Create Date: 2026-10-02
"""

from alembic import op
import sqlalchemy as sa


revision = "e2f6a1c8d4b3"
down_revision = "b7e41d8c9a52"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "automation_projects",
        sa.Column(
            "entrypoint_path",
            sa.String(length=1000),
            nullable=False,
            server_default="main.py",
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "automation_projects",
        "entrypoint_path",
    )
