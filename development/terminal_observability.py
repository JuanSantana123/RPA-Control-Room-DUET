# ============================================================
# DEVELOPMENT - TERMINAL OBSERVABILITY
# ============================================================
#
# Eventos técnicos relacionados ao terminal interativo do
# DUET Studio.
#
# Este módulo NÃO:
#
# - inicia ou encerra processos;
# - possui regras de Checkout;
# - manipula WebSocket;
# - acessa banco de dados.
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_falha_inicio_terminal(
    *,
    project_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica ao iniciar o pseudoterminal do
    AutomationProject.
    """

    logger.exception(
        "Falha técnica ao iniciar terminal do Development",
        extra={
            "event": "terminal.start.failed",
            "category": "SYSTEM",
            "component": "development_terminal",
            "ui_visible": True,
            "status": "failed",
            "action": "start_terminal",
            "reason": "terminal_start_failed",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_falha_encerramento_terminal(
    *,
    project_id: int,
    user_id: int | None,
    pid: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica ao tentar encerrar o processo do
    terminal.
    """

    logger.exception(
        "Falha técnica ao encerrar terminal do Development",
        extra={
            "event": "terminal.close.failed",
            "category": "SYSTEM",
            "component": "development_terminal",
            "ui_visible": True,
            "status": "failed",
            "action": "close_terminal",
            "reason": "terminal_process_termination_failed",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,
            "pid": pid,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_falha_websocket_terminal(
    *,
    project_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra erro inesperado da sessão WebSocket do terminal.

    Falhas específicas de start() não devem ser duplicadas aqui.
    """

    logger.exception(
        "Falha técnica no WebSocket do terminal do Development",
        extra={
            "event": "terminal.websocket.failed",
            "category": "SYSTEM",
            "component": "development_terminal",
            "ui_visible": True,
            "status": "failed",
            "action": "run_terminal_websocket",
            "reason": "unexpected_websocket_error",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_terminal_encerrado_por_perda_checkout(
    *,
    project_id: int,
    user_id: int,
) -> None:
    """
    Mantém no log técnico a informação de que o terminal foi
    encerrado após perda do Checkout.

    É comportamento esperado, portanto NÃO aparece na tela de
    Logs do Sistema.
    """

    logger.info(
        "Terminal encerrado por perda de Checkout",
        extra={
            "event": "terminal.checkout.lost",
            "category": "AUDIT",
            "component": "development_terminal",
            "ui_visible": False,
            "status": "closed",
            "action": "close_terminal",
            "reason": "checkout_lost",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,
        },
    )