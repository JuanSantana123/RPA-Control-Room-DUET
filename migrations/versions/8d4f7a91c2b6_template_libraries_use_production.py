"""template libraries use production at project creation

Revision ID: 8d4f7a91c2b6
Revises: e50d2540f7b1
Create Date: 2026-10-02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8d4f7a91c2b6"
down_revision = "e50d2540f7b1"
branch_labels = None
depends_on = None


TABLE = "template_version_library_dependencies"
OLD_INDEX = (
    "ix_template_version_library_dependencies_"
    "library_version_id"
)


def _index_exists(name: str) -> bool:
    """Evita falha em ambientes onde o índice legado não foi criado."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    return any(
        index.get("name") == name
        for index in inspector.get_indexes(TABLE)
    )


def upgrade() -> None:
    """
    O Template deixa de fixar uma LibraryVersion.

    O valor histórico anterior é preservado em uma coluna explicitamente
    legada para não destruir informação existente e para manter downgrade
    possível. Novos vínculos deixam essa coluna como NULL.
    """

    if _index_exists(OLD_INDEX):
        op.drop_index(
            OLD_INDEX,
            table_name=TABLE,
        )

    op.alter_column(
        TABLE,
        "library_version_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        new_column_name="legacy_library_version_id",
    )

    op.alter_column(
        TABLE,
        "legacy_library_version_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        nullable=True,
    )


def downgrade() -> None:
    """
    Restaura o contrato antigo que exigia library_version_id.

    Registros históricos preservam a versão original. Registros criados
    após o upgrade recebem, para fins de downgrade, a Produção vigente da
    Library. Se alguma Library não possuir Produção nesse momento, o
    downgrade é interrompido em vez de inventar uma versão.
    """

    bind = op.get_bind()

    bind.execute(
        sa.text(
            f"""
            UPDATE {TABLE} AS dependency
               SET legacy_library_version_id = library.production_version_id
              FROM libraries AS library
             WHERE dependency.library_id = library.id
               AND dependency.legacy_library_version_id IS NULL
            """
        )
    )

    unresolved = bind.execute(
        sa.text(
            f"""
            SELECT COUNT(*)
              FROM {TABLE}
             WHERE legacy_library_version_id IS NULL
            """
        )
    ).scalar_one()

    if unresolved:
        raise RuntimeError(
            "Não é possível realizar downgrade: existe vínculo de Template "
            "com Library sem versão de Produção para restaurar o contrato "
            "antigo."
        )

    op.alter_column(
        TABLE,
        "legacy_library_version_id",
        existing_type=sa.Integer(),
        existing_nullable=True,
        nullable=False,
    )

    op.alter_column(
        TABLE,
        "legacy_library_version_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        new_column_name="library_version_id",
    )

    op.create_index(
        OLD_INDEX,
        TABLE,
        ["library_version_id"],
        unique=False,
    )
