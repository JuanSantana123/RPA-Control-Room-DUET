# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DE RECONCILIAÇÃO
# ============================================================
#
# Responsável exclusivamente pelos eventos relevantes gerados
# quando o Control Room precisa reconciliar uma Execution que
# permaneceu em estado running sem receber confirmação final
# normal pelo callback do Agent.
#
# Este módulo registra:
#
# - Execution órfã finalizada como unknown;
# - estado terminal recuperado diretamente do Agent.
#
# Este módulo NÃO:
#
# - consulta Agent;
# - acessa banco de dados;
# - altera Execution;
# - executa regras de reconciliação.
#
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# EXECUTION ÓRFÃ -> UNKNOWN
# ============================================================

def registrar_reconciliacao_unknown(
    *,
    execution_id: int,
    agent_id: str,
    pid: int | None,
) -> None:
    """
    Registra quando uma Execution marcada como running não
    possui mais processo correspondente no Agent e seu estado
    final real não pode ser determinado.
    """

    logger.warning(
        "Execution órfã reconciliada como unknown",
        extra={
            "event": "execution.reconciliation.unknown",
            "category": "SYSTEM",
            "component": "execution_reconciliation",
            "ui_visible": True,

            "status": "unknown",
            "action": "reconcile_running_execution",
            "reason": "process_no_longer_exists",

            "execution_id": execution_id,
            "agent_id": agent_id,
            "pid": pid,

            "resource_type": "execution",
            "resource_id": execution_id,

            "status_before": "running",
            "status_after": "unknown",
        },
    )


# ============================================================
# ESTADO TERMINAL RECUPERADO DO AGENT
# ============================================================

def registrar_reconciliacao_estado_agent(
    *,
    execution_id: int,
    agent_id: str,
    status_after: str,
) -> None:
    """
    Registra quando o Control Room recupera do Agent um estado
    terminal que não havia sido persistido pelo callback normal.
    """

    logger.warning(
        "Execution reconciliada a partir do estado do Agent",
        extra={
            "event": "execution.reconciliation.completed",
            "category": "SYSTEM",
            "component": "execution_reconciliation",
            "ui_visible": True,

            "status": "reconciled",
            "action": "reconcile_running_execution",
            "reason": "agent_terminal_state_recovered",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "status_before": "running",
            "status_after": status_after,
        },
    )