"""
Gerenciamento do bloqueio automático da sessão Windows
quando um Agent do DUET permanece ocioso.

Responsabilidades deste módulo:

- aguardar uma janela de tolerância após o fim de uma execução;
- verificar se existe outra execução queued/running para o Agent;
- confirmar com o próprio Agent que ele continua idle;
- verificar novamente a fila antes do bloqueio;
- solicitar POST /session/lock ao Agent;
- cancelar/substituir timers antigos do mesmo Agent.

IMPORTANTE:

Este módulo NÃO executa LockWorkStation diretamente.

O bloqueio real continua pertencendo ao RPA-Agent através de:

    POST /session/lock

Assim preservamos a separação:

Control Room
    -> decide QUANDO bloquear

Agent
    -> decide se localmente é SEGURO bloquear
    -> executa o bloqueio real na sessão Windows
"""

from __future__ import annotations


import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

import requests


from database import SessionLocal
from models import Agent, Execution

from agents.token_security import (
    descriptografar_agent_token,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Tempo padrão durante o qual a sessão permanece desbloqueada
# depois que uma execução termina.
#
# Durante esse período outra automação poderá chegar sem que
# seja necessário bloquear e desbloquear o Windows novamente.
DEFAULT_IDLE_LOCK_DELAY_SECONDS = 30.0


# Timeout para consultas simples ao Agent.
AGENT_STATUS_TIMEOUT_SECONDS = 10.0


# Timeout maior para o bloqueio porque o Agent também confirma
# através do session_manager que o Windows ficou realmente locked.
AGENT_LOCK_TIMEOUT_SECONDS = 20.0


# ============================================================
# CONEXÃO TRANSITÓRIA COM O AGENT
# ============================================================

@dataclass
class AgentConnection:
    """
    Dados necessários somente durante a comunicação técnica
    Control Room -> Agent.

    O token possui repr=False para diminuir o risco de
    exposição acidental em logs/debug.
    """

    host: str
    port: int
    token: str = field(
        repr=False
    )


# ============================================================
# TIMERS POR AGENT
# ============================================================
#
# Mantemos no máximo um Timer de idle por Agent dentro deste
# processo do Control Room.
#
# Exemplo:
#
#   Robot A termina
#       -> timer 30s
#
#   Robot B termina antes dos 30s
#       -> cancela timer antigo
#       -> cria novo timer de 30s
#
# Dessa forma não acumulamos várias verificações atrasadas
# para o mesmo Agent.
# ============================================================

_idle_timers: dict[
    str,
    threading.Timer,
] = {}


_idle_timers_lock = (
    threading.Lock()
)


# ============================================================
# CONSULTAR TRABALHO PENDENTE
# ============================================================

def _existe_trabalho_pendente(
    agent_id: str,
) -> bool:
    """
    Verifica no banco do Control Room se existe trabalho que
    ainda ocupa ou aguarda o Agent.

    Consideramos trabalho pendente:

        running
            execução atualmente ativa;

        queued
            execução aguardando para esse Agent.

    O Control Room é a fonte correta dessa informação porque
    o Agent conhece somente seu estado operacional local.
    """

    db = SessionLocal()

    try:

        execucao = (
            db.query(
                Execution.id
            )
            .filter(
                Execution.agent_id
                ==
                agent_id,

                Execution.status.in_(
                    (
                        "queued",
                        "running",
                    )
                ),
            )
            .first()
        )

        return (
            execucao is not None
        )

    finally:

        db.close()


# ============================================================
# OBTER CONEXÃO DO AGENT
# ============================================================

def _obter_conexao_agent(
    agent_id: str,
) -> Optional[AgentConnection]:
    """
    Carrega host, porta e token técnico do Agent.

    O token é descriptografado somente quando realmente
    precisamos realizar comunicação com o Agent.

    Ele não é persistido novamente e não é colocado em logs.
    """

    db = SessionLocal()

    try:

        agent = (
            db.query(
                Agent
            )
            .filter(
                Agent.agent_id
                ==
                agent_id
            )
            .first()
        )

        if not agent:

            logger.warning(
                "Agent não encontrado durante verificação de idle",
                extra={
                    "event": "agent_idle_agent_not_found",
                    "agent_id": agent_id,
                },
            )

            return None


        # Copiamos somente valores escalares antes de fechar
        # a sessão SQLAlchemy.
        host = agent.host
        port = agent.port
        token_encrypted = (
            agent.agent_token_encrypted
        )

    finally:

        db.close()


    if (
        not host
        or not port
        or not token_encrypted
    ):

        logger.warning(
            "Agent sem dados de comunicação para bloqueio idle",
            extra={
                "event": "agent_idle_connection_missing",
                "agent_id": agent_id,
            },
        )

        return None


    agent_token = (
        descriptografar_agent_token(
            token_encrypted
        )
    )


    return AgentConnection(
        host=host,
        port=int(
            port
        ),
        token=agent_token,
    )


# ============================================================
# CONFIRMAR ESTADO LOCAL DO AGENT
# ============================================================

def _agent_continua_idle(
    *,
    agent_id: str,
    connection: AgentConnection,
) -> bool:
    """
    Confirma com o próprio Agent que não existe Robot
    atualmente em execução.

    Esta é uma segunda camada de proteção além da consulta
    ao banco do Control Room.
    """

    url = (
        f"http://{connection.host}:"
        f"{connection.port}"
        f"/execution/status"
    )

    try:

        response = requests.get(
            url,
            headers={
                "Authorization": (
                    f"Bearer {connection.token}"
                )
            },
            timeout=(
                AGENT_STATUS_TIMEOUT_SECONDS
            ),
        )

        response.raise_for_status()

        resultado = response.json()

    except Exception as error:

        logger.warning(
            "Não foi possível confirmar estado idle do Agent",
            extra={
                "event": "agent_idle_status_failed",
                "agent_id": agent_id,
                "error_type": (
                    type(error).__name__
                ),
                "error_message": str(
                    error
                ),
            },
        )

        return False


    return (
        resultado.get(
            "status"
        )
        ==
        "success"
        and
        resultado.get(
            "execution_status"
        )
        ==
        "idle"
    )


# ============================================================
# SOLICITAR BLOQUEIO AO AGENT
# ============================================================

def _solicitar_bloqueio(
    *,
    agent_id: str,
    connection: AgentConnection,
) -> bool:
    """
    Solicita ao Agent o bloqueio da sessão Windows.

    Mesmo neste ponto o Agent ainda possui sua própria
    proteção local.

    Portanto, se uma execução tiver começado na pequena
    janela entre nossa última verificação e esta chamada,
    /session/lock responderá agent_busy e NÃO bloqueará.
    """

    url = (
        f"http://{connection.host}:"
        f"{connection.port}"
        f"/session/lock"
    )

    try:

        response = requests.post(
            url,
            headers={
                "Authorization": (
                    f"Bearer {connection.token}"
                )
            },
            timeout=(
                AGENT_LOCK_TIMEOUT_SECONDS
            ),
        )

        response.raise_for_status()

        resultado = response.json()

    except Exception as error:

        logger.warning(
            "Falha ao solicitar bloqueio idle ao Agent",
            extra={
                "event": "agent_idle_lock_request_failed",
                "agent_id": agent_id,
                "error_type": (
                    type(error).__name__
                ),
                "error_message": str(
                    error
                ),
            },
        )

        return False


    if resultado.get(
        "success"
    ):

        logger.info(
            "Sessão Windows bloqueada após período de idle",
            extra={
                "event": "agent_idle_session_locked",
                "agent_id": agent_id,
                "lock_status": resultado.get(
                    "status"
                ),
            },
        )

        return True


    # agent_busy não é erro.
    #
    # Significa apenas que uma execução começou durante
    # a janela de concorrência e o próprio Agent protegeu
    # corretamente a sessão.
    if (
        resultado.get(
            "status"
        )
        ==
        "agent_busy"
    ):

        logger.info(
            "Bloqueio idle cancelado porque Agent ficou ocupado",
            extra={
                "event": "agent_idle_lock_cancelled_busy",
                "agent_id": agent_id,
                "execution_id": resultado.get(
                    "execution_id"
                ),
            },
        )

        return False


    logger.warning(
        "Agent recusou bloqueio automático da sessão",
        extra={
            "event": "agent_idle_lock_rejected",
            "agent_id": agent_id,
            "lock_status": resultado.get(
                "status"
            ),
            "message": resultado.get(
                "message"
            ),
        },
    )

    return False


# ============================================================
# EXECUTAR VERIFICAÇÃO APÓS O DELAY
# ============================================================

def _verificar_e_bloquear_agent_ocioso(
    *,
    agent_id: str,
):
    """
    Executa a verificação completa de idle depois que o Timer
    configurado para o Agent vence.

    Ordem das proteções:

    1. Control Room verifica queued/running;
    2. Agent confirma execution_status=idle;
    3. Control Room verifica queued/running novamente;
    4. Agent /session/lock faz a proteção local final.
    """

    connection = None

    try:

        # ----------------------------------------------------
        # 1. PRIMEIRA VERIFICAÇÃO DO BANCO
        # ----------------------------------------------------

        if _existe_trabalho_pendente(
            agent_id
        ):

            logger.info(
                "Bloqueio idle cancelado: Agent possui trabalho pendente",
                extra={
                    "event": "agent_idle_lock_cancelled_work",
                    "agent_id": agent_id,
                    "check": "before_agent_status",
                },
            )

            return


        # ----------------------------------------------------
        # 2. CARREGA CONEXÃO SOMENTE QUANDO NECESSÁRIO
        # ----------------------------------------------------

        connection = (
            _obter_conexao_agent(
                agent_id
            )
        )

        if connection is None:
            return


        # ----------------------------------------------------
        # 3. CONFIRMA ESTADO LOCAL DO AGENT
        # ----------------------------------------------------

        if not _agent_continua_idle(
            agent_id=agent_id,
            connection=connection,
        ):

            logger.info(
                "Bloqueio idle cancelado: Agent não está idle",
                extra={
                    "event": "agent_idle_lock_cancelled_not_idle",
                    "agent_id": agent_id,
                },
            )

            return


        # ----------------------------------------------------
        # 4. SEGUNDA VERIFICAÇÃO DO BANCO
        # ----------------------------------------------------
        #
        # Uma execução pode ter entrado na fila enquanto
        # consultávamos /execution/status.
        # ----------------------------------------------------

        if _existe_trabalho_pendente(
            agent_id
        ):

            logger.info(
                "Bloqueio idle cancelado: novo trabalho detectado",
                extra={
                    "event": "agent_idle_lock_cancelled_work",
                    "agent_id": agent_id,
                    "check": "before_lock",
                },
            )

            return


        # ----------------------------------------------------
        # 5. SOLICITA BLOQUEIO
        # ----------------------------------------------------

        _solicitar_bloqueio(
            agent_id=agent_id,
            connection=connection,
        )


    except Exception as error:

        # O mecanismo de segurança/housekeeping jamais deve
        # alterar o resultado final de uma execução já concluída.
        logger.exception(
            "Erro durante verificação automática de idle do Agent",
            extra={
                "event": "agent_idle_check_failed",
                "agent_id": agent_id,
                "error_type": (
                    type(error).__name__
                ),
                "error_message": str(
                    error
                ),
            },
        )


    finally:

        # Remove nossa referência ao token assim que a
        # comunicação técnica termina.
        #
        # Strings Python são imutáveis e não conseguimos
        # garantir sobrescrita física da memória, mas evitamos
        # manter a referência além do necessário.
        if connection is not None:
            connection.token = ""


# ============================================================
# AGENDAR VERIFICAÇÃO DE IDLE
# ============================================================

def agendar_verificacao_bloqueio_idle(
    *,
    agent_id: str,
    delay_seconds: float = (
        DEFAULT_IDLE_LOCK_DELAY_SECONDS
    ),
):
    """
    Agenda uma verificação futura de ociosidade para determinado
    Agent.

    Existe no máximo um Timer ativo por Agent dentro deste
    processo do Control Room.

    Uma nova chamada substitui o Timer anterior.
    """

    if not agent_id:

        logger.warning(
            "Tentativa de agendar idle sem agent_id",
            extra={
                "event": "agent_idle_schedule_invalid",
            },
        )

        return


    delay_seconds = max(
        0.0,
        float(
            delay_seconds
        ),
    )


    with _idle_timers_lock:

        timer_anterior = (
            _idle_timers.get(
                agent_id
            )
        )

        if timer_anterior is not None:

            timer_anterior.cancel()


        timer = threading.Timer(
            delay_seconds,
            _verificar_e_bloquear_agent_ocioso,
            kwargs={
                "agent_id": agent_id,
            },
        )

        # O Timer não pode impedir o encerramento normal
        # do processo do Control Room.
        timer.daemon = True


        _idle_timers[
            agent_id
        ] = timer


        timer.start()


    logger.info(
        "Verificação de idle agendada para o Agent",
        extra={
            "event": "agent_idle_check_scheduled",
            "agent_id": agent_id,
            "delay_seconds": delay_seconds,
        },
    )