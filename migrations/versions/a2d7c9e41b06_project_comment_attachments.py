"""add project comment image attachments

Revision ID: a2d7c9e41b06
Revises: f7a1d4b3c902
Create Date: 2026-09-27
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a2d7c9e41b06"
down_revision: str | None = "f7a1d4b3c902"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_comment_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["project_comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["automation_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(op.f("ix_project_comment_attachments_id"), "project_comment_attachments", ["id"], unique=False)
    op.create_index(op.f("ix_project_comment_attachments_project_id"), "project_comment_attachments", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_comment_attachments_comment_id"), "project_comment_attachments", ["comment_id"], unique=False)
    op.create_index(op.f("ix_project_comment_attachments_uploaded_by"), "project_comment_attachments", ["uploaded_by"], unique=False)
    op.create_index(op.f("ix_project_comment_attachments_created_at"), "project_comment_attachments", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_comment_attachments_created_at"), table_name="project_comment_attachments")
    op.drop_index(op.f("ix_project_comment_attachments_uploaded_by"), table_name="project_comment_attachments")
    op.drop_index(op.f("ix_project_comment_attachments_comment_id"), table_name="project_comment_attachments")
    op.drop_index(op.f("ix_project_comment_attachments_project_id"), table_name="project_comment_attachments")
    op.drop_index(op.f("ix_project_comment_attachments_id"), table_name="project_comment_attachments")
    op.drop_table("project_comment_attachments")
