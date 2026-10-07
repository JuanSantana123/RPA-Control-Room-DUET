"""
Adiciona as dependências de Libraries às versões de Templates.

Cada AutomationTemplateVersion passa a possuir um snapshot
imutável das LibraryVersions utilizadas naquele momento.

Exemplo:

    Template Padrão DUET
        v3
            logging_core -> 2.0.0
            excel_utils  -> 4.1.0

        v4
            logging_core -> 3.0.0
            excel_utils  -> 4.1.0

IMPORTANTE
----------
A dependência pertence à versão do Template.

Portanto:

- alterar uma Library não modifica Templates anteriores;
- alterar a composição do Template exige uma nova versão;
- LibraryVersion continua imutável;
- AutomationTemplateVersion continua imutável;
- projetos já criados não são alterados.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# IDENTIFICAÇÃO DA MIGRATION
# ============================================================

revision: str = "e50d2540f7b1"

# Migration anterior:
#
# Developer IDE Session / External IDE
down_revision: Union[str, Sequence[str], None] = (
    "3f7938c26387"
)

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """
    Cria a tabela que registra quais versões publicadas de
    Libraries pertencem a cada AutomationTemplateVersion.
    """

    # --------------------------------------------------------
    # TABELA
    # --------------------------------------------------------

    op.create_table(
        "template_version_library_dependencies",

        # ====================================================
        # IDENTIFICADOR
        # ====================================================

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        # ====================================================
        # VERSÃO DO TEMPLATE
        # ====================================================

        sa.Column(
            "template_version_id",
            sa.Integer(),
            nullable=False,
        ),

        # ====================================================
        # LIBRARY
        # ====================================================

        sa.Column(
            "library_id",
            sa.Integer(),
            nullable=False,
        ),

        # ====================================================
        # VERSÃO EXATA DA LIBRARY
        # ====================================================

        sa.Column(
            "library_version_id",
            sa.Integer(),
            nullable=False,
        ),

        # ====================================================
        # AUDITORIA
        # ====================================================

        sa.Column(
            "created_by",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        # ====================================================
        # CHAVE PRIMÁRIA
        # ====================================================

        sa.PrimaryKeyConstraint(
            "id",
        ),

        # ====================================================
        # FOREIGN KEYS
        # ====================================================

        # Se uma versão de Template for removida fisicamente,
        # suas dependências deixam de possuir significado.
        sa.ForeignKeyConstraint(
            ["template_version_id"],
            ["automation_template_versions.id"],
            ondelete="CASCADE",
        ),

        # Library é identidade estável do catálogo.
        sa.ForeignKeyConstraint(
            ["library_id"],
            ["libraries.id"],
        ),

        # Aponta sempre para uma LibraryVersion publicada
        # específica e imutável.
        sa.ForeignKeyConstraint(
            ["library_version_id"],
            ["library_versions.id"],
        ),

        # Usuário responsável pela criação do snapshot.
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),

        # ====================================================
        # CONSISTÊNCIA
        # ====================================================

        # Uma mesma versão de Template não pode utilizar
        # simultaneamente duas versões da mesma Library.
        #
        # Exemplo inválido:
        #
        # Template v3
        #   logging_core -> 2.0.0
        #   logging_core -> 3.0.0
        sa.UniqueConstraint(
            "template_version_id",
            "library_id",
            name="uq_tplver_libdep_library",
        ),
    )

    # ========================================================
    # ÍNDICES
    # ========================================================

    op.create_index(
        op.f(
            "ix_template_version_library_dependencies_id"
        ),
        "template_version_library_dependencies",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "template_version_id"
        ),
        "template_version_library_dependencies",
        ["template_version_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "library_id"
        ),
        "template_version_library_dependencies",
        ["library_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "library_version_id"
        ),
        "template_version_library_dependencies",
        ["library_version_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "created_by"
        ),
        "template_version_library_dependencies",
        ["created_by"],
        unique=False,
    )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """
    Remove somente a estrutura criada por esta migration.

    Nenhum AutomationTemplate, Library, projeto, Robot,
    Execution ou Schedule é alterado.
    """

    # Remove os índices antes da tabela.

    op.drop_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "created_by"
        ),
        table_name=(
            "template_version_library_dependencies"
        ),
    )

    op.drop_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "library_version_id"
        ),
        table_name=(
            "template_version_library_dependencies"
        ),
    )

    op.drop_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "library_id"
        ),
        table_name=(
            "template_version_library_dependencies"
        ),
    )

    op.drop_index(
        op.f(
            "ix_template_version_library_dependencies_"
            "template_version_id"
        ),
        table_name=(
            "template_version_library_dependencies"
        ),
    )

    op.drop_index(
        op.f(
            "ix_template_version_library_dependencies_id"
        ),
        table_name=(
            "template_version_library_dependencies"
        ),
    )

    op.drop_table(
        "template_version_library_dependencies"
    )