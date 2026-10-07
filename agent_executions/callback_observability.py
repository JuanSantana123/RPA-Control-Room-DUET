# ============================================================
# DUET - AGENT EXECUTIONS - OBSERVABILIDADE DE CALLBACK
# ============================================================
#
# Responsável exclusivamente pelos eventos de observabilidade
# relacionados à validação do callback de resultado final
# enviado pelo Agent.
#
# Este módulo registra:
#
# - execution_id inconsistente;
# - Execution inexistente;
# - Agent autenticado diferente do Agent informado;
# - Agent diferente do Agent associado à Execution;
# - status final inválido;
# - conflito com Execution já finalizada;
# - transição de estado inválida;
# - conflito concorrente na transição atômica.
#
# Este módulo NÃO:
#
# - consulta banco de dados;
# - altera Execution;
# - autentica Agent;
# - processa o resultado do Robot;
# - agenda bloqueio de sessão;
# - decide respostas HTTP.
#
# Callbacks duplicados idempotentes não são registrados como
# falha, pois fazem parte do comportamento normal de retry.
#
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# EXECUTION_ID INCONSISTENTE
# ============================================================

def registrar_execution_id_inconsistente(
    *,
    execution_id_url: int,
    execution_id_body: int,
    agent_id: str,
) -> None:
    """
    Registra quando URL e payload apontam para Executions
    diferentes.
    """

    logger.warning(
        "execution_id da URL não corresponde ao execution_id "
        "informado pelo Agent",
        extra={
            "event": "execution.result.id_mismatch",
            "category": "INTEGRATION",
            "component": "execution_result",
            "ui_visible": True,

            "status": "rejected",
            "action": "receive_execution_result",
            "reason": "execution_result_id_mismatch",

            "execution_id": execution_id_url,
            "execution_id_body": execution_id_body,
            "agent_id": agent_id,

            "resource_type": "execution",
            "resource_id": execution_id_url,
        },
    )


# ============================================================
# EXECUTION NÃO ENCONTRADA
# ============================================================

def registrar_resultado_execucao_inexistente(
    *,
    execution_id: int,
    agent_id: str,
) -> None:
    """
    Registra callback recebido para uma Execution que não
    existe no Control Room.
    """

    logger.warning(
        "Resultado recebido para execução inexistente",
        extra={
            "event": "execution.result.not_found",
            "category": "INTEGRATION",
            "component": "execution_result",
            "ui_visible": True,

            "status": "rejected",
            "action": "receive_execution_result",
            "reason": "execution_result_not_found",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )


# ============================================================
# AGENT AUTENTICADO DIFERENTE DO PAYLOAD
# ============================================================

def registrar_agent_autenticado_incompativel(
    *,
    execution_id: int,
    authenticated_agent_id: str,
    reported_agent_id: str,
) -> None:
    """
    Registra tentativa de callback em que o Agent autenticado
    não corresponde ao agent_id declarado no payload.
    """

    logger.warning(
        "Agent autenticado não corresponde ao Agent informado "
        "no resultado",
        extra={
            "event": "execution.result.agent_auth_mismatch",
            "category": "SECURITY",
            "component": "execution_result",
            "ui_visible": True,

            "status": "rejected",
            "action": "receive_execution_result",
            "reason": "execution_result_agent_auth_mismatch",

            "execution_id": execution_id,
            "agent_id": reported_agent_id,
            "authenticated_agent_id": authenticated_agent_id,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )


# ============================================================
# AGENT NÃO PERTENCE À EXECUTION
# ============================================================

def registrar_agent_execucao_incompativel(
    *,
    execution_id: int,
    expected_agent_id: str,
    reported_agent_id: str,
) -> None:
    """
    Registra quando um Agent tenta fornecer resultado para
    uma Execution pertencente a outro Agent.
    """

    logger.warning(
        "Agent não corresponde à execução ao enviar resultado",
        extra={
            "event": "execution.result.agent_mismatch",
            "category": "SECURITY",
            "component": "execution_result",
            "ui_visible": True,

            "status": "rejected",
            "action": "receive_execution_result",
            "reason": "execution_result_agent_mismatch",

            "execution_id": execution_id,
            "agent_id": reported_agent_id,
            "expected_agent_id": expected_agent_id,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )


# ============================================================
# STATUS FINAL INVÁLIDO
# ============================================================

def registrar_status_final_invalido(
    *,
    execution_id: int,
    agent_id: str,
    current_status: str | None,
    received_status: str | None,
) -> None:
    """
    Registra callback utilizando status que não representa
    um estado terminal permitido.
    """

    logger.warning(
        "Agent tentou informar status final inválido",
        extra={
            "event": "execution.result.invalid_status",
            "category": "INTEGRATION",
            "component": "execution_result",
            "ui_visible": True,

            "status": "rejected",
            "action": "receive_execution_result",
            "reason": "execution_result_invalid_status",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "current_status": current_status,
            "received_status": received_status,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )


# ============================================================
# CONFLITO COM RESULTADO TERMINAL EXISTENTE
# ============================================================

def registrar_conflito_resultado_terminal(
    *,
    execution_id: int,
    agent_id: str,
    current_status: str | None,
    received_status: str | None,
) -> None:
    """
    Registra tentativa de substituir um resultado terminal
    já persistido por outro resultado terminal diferente.
    """

    logger.warning(
        "Tentativa de alterar execução já finalizada",
        extra={
            "event": "execution.result.terminal_conflict",
            "category": "INTEGRATION",
            "component": "execution_result",
            "ui_visible": True,

            "status": "rejected",
            "action": "receive_execution_result",
            "reason": "execution_result_terminal_conflict",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "current_status": current_status,
            "received_status": received_status,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )


# ============================================================
# TRANSIÇÃO INVÁLIDA
# ============================================================

def registrar_transicao_resultado_invalida(
    *,
    execution_id: int,
    agent_id: str,
    current_status: str | None,
    received_status: str | None,
) -> None:
    """
    Registra resultado final recebido para uma Execution que
    não se encontra em estado running.
    """

    logger.warning(
        "Resultado recebido para execução fora de running",
        extra={
            "event": "execution.result.invalid_transition",
            "category": "INTEGRATION",
            "component": "execution_result",
            "ui_visible": True,

            "status": "rejected",
            "action": "receive_execution_result",
            "reason": "execution_result_invalid_transition",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "current_status": current_status,
            "received_status": received_status,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )


# ============================================================
# CONFLITO NA TRANSIÇÃO ATÔMICA
# ============================================================

def registrar_conflito_atomico_resultado(
    *,
    execution_id: int,
    agent_id: str,
    current_status: str | None,
    received_status: str | None,
) -> None:
    """
    Registra quando outra transação altera a Execution entre
    a validação inicial e o UPDATE condicional.

    Callbacks concorrentes com o mesmo resultado são tratados
    como idempotentes e não chegam a esta função.
    """

    logger.warning(
        "Callback perdeu transição atômica da execução",
        extra={
            "event": "execution.result.atomic_conflict",
            "category": "SYSTEM",
            "component": "execution_result",
            "ui_visible": True,

            "status": "conflict",
            "action": "finalize_execution_result",
            "reason": "execution_result_atomic_conflict",

            "execution_id": execution_id,
            "agent_id": agent_id,

            "current_status": current_status,
            "received_status": received_status,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )