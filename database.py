from sqlalchemy import create_engine
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

    # Cria todas as tabelas definidas nos models.py
    # que ainda não existem no banco de dados.
    #
    # Isso funciona tanto para SQLite quanto para PostgreSQL.
    Base.metadata.create_all(bind=engine)

