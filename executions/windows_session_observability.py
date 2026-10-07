# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DE SESSÃO WINDOWS
# ============================================================
#
# Responsável exclusivamente pelos eventos técnicos
# relacionados à preparação da sessão Windows necessária
# para executar um Robot no Agent.
#
# Este módulo registra:
#
# - falha inesperada durante preparação da sessão;
# - sessão Windows não disponível/pronta.
#
# Este módulo NÃO:
#
# - consulta o Vault;
# - resolve passwords;
# - autentica sessão Windows;
# - envia requests ao Agent;
# - altera Execution.
#
# IMPORTANTE:
#
# Credenciais, passwords, tokens ou secrets nunca devem ser
# enviados para este módulo.
#
# ============================================================

import logging

from typing import Any, Mapping


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA TÉCNICA NA PREPARAÇÃO
# ============================================================

def registrar_falha_preparacao_sessao_windows(
    *,
    contexto_log: Mapping[str, Any],
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada durante a preparação
    da sessão Windows do Agent.
    """

    logger.exception(
        "Falha inesperada ao preparar sessão Windows do Agent",
        extra={
            **contexto_log,

            "event":
                "execution.windows_session.preparation.failed",

            "category": "SYSTEM",
            "component": "windows_session",
            "ui_visible": True,

            "status": "failed",
            "action": "prepare_windows_session",
            "reason":
                "windows_session_preparation_failed",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# SESSÃO NÃO PRONTA
# ============================================================

def registrar_sessao_windows_indisponivel(
    *,
    contexto_log: Mapping[str, Any],
    session_status: str | None,
) -> None:
    """
    Registra quando a sessão Windows necessária para a
    Execution não ficou pronta.
    """

    logger.error(
        "Sessão Windows não disponível para execução",
        extra={
            **contexto_log,

            "event":
                "execution.windows_session.not_ready",

            "category": "SYSTEM",
            "component": "windows_session",
            "ui_visible": True,

            "status": "blocked",
            "action": "prepare_windows_session",
            "reason": "windows_session_not_ready",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),

            "session_status": session_status,
        },
    )