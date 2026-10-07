# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DE GESTÃO DA FILA
# ============================================================
#
# Responsável exclusivamente pelas falhas técnicas ocorridas
# em ações administrativas sobre Executions queued.
#
# Este módulo cobre:
#
# - falha ao cancelar Execution queued;
# - falha ao alterar prioridade de Execution queued.
#
# Operações bem-sucedidas não são registradas nos Logs do
# Sistema, pois o estado persistido da Execution representa
# essas alterações.
#
# Este módulo NÃO:
#
# - acessa banco de dados;
# - altera Execution;
# - decide regras de fila;
# - implementa endpoints FastAPI.
#
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA AO CANCELAR EXECUTION DA FILA
# ============================================================

def registrar_falha_cancelamento_fila(
    *,
    execution_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra exceção técnica durante o cancelamento de uma
    Execution ainda presente na fila.
    """

    logger.exception(
        "Erro ao cancelar execução da fila",
        extra={
            "event": "execution.queue.cancel.failed",
            "category": "SYSTEM",
            "component": "execution_queue_management",
            "ui_visible": True,

            "status": "failed",
            "action": "cancel_queued_execution",
            "reason": "queued_execution_cancel_failed",

            "execution_id": execution_id,
            "user_id": user_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# FALHA AO ALTERAR PRIORIDADE
# ============================================================

def registrar_falha_atualizacao_prioridade(
    *,
    execution_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra exceção técnica durante atualização da prioridade
    de uma Execution queued.
    """

    logger.exception(
        "Falha ao atualizar prioridade da execução",
        extra={
            "event":
                "execution.queue.priority_update.failed",

            "category": "SYSTEM",
            "component": "execution_queue_management",
            "ui_visible": True,

            "status": "failed",
            "action": "update_queued_execution_priority",
            "reason":
                "queued_execution_priority_update_failed",

            "execution_id": execution_id,
            "user_id": user_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )