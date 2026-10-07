"""developer ide sessions

Revision ID: 3f7938c26387
Revises: a2d7c9e41b06
Create Date: 2026-10-01 13:10:02.864218
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# IDENTIFICAÇÃO DA MIGRATION
# ============================================================

revision: str = "3f7938c26387"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "a2d7c9e41b06"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """
    Cria exclusivamente a infraestrutura persistente utilizada
    pelas sessões do DUET Developer Bridge.

    Esta migration NÃO altera Agents, Executions, Vault,
    Scheduler ou qualquer outra estrutura existente.
    """

    # ========================================================
    # TABELA - DEVELOPER IDE SESSIONS
    # ========================================================

    op.create_table(
        "developer_ide_sessions",

        # Identificador interno da sessão.
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        # AutomationProject aberto na IDE externa.
        sa.Column(
            "project_id",
            sa.Integer(),
            nullable=False,
        ),

        # Usuário do DUET proprietário da sessão.
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),

        # Hash SHA-256 do código temporário de abertura.
        sa.Column(
            "launch_code_hash",
            sa.String(length=64),
            nullable=False,
        ),

        # Hash SHA-256 do token utilizado pelo Developer Bridge.
        sa.Column(
            "access_token_hash",
            sa.String(length=64),
            nullable=True,
        ),

        # Expiração do código temporário de abertura.
        sa.Column(
            "launch_expires_at",
            sa.DateTime(),
            nullable=False,
        ),

        # Momento em que o launch code foi utilizado.
        sa.Column(
            "redeemed_at",
            sa.DateTime(),
            nullable=True,
        ),

        # Expiração da sessão do Developer Bridge.
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=True,
        ),

        # Permite invalidar explicitamente a sessão.
        sa.Column(
            "revoked",
            sa.Boolean(),
            nullable=False,
        ),

        # Auditoria da criação.
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        # Última utilização conhecida.
        sa.Column(
            "last_seen_at",
            sa.DateTime(),
            nullable=True,
        ),

        # ====================================================
        # RELACIONAMENTOS
        # ====================================================

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

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )


    # ========================================================
    # ÍNDICES
    # ========================================================

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_access_token_hash"
        ),
        "developer_ide_sessions",
        ["access_token_hash"],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_created_at"
        ),
        "developer_ide_sessions",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_expires_at"
        ),
        "developer_ide_sessions",
        ["expires_at"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_id"
        ),
        "developer_ide_sessions",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_launch_code_hash"
        ),
        "developer_ide_sessions",
        ["launch_code_hash"],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_launch_expires_at"
        ),
        "developer_ide_sessions",
        ["launch_expires_at"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_project_id"
        ),
        "developer_ide_sessions",
        ["project_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_revoked"
        ),
        "developer_ide_sessions",
        ["revoked"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_developer_ide_sessions_user_id"
        ),
        "developer_ide_sessions",
        ["user_id"],
        unique=False,
    )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """
    Remove somente a estrutura introduzida por esta migration.
    """

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_user_id"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_revoked"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_project_id"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_launch_expires_at"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_launch_code_hash"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_id"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_expires_at"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_created_at"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_index(
        op.f(
            "ix_developer_ide_sessions_access_token_hash"
        ),
        table_name="developer_ide_sessions",
    )

    op.drop_table(
        "developer_ide_sessions"
    )