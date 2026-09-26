from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
# ============================================================
# BANCO DE DADOS
# ============================================================

# ============================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================

# O Control Room utiliza exclusivamente PostgreSQL.
#
# A DATABASE_URL deve estar configurada no ambiente antes
# de iniciar a aplicação.
#
# Não existe fallback para SQLite.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não configurada. "
        "O Control Room requer PostgreSQL."
    )

# ============================================================
# ENGINE
# ============================================================

# O Control Room utiliza exclusivamente PostgreSQL.
engine = create_engine(
    DATABASE_URL
)

# ============================================================
# BASE DOS MODELOS
# ============================================================

Base = declarative_base()


# ============================================================
# SESSÃO
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)



# ============================================================
# CRIA BANCO / TABELAS
# ============================================================

def criar_banco():
    """
    Atualiza o schema até a revisão Alembic mais recente.

    Bancos legados sem ``alembic_version`` só recebem o baseline quando a
    estrutura real é equivalente ao metadata atual. Qualquer divergência
    interrompe o startup para evitar marcar como migrado um schema incompleto.
    """

    config = Config(str(Path(__file__).with_name("alembic.ini")))

    with engine.begin() as connection:
        # Serializa bootstrap/migração quando mais de uma instância sobe ao
        # mesmo tempo. O lock é liberado automaticamente no fim da transação.
        connection.execute(text("SELECT pg_advisory_xact_lock(1877423101)"))
        config.attributes["connection"] = connection

        table_names = set(inspect(connection).get_table_names())
        application_tables = table_names - {"alembic_version"}

        if not application_tables:
            command.upgrade(config, "head")
            return

        if "alembic_version" not in table_names:
            migration_context = MigrationContext.configure(connection)
            differences = compare_metadata(migration_context, Base.metadata)

            if differences:
                preview = "; ".join(str(item) for item in differences[:5])
                raise RuntimeError(
                    "Schema PostgreSQL legado diverge do baseline versionado. "
                    "A migração automática foi interrompida. "
                    f"Primeiras diferenças: {preview}"
                )

            command.stamp(config, "head")
            return

        command.upgrade(config, "head")

