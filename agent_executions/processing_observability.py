# ============================================================
# DUET - AGENT EXECUTIONS - OBSERVABILIDADE DE PROCESSAMENTO
# ============================================================
#
# Responsável exclusivamente por falhas técnicas internas
# ocorridas durante ou após a persistência do resultado final
# enviado pelo Agent.
#
# Este módulo registra:
#
# - falha ao agendar verificação de idle da sessão;
# - falha técnica ao processar/persistir o resultado final.
#
# Este módulo NÃO:
#
# - valida callbacks;
# - consulta ou altera banco;
# - agenda timers diretamente;
# - altera o resultado da Execution;
# - registra falhas funcionais do código do Robot.
#
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA AO AGENDAR VERIFICAÇÃO DE IDLE
# ============================================================

def registrar_falha_agendamento_idle(
    *,
    execution_id: int,
    agent_id: str,
    error: Exception,
) -> None:
    """
    Registra falha técnica ao criar a verificação posterior
    de ociosidade da sessão Windows do Agent.

    O resultado da Execution já está persistido e não deve
    ser alterado por esta falha de housekeeping.
    """

    logger.exception(
        "Não foi possível agendar verificação de idle "
        "após a execução",
        extra={
            "event": "execution.result.idle_schedule.failed",
            "category": "SYSTEM",
            "component": "agent_idle",
            "ui_visible": True,

            "status": "failed",
            "action": "schedule_agent_idle_check",
            "reason": "agent_idle_schedule_failed",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# FALHA AO PROCESSAR/PERSISTIR RESULTADO
# ============================================================

def registrar_falha_atualizacao_resultado(
    *,
    execution_id: int,
    agent_id: str,
    error: Exception,
) -> None:
    """
    Registra exceção técnica ocorrida durante o processamento
    ou persistência do resultado final da Execution.

    Como esta função é chamada dentro do except principal,
    logger.exception() preserva o traceback real.
    """

    logger.exception(
        "Erro ao atualizar resultado da execução",
        extra={
            "event": "execution.result.update.failed",
            "category": "SYSTEM",
            "component": "execution_result",
            "ui_visible": True,

            "status": "failed",
            "action": "update_execution_result",
            "reason": "execution_result_update_failed",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )