# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DE INÍCIO
# ============================================================
#
# Responsável exclusivamente pelos eventos técnicos entre
# o envio de /execution/run e a confirmação de que o processo
# do Robot realmente foi iniciado no Agent.
#
# Este módulo registra:
#
# - timeout de confirmação;
# - falha de comunicação;
# - comando recusado;
# - resposta inválida;
# - sucesso informado sem PID;
# - falha informada pelo Agent antes do processo iniciar.
#
# Este módulo NÃO:
#
# - envia o comando HTTP;
# - altera Execution;
# - persiste PID;
# - executa Robot;
# - reconcilia Executions.
#
# ============================================================

import logging

from typing import Any, Mapping


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# TIMEOUT NA CONFIRMAÇÃO
# ============================================================

def registrar_timeout_inicio_execucao(
    *,
    contexto_log: Mapping[str, Any],
    error: Exception,
) -> None:
    """
    Registra timeout depois do envio do comando de execução.

    O resultado permanece indeterminado porque o Agent pode
    ter recebido e iniciado o processo mesmo sem a resposta
    HTTP chegar ao Control Room.
    """

    logger.warning(
        "Timeout ao aguardar confirmação de início do Agent",
        extra={
            **contexto_log,

            "event":
                "execution.start.confirmation.timeout",

            "category": "INTEGRATION",
            "component": "execution_start",
            "ui_visible": True,

            "status": "running",
            "action": "start_execution",
            "reason": "execution_start_timeout",
            "result": "indeterminate",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# FALHA DE COMUNICAÇÃO
# ============================================================

def registrar_falha_comunicacao_inicio_execucao(
    *,
    contexto_log: Mapping[str, Any],
    error: Exception,
) -> None:
    """
    Registra falha de transporte depois do envio do comando
    de início.

    O resultado permanece indeterminado.
    """

    logger.error(
        "Falha de comunicação ao aguardar início da execução",
        extra={
            **contexto_log,

            "event":
                "execution.start.communication.failed",

            "category": "INTEGRATION",
            "component": "execution_start",
            "ui_visible": True,

            "status": "running",
            "action": "start_execution",
            "reason": "execution_start_request_failed",
            "result": "indeterminate",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# COMANDO RECUSADO
# ============================================================

def registrar_comando_execucao_recusado(
    *,
    contexto_log: Mapping[str, Any],
    http_status: int,
) -> None:
    """
    Registra quando o Agent rejeita explicitamente o comando
    de execução.
    """

    logger.error(
        "Agent recusou o comando de execução",
        extra={
            **contexto_log,

            "event": "execution.start.rejected",
            "category": "INTEGRATION",
            "component": "execution_start",
            "ui_visible": True,

            "status": "failed",
            "action": "start_execution",
            "reason": "execution_command_rejected",

            "status_before": "running",
            "status_after": "error",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),

            "http_status": http_status,
        },
    )


# ============================================================
# RESPOSTA INVÁLIDA
# ============================================================

def registrar_json_invalido_inicio_execucao(
    *,
    contexto_log: Mapping[str, Any],
) -> None:
    """
    Registra quando a resposta do Agent ao comando de início
    não pode ser interpretada.
    """

    logger.error(
        "Agent retornou JSON inválido ao iniciar execução",
        extra={
            **contexto_log,

            "event":
                "execution.start.invalid_response",

            "category": "INTEGRATION",
            "component": "execution_start",
            "ui_visible": True,

            "status": "failed",
            "action": "start_execution",
            "reason": "execution_start_invalid_json",

            "status_before": "running",
            "status_after": "error",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),
        },
    )


# ============================================================
# SUCESSO INFORMADO SEM PID
# ============================================================

def registrar_execucao_iniciada_sem_pid(
    *,
    contexto_log: Mapping[str, Any],
) -> None:
    """
    Registra inconsistência em que o Agent informa sucesso,
    mas não devolve o PID do processo iniciado.
    """

    logger.error(
        "Agent informou execução iniciada sem PID",
        extra={
            **contexto_log,

            "event": "execution.start.pid.missing",
            "category": "SYSTEM",
            "component": "execution_start",
            "ui_visible": True,

            "status": "failed",
            "action": "validate_execution_start",
            "reason": "execution_started_without_pid",

            "status_before": "running",
            "status_after": "error",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),
        },
    )


# ============================================================
# PROCESSO NÃO FOI INICIADO
# ============================================================

def registrar_falha_inicio_execucao(
    *,
    contexto_log: Mapping[str, Any],
    error_message: str | None,
) -> None:
    """
    Registra quando o Agent informa que não conseguiu criar
    ou iniciar o processo do Robot.

    Esse evento representa falha antes do Robot efetivamente
    começar a executar.
    """

    logger.error(
        "Agent não conseguiu iniciar o Robot",
        extra={
            **contexto_log,

            "event": "execution.start.failed",
            "category": "SYSTEM",
            "component": "execution_start",
            "ui_visible": True,

            "status": "failed",
            "action": "start_execution",
            "reason": "execution_start_failed",

            "status_before": "running",
            "status_after": "error",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),

            "error_message": error_message,
        },
    )