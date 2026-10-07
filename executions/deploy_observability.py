# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DE DEPLOY
# ============================================================
#
# Responsável exclusivamente pelos eventos técnicos
# relacionados ao envio do pacote de execução para o Agent.
#
# Este módulo registra:
#
# - falha de comunicação durante deploy;
# - deploy rejeitado pelo Agent;
# - resposta inválida durante deploy.
#
# Este módulo NÃO:
#
# - abre arquivos;
# - envia requests HTTP;
# - altera Execution;
# - finaliza reservas;
# - executa Robots.
#
# ============================================================

import logging

from typing import Any, Mapping


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA DE COMUNICAÇÃO
# ============================================================

def registrar_falha_comunicacao_deploy(
    *,
    contexto_log: Mapping[str, Any],
    error: Exception,
) -> None:
    """
    Registra falha de transporte durante o envio do pacote
    do Robot ao Agent.
    """

    logger.error(
        "Falha de comunicação durante deploy do Robot",
        extra={
            **contexto_log,

            "event": "execution.deploy.communication.failed",
            "category": "INTEGRATION",
            "component": "execution_deploy",
            "ui_visible": True,

            "status": "failed",
            "action": "deploy_robot_to_agent",
            "reason": "robot_deploy_request_failed",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# DEPLOY RECUSADO
# ============================================================

def registrar_deploy_recusado(
    *,
    contexto_log: Mapping[str, Any],
    http_status: int,
) -> None:
    """
    Registra quando o Agent rejeita o pacote durante deploy.
    """

    logger.error(
        "Agent recusou o deploy do Robot",
        extra={
            **contexto_log,

            "event": "execution.deploy.rejected",
            "category": "INTEGRATION",
            "component": "execution_deploy",
            "ui_visible": True,

            "status": "failed",
            "action": "deploy_robot_to_agent",
            "reason": "robot_deploy_rejected",

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

def registrar_json_invalido_deploy(
    *,
    contexto_log: Mapping[str, Any],
) -> None:
    """
    Registra quando o Agent responde ao deploy com conteúdo
    que não pode ser interpretado como JSON.
    """

    logger.error(
        "Agent retornou JSON inválido durante deploy do Robot",
        extra={
            **contexto_log,

            "event": "execution.deploy.invalid_response",
            "category": "INTEGRATION",
            "component": "execution_deploy",
            "ui_visible": True,

            "status": "failed",
            "action": "deploy_robot_to_agent",
            "reason": "robot_deploy_invalid_json",

            "resource_type": "execution",
            "resource_id": contexto_log.get(
                "execution_id"
            ),
        },
    )