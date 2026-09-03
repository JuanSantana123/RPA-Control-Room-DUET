from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


# ============================================================
# BANCO DE DADOS
# ============================================================

DATABASE_URL = "sqlite:///./control_room.db"


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
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
# MIGRAÇÃO DA TABELA DE AGENDAMENTOS
# ============================================================

def _atualizar_tabela_schedules():

    colunas = {
        "intervalo_ativo": "INTEGER NOT NULL DEFAULT 0",
        "intervalo_valor": "INTEGER",
        "intervalo_unidade": "VARCHAR",
        "horario_fim": "VARCHAR"
    }

    with engine.begin() as connection:

        resultado = connection.execute(
            text("PRAGMA table_info(schedules)")
        )

        existentes = {
            linha[1]
            for linha in resultado.fetchall()
        }

        # A tabela pode ainda não existir. O create_all abaixo
        # cuidará da criação inicial.
        if not existentes:
            return

        for nome, definicao in colunas.items():

            if nome not in existentes:

                connection.execute(
                    text(
                        f"ALTER TABLE schedules ADD COLUMN {nome} {definicao}"
                    )
                )

def _atualizar_tabela_executions():
    # Colunas que podem precisar ser adicionadas
    # em uma tabela executions já existente.
    colunas = {
        "pid": "INTEGER"
    }

    with engine.begin() as connection:
        resultado = connection.execute(
            text("PRAGMA table_info(executions)")
        )

        existentes = {
            linha[1]
            for linha in resultado.fetchall()
        }

        if not existentes:
            return

        for nome, definicao in colunas.items():
            if nome not in existentes:
                connection.execute(
                    text(
                        f"ALTER TABLE executions "
                        f"ADD COLUMN {nome} {definicao}"
                    )
                )
# ============================================================
# CRIA BANCO / TABELAS
# ============================================================

def criar_banco():
    Base.metadata.create_all(bind=engine)
    _atualizar_tabela_schedules()
    _atualizar_tabela_executions()
