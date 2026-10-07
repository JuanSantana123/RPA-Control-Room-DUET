# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DE PREFLIGHT
# ============================================================
#
# Responsável exclusivamente pelos eventos técnicos que
# impedem ou comprometem uma Execution antes do deploy/start.
#
# Este módulo cobre:
#
# - montagem do pacote de Desenvolvimento;
# - artefato físico necessário para execução;
# - comunicação com /health do Agent;
# - validação do estado online do Agent;
# - comunicação com /execution/status.
#
# Este módulo NÃO:
#
# - monta pacotes;
# - acessa banco de dados;
# - altera Agent ou Execution;
# - envia requests HTTP;
# - realiza deploy;
# - inicia Robots.
#
# ============================================================

import logging

from typing import Any, Mapping


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA AO MONTAR PACOTE DE DESENVOLVIMENTO
# ============================================================

def registrar_falha_build_pacote_desenvolvimento(
    *,
    project_id: int,
    agent_id: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica durante a criação do pacote
    temporário de um AutomationProject.
    """

    logger.exception(
        "Falha ao montar pacote de Desenvolvimento",
        extra={
            "event":
                "execution.development.package_build.failed",

            "category": "SYSTEM",
            "component": "execution_preflight",
            "ui_visible": True,

            "status": "failed",
            "action": "build_development_package",
            "reason": "development_package_build_failed",

            "project_id": project_id,
            "agent_id": agent_id,
            "user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# ARTEFATO DE EXECUÇÃO NÃO ENCONTRADO
# ============================================================

def registrar_artefato_execucao_nao_encontrado(
    *,
    contexto_log: Mapping[str, Any],
    robot_name: str | None,
    robot_filename: str | None,
) -> None:
    """
    Registra quando o artefato necessário para executar o
    Robot não existe fisicamente no Control Room.

    O caminho físico completo não é registrado.
    """

    logger.error(
        "Arquivo do Robot não encontrado no Control Room",
        extra={
            **contexto_log,

            "event": "execution.artifact.not_found",
            "category": "SYSTEM",
            "component": "execution_preflight",
            "ui_visible": True,

            "status": "failed",
            "action": "validate_execution_artifact",
            "reason": "execution_robot_file_not_found",

            "robot_name": robot_name,
            "robot_filename": robot_filename,

            "resource_type": "execution_artifact",
            "resource_name": robot_filename,
        },
    )


# ============================================================
# FALHA DE COMUNICAÇÃO COM /HEALTH
# ============================================================

def registrar_falha_health_agent(
    *,
    contexto_log: Mapping[str, Any],
    agent_name: str | None,
    error: Exception,
) -> None:
    """
    Registra falha de transporte ao consultar o endpoint
    /health do Agent.
    """

    logger.error(
        "Agent indisponível durante validação de health",
        extra={
            **contexto_log,

            "event":
                "execution.agent.health.communication.failed",

            "category": "INTEGRATION",
            "component": "agent_health",
            "ui_visible": True,

            "status": "failed",
            "action": "check_agent_health",
            "reason": "execution_agent_health_failed",

            "agent_name": agent_name,

            "resource_type": "agent",
            "resource_id": contexto_log.get(
                "agent_id"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# /HEALTH RETORNOU HTTP DE ERRO
# ============================================================

def registrar_erro_http_health_agent(
    *,
    contexto_log: Mapping[str, Any],
    agent_name: str | None,
    http_status: int,
) -> None:
    """
    Registra resposta HTTP inválida recebida do /health.
    """

    logger.error(
        "Agent respondeu com erro na validação de health",
        extra={
            **contexto_log,

            "event": "execution.agent.health.http_error",

            "category": "INTEGRATION",
            "component": "agent_health",
            "ui_visible": True,

            "status": "failed",
            "action": "check_agent_health",
            "reason": "execution_agent_health_http_error",

            "agent_name": agent_name,

            "resource_type": "agent",
            "resource_id": contexto_log.get(
                "agent_id"
            ),

            "http_status": http_status,
        },
    )


# ============================================================
# /HEALTH RETORNOU JSON INVÁLIDO
# ============================================================

def registrar_json_invalido_health_agent(
    *,
    contexto_log: Mapping[str, Any],
    agent_name: str | None,
) -> None:
    """
    Registra quando a resposta do /health não pode ser
    interpretada como JSON.
    """

    logger.error(
        "Agent retornou JSON inválido na validação de health",
        extra={
            **contexto_log,

            "event":
                "execution.agent.health.invalid_response",

            "category": "INTEGRATION",
            "component": "agent_health",
            "ui_visible": True,

            "status": "failed",
            "action": "check_agent_health",
            "reason": "execution_agent_health_invalid_json",

            "agent_name": agent_name,

            "resource_type": "agent",
            "resource_id": contexto_log.get(
                "agent_id"
            ),
        },
    )


# ============================================================
# AGENT RESPONDEU, MAS NÃO ESTÁ ONLINE
# ============================================================

def registrar_agent_nao_online_execucao(
    *,
    contexto_log: Mapping[str, Any],
    agent_name: str | None,
    health_status: str | None,
) -> None:
    """
    Registra quando o Agent responde ao /health, mas informa
    estado diferente de online.
    """

    logger.error(
        "Agent não está online para execução",
        extra={
            **contexto_log,

            "event": "execution.agent.not_online",
            "category": "SYSTEM",
            "component": "agent_health",
            "ui_visible": True,

            "status": "blocked",
            "action": "validate_agent_online",
            "reason": "execution_agent_not_online",

            "agent_name": agent_name,
            "agent_status": health_status,

            "resource_type": "agent",
            "resource_id": contexto_log.get(
                "agent_id"
            ),
        },
    )


# ============================================================
# FALHA AO CONSULTAR /EXECUTION/STATUS
# ============================================================

def registrar_falha_consulta_status_agent(
    *,
    contexto_log: Mapping[str, Any],
    agent_name: str | None,
    error: Exception,
) -> None:
    """
    Registra falha de transporte durante a consulta do status
    de execução atual do Agent.
    """

    logger.error(
        "Falha ao consultar status de execução do Agent",
        extra={
            **contexto_log,

            "event":
                "execution.agent.status.communication.failed",

            "category": "INTEGRATION",
            "component": "agent_execution_status",
            "ui_visible": True,

            "status": "failed",
            "action": "check_agent_execution_status",
            "reason": "execution_status_request_failed",

            "agent_name": agent_name,

            "resource_type": "agent",
            "resource_id": contexto_log.get(
                "agent_id"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# /EXECUTION/STATUS RETORNOU HTTP DE ERRO
# ============================================================

def registrar_erro_http_status_agent(
    *,
    contexto_log: Mapping[str, Any],
    agent_name: str | None,
    http_status: int,
) -> None:
    """
    Registra resposta HTTP inválida recebida ao consultar
    /execution/status.
    """

    logger.error(
        "Agent respondeu com erro ao consultar status de execução",
        extra={
            **contexto_log,

            "event": "execution.agent.status.http_error",

            "category": "INTEGRATION",
            "component": "agent_execution_status",
            "ui_visible": True,

            "status": "failed",
            "action": "check_agent_execution_status",
            "reason": "execution_status_http_error",

            "agent_name": agent_name,

            "resource_type": "agent",
            "resource_id": contexto_log.get(
                "agent_id"
            ),

            "http_status": http_status,
        },
    )


# ============================================================
# /EXECUTION/STATUS RETORNOU JSON INVÁLIDO
# ============================================================

def registrar_json_invalido_status_agent(
    *,
    contexto_log: Mapping[str, Any],
    agent_name: str | None,
) -> None:
    """
    Registra quando a resposta de /execution/status não pode
    ser interpretada como JSON.
    """

    logger.error(
        "Agent retornou JSON inválido ao consultar status de execução",
        extra={
            **contexto_log,

            "event":
                "execution.agent.status.invalid_response",

            "category": "INTEGRATION",
            "component": "agent_execution_status",
            "ui_visible": True,

            "status": "failed",
            "action": "check_agent_execution_status",
            "reason": "execution_status_invalid_json",

            "agent_name": agent_name,

            "resource_type": "agent",
            "resource_id": contexto_log.get(
                "agent_id"
            ),
        },
    )