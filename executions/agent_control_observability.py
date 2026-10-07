# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DE CONTROLE DO AGENT
# ============================================================
#
# Responsável exclusivamente pelos eventos técnicos gerados
# pelas operações de controle de execução realizadas pelo
# Control Room contra o Agent.
#
# Este módulo cobre:
#
# - consulta manual de /execution/status;
# - envio de /execution/stop;
# - respostas HTTP inválidas;
# - respostas JSON inválidas;
# - rejeição do comando de stop pelo Agent.
#
# Este módulo NÃO:
#
# - envia requests HTTP;
# - acessa banco de dados;
# - altera Execution;
# - descriptografa tokens;
# - implementa endpoints FastAPI.
#
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA DE COMUNICAÇÃO AO CONSULTAR STATUS
# ============================================================

def registrar_falha_consulta_status_agent(
    *,
    agent_id: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha de transporte durante consulta manual do
    endpoint /execution/status do Agent.
    """

    logger.error(
        "Falha ao consultar status do Agent",
        extra={
            "event":
                "execution.control.status.communication.failed",

            "category": "INTEGRATION",
            "component": "execution_control",
            "ui_visible": True,

            "status": "failed",
            "action": "query_agent_execution_status",
            "reason":
                "agent_execution_status_request_failed",

            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "agent",
            "resource_id": agent_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# ERRO HTTP AO CONSULTAR STATUS
# ============================================================

def registrar_erro_http_consulta_status_agent(
    *,
    agent_id: str,
    user_id: int | None,
    http_status: int,
) -> None:
    """
    Registra resposta HTTP de erro recebida durante consulta
    de /execution/status.
    """

    logger.error(
        "Agent respondeu com erro ao consultar status",
        extra={
            "event": "execution.control.status.http_error",

            "category": "INTEGRATION",
            "component": "execution_control",
            "ui_visible": True,

            "status": "failed",
            "action": "query_agent_execution_status",
            "reason": "agent_execution_status_http_error",

            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "agent",
            "resource_id": agent_id,

            "http_status": http_status,
        },
    )


# ============================================================
# JSON INVÁLIDO AO CONSULTAR STATUS
# ============================================================

def registrar_resposta_invalida_consulta_status_agent(
    *,
    agent_id: str,
    user_id: int | None,
) -> None:
    """
    Registra quando /execution/status responde com conteúdo
    que não pode ser interpretado como JSON.
    """

    logger.error(
        "Agent retornou JSON inválido ao consultar status",
        extra={
            "event":
                "execution.control.status.invalid_response",

            "category": "INTEGRATION",
            "component": "execution_control",
            "ui_visible": True,

            "status": "failed",
            "action": "query_agent_execution_status",
            "reason":
                "agent_execution_status_invalid_json",

            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "agent",
            "resource_id": agent_id,
        },
    )


# ============================================================
# FALHA DE COMUNICAÇÃO AO ENVIAR STOP
# ============================================================

def registrar_falha_envio_stop_agent(
    *,
    execution_id: int,
    agent_id: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha de transporte durante envio do comando
    /execution/stop ao Agent.
    """

    logger.error(
        "Falha ao enviar comando de parada ao Agent",
        extra={
            "event":
                "execution.control.stop.communication.failed",

            "category": "INTEGRATION",
            "component": "execution_control",
            "ui_visible": True,

            "status": "failed",
            "action": "stop_execution",
            "reason": "agent_execution_stop_request_failed",

            "execution_id": execution_id,
            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# ERRO HTTP AO ENVIAR STOP
# ============================================================

def registrar_erro_http_stop_agent(
    *,
    execution_id: int,
    agent_id: str,
    user_id: int | None,
    http_status: int,
) -> None:
    """
    Registra resposta HTTP de erro recebida ao enviar STOP.
    """

    logger.error(
        "Agent respondeu com erro ao parar execução",
        extra={
            "event": "execution.control.stop.http_error",

            "category": "INTEGRATION",
            "component": "execution_control",
            "ui_visible": True,

            "status": "failed",
            "action": "stop_execution",
            "reason": "agent_execution_stop_http_error",

            "execution_id": execution_id,
            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "http_status": http_status,
        },
    )


# ============================================================
# JSON INVÁLIDO AO ENVIAR STOP
# ============================================================

def registrar_resposta_invalida_stop_agent(
    *,
    execution_id: int,
    agent_id: str,
    user_id: int | None,
) -> None:
    """
    Registra quando a resposta de /execution/stop não pode
    ser interpretada como JSON.
    """

    logger.error(
        "Agent retornou JSON inválido ao parar execução",
        extra={
            "event":
                "execution.control.stop.invalid_response",

            "category": "INTEGRATION",
            "component": "execution_control",
            "ui_visible": True,

            "status": "failed",
            "action": "stop_execution",
            "reason": "agent_execution_stop_invalid_json",

            "execution_id": execution_id,
            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "execution",
            "resource_id": execution_id,
        },
    )


# ============================================================
# AGENT RECUSOU O STOP
# ============================================================

def registrar_stop_recusado_agent(
    *,
    execution_id: int,
    agent_id: str,
    user_id: int | None,
    agent_message: str | None,
) -> None:
    """
    Registra quando o Agent responde corretamente ao comando
    de stop, mas informa que a operação não foi aceita.
    """

    logger.warning(
        "Agent recusou o comando de parada",
        extra={
            "event": "execution.control.stop.rejected",

            "category": "INTEGRATION",
            "component": "execution_control",
            "ui_visible": True,

            "status": "failed",
            "action": "stop_execution",
            "reason": "agent_execution_stop_rejected",

            "execution_id": execution_id,
            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "agent_message": agent_message,
        },
    )