# ============================================================
# OBSERVABILIDADE - AGENTS
# ============================================================
#
# Centraliza eventos técnicos importantes relacionados aos
# Agents do DUET.
#
# Este módulo NÃO:
#
# - processa heartbeat;
# - altera status do Agent;
# - consulta banco;
# - autentica agent_token;
# - registra o agent_token recebido;
# - registra hash ou ciphertext do token.
#
# O objetivo é manter os eventos de observabilidade separados
# das regras de negócio.
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# AGENT OFFLINE
# ============================================================

def registrar_agent_offline(
    *,
    agent_id: str,
    agent_name: str | None = None,
    agent_host: str | None = None,
    agent_port: int | None = None,
) -> None:
    """
    Registra a transição real de um Agent para offline.

    Este evento deve ser emitido somente uma vez na mudança:

        online -> offline

    Os ciclos seguintes do monitor não devem gerar novos eventos
    enquanto o Agent continuar offline.
    """

    logger.warning(
        "Agent ficou offline por ausência de heartbeat",
        extra={
            "event": "agent.offline",
            "category": "SYSTEM",
            "component": "agent",
            "ui_visible": True,
            "status": "failed",
            "action": "monitor_heartbeat",
            "reason": "heartbeat_timeout",

            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_host": agent_host,
            "agent_port": agent_port,

            "resource_type": "agent",
            "resource_id": agent_id,
            "resource_name": agent_name,
        },
    )


# ============================================================
# AGENT VOLTOU ONLINE
# ============================================================

def registrar_agent_online(
    *,
    agent_id: str,
    agent_name: str | None = None,
    agent_host: str | None = None,
    agent_port: int | None = None,
) -> None:
    """
    Registra a recuperação de comunicação de um Agent.

    Este evento representa exclusivamente a transição:

        offline -> online

    Um heartbeat normal de um Agent que já está online não deve
    gerar este evento.
    """

    logger.info(
        "Agent voltou a ficar online",
        extra={
            "event": "agent.online",
            "category": "SYSTEM",
            "component": "agent",
            "ui_visible": True,
            "status": "success",
            "action": "restore_heartbeat",
            "reason": "heartbeat_restored",

            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_host": agent_host,
            "agent_port": agent_port,

            "resource_type": "agent",
            "resource_id": agent_id,
            "resource_name": agent_name,
        },
    )
# ============================================================
# FALHA DE AUTENTICAÇÃO TÉCNICA
# ============================================================

def registrar_falha_autenticacao_agent(
    *,
    reason: str,
    agent_id: str | None = None,
    agent_name: str | None = None,
) -> None:
    """
    Registra rejeição da autenticação técnica de um Agent.

    Segurança
    ---------
    Esta função NUNCA recebe ou registra:

    - agent_token;
    - hash do agent_token;
    - ciphertext do agent_token.
    """

    logger.warning(
        "Falha na autenticação técnica do Agent",
        extra={
            "event": "agent.authentication.failed",
            "category": "SECURITY",
            "component": "agent",
            "ui_visible": True,

            "status": "failed",
            "action": "authenticate",
            "reason": reason,

            "agent_id": agent_id,

            "resource_type": "agent",
            "resource_id": agent_id,
            "resource_name": agent_name,
        },
    )


# ============================================================
# FALHA NO PROCESSAMENTO DO HEARTBEAT
# ============================================================
def registrar_falha_heartbeat_agent(
    *,
    agent_id: str,
    reason: str = "heartbeat_processing_failed",
    error: Exception | None = None,
) -> None:
    """
    Registra falhas técnicas durante o processamento de heartbeat.

    Pode representar:

    - uma exceção interna durante o processamento;
    - uma inconsistência operacional detectada sem exceção.

    Nenhuma credencial técnica do Agent é registrada.
    """

    extra = {
        "event": "agent.heartbeat.failed",
        "category": "SYSTEM",
        "component": "agent",
        "ui_visible": True,

        "status": "failed",
        "action": "process_heartbeat",
        "reason": reason,

        "agent_id": agent_id,

        "resource_type": "agent",
        "resource_id": agent_id,

        "error_type": (
            type(error).__name__
            if error is not None
            else None
        ),
        "error_message": (
            str(error)
            if error is not None
            else None
        ),
    }

    # Quando existe uma exceção real, preservamos também
    # o traceback completo para diagnóstico.
    if error is not None:
        logger.exception(
            "Erro ao processar heartbeat do Agent",
            extra=extra,
        )
        return

    # Falhas técnicas detectadas de forma controlada não devem
    # fabricar traceback ou exceção inexistente.
    logger.warning(
        "Falha ao processar heartbeat do Agent",
        extra=extra,
    )
# ============================================================
# FALHA NO REGISTRO DO AGENT
# ============================================================
def registrar_falha_registro_agent(
    *,
    reason: str,
    agent_id: str | None = None,
    agent_name: str | None = None,
    agent_host: str | None = None,
    agent_port: int | str | None = None,
    error: Exception | None = None,
) -> None:
    """
    Registra falha operacional durante o processo de registro
    de um Agent no Control Room.

    Esta função não recebe nem registra agent_token, hash ou
    ciphertext de credenciais técnicas.
    """

    logger.warning(
        "Falha ao registrar Agent",
        extra={
            "event": "agent.registration.failed",
            "category": "INTEGRATION",
            "component": "agent",
            "ui_visible": True,

            "status": "failed",
            "action": "register_agent",
            "reason": reason,

            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_host": agent_host,
            "agent_port": agent_port,

            "resource_type": "agent",
            "resource_id": agent_id,
            "resource_name": agent_name,

            "error_type": (
                type(error).__name__
                if error is not None
                else None
            ),
            "error_message": (
                str(error)
                if error is not None
                else None
            ),
        },
    )