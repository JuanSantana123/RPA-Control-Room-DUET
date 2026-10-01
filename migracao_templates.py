# ============================================================
# MIGRAÇÃO - AUTOMATION TEMPLATES
# ============================================================
#
# Cria as tabelas versionadas de Templates e adiciona ao
# AutomationProject os campos de proveniência do Template.
#
# A migração é idempotente:
# pode ser executada novamente sem recriar colunas existentes.
#
# IMPORTANTE:
# execute depois de substituir models.py pela versão desta entrega.
# ============================================================

from sqlalchemy import inspect, text

from database import (
    Base,
    engine,
)

from models import (
    AutomationTemplate,
    AutomationTemplateVersion,
)


# ============================================================
# AUXILIARES
# ============================================================

def _column_exists(
    inspector,
    table_name: str,
    column_name: str,
) -> bool:
    """
    Retorna True quando a coluna já existe.
    """

    return any(
        column.get("name") ==
            column_name
        for column in inspector.get_columns(
            table_name
        )
    )


def _index_exists(
    inspector,
    table_name: str,
    index_name: str,
) -> bool:
    """
    Retorna True quando o índice já existe.
    """

    return any(
        index.get("name") ==
            index_name
        for index in inspector.get_indexes(
            table_name
        )
    )


# ============================================================
# MIGRAÇÃO
# ============================================================

def executar_migracao() -> None:
    """
    Evolui o schema atual sem destruir dados existentes.
    """

    dialect = (
        engine.dialect.name.lower()
    )

    if dialect != "postgresql":
        raise RuntimeError(
            "Esta migration foi preparada para PostgreSQL. "
            f"Banco detectado: {dialect}."
        )

    print()
    print("=" * 72)
    print("DUET CORE - MIGRAÇÃO AUTOMATION TEMPLATES")
    print("=" * 72)

    # --------------------------------------------------------
    # ETAPA 1 - CRIA TABELAS NOVAS
    # --------------------------------------------------------

    print(
        "[1/6] Criando tabelas de Templates..."
    )

    Base.metadata.create_all(
        bind=engine,
        tables=[
            AutomationTemplate.__table__,
            AutomationTemplateVersion.__table__,
        ],
        checkfirst=True,
    )

    print(
        "      tabelas verificadas/criadas."
    )

    # --------------------------------------------------------
    # ETAPA 2 - base_template_id
    # --------------------------------------------------------

    inspector = inspect(
        engine
    )

    print(
        "[2/6] Verificando automation_projects.base_template_id..."
    )

    if not _column_exists(
        inspector,
        "automation_projects",
        "base_template_id",
    ):

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE automation_projects
                    ADD COLUMN base_template_id INTEGER NULL
                    REFERENCES automation_templates(id)
                    ON DELETE SET NULL
                    """
                )
            )

        print(
            "      coluna criada."
        )

    else:
        print(
            "      coluna já existe."
        )

    # --------------------------------------------------------
    # ETAPA 3 - base_template_name
    # --------------------------------------------------------

    inspector = inspect(
        engine
    )

    print(
        "[3/6] Verificando automation_projects.base_template_name..."
    )

    if not _column_exists(
        inspector,
        "automation_projects",
        "base_template_name",
    ):

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE automation_projects
                    ADD COLUMN base_template_name VARCHAR(180) NULL
                    """
                )
            )

        print(
            "      coluna criada."
        )

    else:
        print(
            "      coluna já existe."
        )

    # --------------------------------------------------------
    # ETAPA 4 - base_template_version_id
    # --------------------------------------------------------

    inspector = inspect(
        engine
    )

    print(
        "[4/6] Verificando automation_projects."
        "base_template_version_id..."
    )

    if not _column_exists(
        inspector,
        "automation_projects",
        "base_template_version_id",
    ):

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE automation_projects
                    ADD COLUMN base_template_version_id INTEGER NULL
                    REFERENCES automation_template_versions(id)
                    ON DELETE SET NULL
                    """
                )
            )

        print(
            "      coluna criada."
        )

    else:
        print(
            "      coluna já existe."
        )

    # --------------------------------------------------------
    # ETAPA 5 - base_template_version
    # --------------------------------------------------------

    inspector = inspect(
        engine
    )

    print(
        "[5/6] Verificando automation_projects."
        "base_template_version..."
    )

    if not _column_exists(
        inspector,
        "automation_projects",
        "base_template_version",
    ):

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE automation_projects
                    ADD COLUMN base_template_version INTEGER NULL
                    """
                )
            )

        print(
            "      coluna criada."
        )

    else:
        print(
            "      coluna já existe."
        )

    # --------------------------------------------------------
    # ETAPA 6 - ÍNDICES
    # --------------------------------------------------------

    inspector = inspect(
        engine
    )

    print(
        "[6/6] Verificando índices de proveniência..."
    )

    indexes = [
        (
            "ix_automation_projects_base_template_id",
            "base_template_id",
        ),
        (
            "ix_automation_projects_base_template_version_id",
            "base_template_version_id",
        ),
    ]

    for (
        index_name,
        column_name,
    ) in indexes:

        if _index_exists(
            inspector,
            "automation_projects",
            index_name,
        ):
            print(
                f"      {index_name}: já existe."
            )
            continue

        with engine.begin() as connection:
            connection.execute(
                text(
                    f"""
                    CREATE INDEX {index_name}
                    ON automation_projects ({column_name})
                    """
                )
            )

        print(
            f"      {index_name}: criado."
        )

        inspector = inspect(
            engine
        )

    print()
    print(
        "MIGRAÇÃO DE TEMPLATES CONCLUÍDA."
    )
    print()


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":
    executar_migracao()
