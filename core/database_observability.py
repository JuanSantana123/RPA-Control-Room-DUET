# ============================================================
# OBSERVABILIDADE - BANCO DE DADOS
# ============================================================
#
# Responsabilidade:
#     Classificar e registrar eventos técnicos relacionados
#     à inicialização do PostgreSQL e às migrations Alembic.
#
# Este módulo NÃO:
#     - cria conexões;
#     - executa migrations;
#     - altera schema;
#     - controla transações.
#
# Ele recebe o resultado da inicialização e registra somente
# informações relevantes para diagnóstico.
# ============================================================

from sqlalchemy.exc import (
    InterfaceError,
    OperationalError,
)

from core.logging_config import logger


# ============================================================
# BANCO INICIALIZADO
# ============================================================

def registrar_banco_inicializado() -> None:
    """
    Registra tecnicamente que a inicialização do banco terminou.

    O evento permanece no JSON físico, mas não aparece na tela
    de Observabilidade porque uma inicialização normal não exige
    atenção operacional.
    """

    logger.info(
        "Banco de dados inicializado",
        extra={
            "event": "database.initialized",
            "category": "SYSTEM",
            "component": "database",
            "status": "success",
            "ui_visible": False,
        },
    )


# ============================================================
# FALHA DE INICIALIZAÇÃO
# ============================================================

def registrar_falha_inicializacao_banco(
    error: Exception,
) -> None:
    """
    Classifica a falha da inicialização do banco.

    OperationalError / InterfaceError:
        problema de conexão/comunicação com PostgreSQL.

    Demais exceções:
        problema ocorrido durante bootstrap, validação do schema
        ou execução das migrations Alembic.
    """

    if isinstance(
        error,
        (
            OperationalError,
            InterfaceError,
        ),
    ):
        evento = "database.connection.failed"
        mensagem = "Falha de conexão com o banco de dados"

    else:
        evento = "database.migration.failed"
        mensagem = "Falha ao inicializar ou migrar o banco de dados"

    # logger.exception() é intencional:
    # além dos campos estruturados, preserva o traceback completo
    # no arquivo JSON para diagnóstico técnico.
    logger.exception(
        mensagem,
        extra={
            "event": evento,
            "category": "SYSTEM",
            "component": "database",
            "status": "failed",
            "ui_visible": True,
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )