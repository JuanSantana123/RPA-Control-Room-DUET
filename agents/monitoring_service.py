# ============================================================
# SERVICE - MONITORAMENTO DE AGENTS
# ============================================================
#
# Responsável por:
#
# - detectar ausência de heartbeat;
# - marcar Agent como offline;
# - encerrar execuções running associadas ao Agent.
#
# Este módulo não possui endpoints HTTP.
# ============================================================

from datetime import datetime, timedelta
import logging
import time

from database import SessionLocal

from agents.repository import (
    listar_agents_ativos,
    listar_execucoes_running_agent,
)


logger = logging.getLogger("control_room")


def verificar_agents_offline():
    """
    Verifica Agents sem heartbeat há mais de 60 segundos.

    Ao detectar um Agent offline:
    - altera seu status;
    - encerra execuções running com erro.
    """

    db = SessionLocal()

    try:

        agora = datetime.now()
        limite = agora - timedelta(seconds=60)

        agents = listar_agents_ativos(db)

        for agent in agents:

            if (
                agent.last_heartbeat is not None
                and agent.last_heartbeat < limite
            ):

                if agent.status != "offline":

                    logger.warning(
                        "Agent ficou offline por ausência de heartbeat",
                        extra={
                            "event": "agent_offline_detected",
                            "agent_id": agent.agent_id,
                            "agent_name": agent.name,
                            "agent_host": agent.host,
                            "agent_port": agent.port,
                            "reason": "heartbeat_timeout",
                        },
                    )

                    agent.status = "offline"

                    execucoes = (
                        listar_execucoes_running_agent(
                            db,
                            agent.agent_id,
                        )
                    )

                    for execucao in execucoes:

                        execucao.status = "error"
                        execucao.finished_at = agora
                        execucao.error_message = (
                            "Agent ficou offline durante a execução"
                        )

                        logger.warning(
                            (
                                "Execução interrompida porque "
                                "o Agent ficou offline"
                            ),
                            extra={
                                "event": (
                                    "execution_interrupted_agent_offline"
                                ),
                                "execution_id": execucao.id,
                                "agent_id": agent.agent_id,
                                "agent_name": agent.name,
                                "agent_host": agent.host,
                                "agent_port": agent.port,
                                "reason": "agent_offline",
                            },
                        )

        db.commit()

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro durante monitoramento de Agents",
            extra={
                "event": "agent_monitor_error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

    finally:
        db.close()


def monitorar_agents():
    """
    Loop contínuo de monitoramento.

    Mantém a frequência original de 10 segundos.
    """

    while True:

        verificar_agents_offline()

        time.sleep(10)