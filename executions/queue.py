# ============================================================
# DUET CORE - EXECUTIONS - QUEUE WORKER
# ============================================================
#
# Responsabilidade:
#
# - localizar Executions queued;
# - verificar o Agent associado;
# - manter queued enquanto Agent estiver offline/ocupado;
# - entregar a Execution ao serviço de execução;
# - respeitar o claim atômico queued -> running;
# - continuar funcionando após restart;
# - suportar múltiplos Workers concorrentes.
#
# IMPORTANTE:
#
# A Queue NÃO altera queued -> running diretamente.
#
# Essa transição pertence a executions.service._executar_robot(),
# que realiza o UPDATE condicional:
#
#     WHERE id = ?
#       AND status = 'queued'
#
# Assim apenas um Worker vence o claim.
# ============================================================

import logging
import threading
import time

import requests

from database import SessionLocal

from models import (
    Agent,
    Execution,
)

from schemas.executions import (
    ExecutionRequest,
)

from executions.logging_context import (
    obter_contexto_execucao_log,
)

from executions.service import (
    _executar_robot,
    reconciliar_execucao_running,
)

from agents.token_security import (
    descriptografar_agent_token,
)


logger = logging.getLogger(
    "control_room"
)


QUEUE_POLL_SECONDS = 5


# ============================================================
# BUSCAR CANDIDATOS
# ============================================================
def buscar_execucoes_fila():
    """
    Retorna as Executions queued ordenadas por antiguidade.

    Não aplicamos um LIMIT global fixo porque os primeiros
    registros podem pertencer a Agents offline ou ocupados.

    Um limite fixo poderia impedir indefinidamente que uma
    Execution posterior, destinada a um Agent disponível,
    fosse examinada pelo Worker.
    """

    db = SessionLocal()

    try:

        execucoes = (
            db.query(Execution)
            .filter(
                Execution.status == "queued"
            )
            .order_by(
                Execution.id.asc()
            )
            .all()
        )

        return [
            {
                "execution_id":
                    execucao.id,

                "source_type":
                    execucao.source_type,

                "robot_id":
                    execucao.robot_id,

                "project_id":
                    execucao.project_id,

                "agent_id":
                    execucao.agent_id,

                "user_id":
                    execucao.user_id,

                "schedule_id":
                    getattr(
                        execucao,
                        "schedule_id",
                        None,
                    ),

                "schedule_run_id":
                    getattr(
                        execucao,
                        "schedule_run_id",
                        None,
                    ),
            }

            for execucao in execucoes
        ]

    finally:

        db.close()
# ============================================================
# FINALIZAR QUEUED INVÁLIDA
# ============================================================

def _finalizar_queued_com_erro(
    execution_id: int,
    mensagem: str,
):
    """
    Finaliza uma Execution somente se ela AINDA estiver queued.

    O UPDATE condicional impede sobrescrever uma execução que
    outro Worker já tenha colocado em running.
    """

    db = SessionLocal()

    try:

        linhas = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id,
                Execution.status == "queued",
            )
            .update(
                {
                    Execution.status:
                        "error",

                    Execution.finished_at:
                        __import__(
                            "datetime"
                        ).datetime.now(),

                    Execution.error_message:
                        mensagem,
                },
                synchronize_session=False,
            )
        )

        if linhas == 1:
            db.commit()
            return True

        db.rollback()
        return False

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ============================================================
# PROCESSAR UMA EXECUTION
# ============================================================

def _processar_execucao_queued(
    dados: dict,
):
    """
    Tenta processar uma única Execution queued.

    Retornos principais:

        waiting
            Agent offline/ocupado.

        dispatched
            Worker venceu o claim e iniciou processamento.

        claim_lost
            outro Worker venceu.

        error
            fila inválida.
    """

    execution_id = dados["execution_id"]
    agent_id = dados["agent_id"]
    robot_id = dados["robot_id"]
    project_id = dados["project_id"]
    source_type = dados["source_type"]
    user_id = dados["user_id"]

    # ========================================================
    # CONFIRMA QUE CONTINUA QUEUED
    # ========================================================

    db = SessionLocal()

    try:

        execucao = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id,
                Execution.status == "queued",
            )
            .first()
        )

        if not execucao:

            return {
                "status": "claim_lost"
            }

        agent = (
            db.query(Agent)
            .filter(
                Agent.agent_id == agent_id
            )
            .first()
        )

        if not agent:

            _finalizar_queued_com_erro(
                execution_id,
                "Agent associado à execução não existe.",
            )

            return {
                "status": "error"
            }

        # Agent administrativamente desativado é diferente
        # de Agent temporariamente offline.
        if not agent.is_active:

            _finalizar_queued_com_erro(
                execution_id,
                "Agent associado à execução está inativo.",
            )

            return {
                "status": "error"
            }

        # Copiamos os dados necessários antes de fechar sessão.
        agent_host = agent.host
        agent_port = agent.port
        agent_status = agent.status

        agent_token_encrypted = (
            agent.agent_token_encrypted
        )

    finally:

        db.close()

    # ========================================================
    # AGENT OFFLINE
    # ========================================================
    #
    # NÃO alteramos a Execution.
    #
    # Ela permanece queued e será recuperada automaticamente
    # quando o Agent voltar.
    # ========================================================

    if agent_status != "online":

        return {
            "status": "waiting",
            "reason": "agent_offline",
        }

    # ========================================================
    # CONSULTA STATUS REAL DO AGENT
    # ========================================================

    try:

        agent_token = (
            descriptografar_agent_token(
                agent_token_encrypted
            )
        )

        response = requests.get(
            (
                f"http://{agent_host}:"
                f"{agent_port}/execution/status"
            ),
            headers={
                "Authorization":
                    f"Bearer {agent_token}"
            },
            timeout=5,
        )

    except Exception as error:

        logger.warning(
            "Agent indisponível durante processamento da fila",
            extra={
                "event":
                    "queue_agent_unreachable",
                "execution_id":
                    execution_id,
                "agent_id":
                    agent_id,
                "status":
                    "waiting",
                "error_type":
                    type(error).__name__,
            }
        )

        return {
            "status": "waiting",
            "reason": "agent_unreachable",
        }

    if response.status_code != 200:

        return {
            "status": "waiting",
            "reason": "agent_status_http_error",
        }

    try:

        status_data = response.json()

    except ValueError:

        return {
            "status": "waiting",
            "reason": "agent_invalid_json",
        }

    if (
        status_data.get(
            "execution_status"
        )
        != "idle"
    ):

        return {
            "status": "waiting",
            "reason": "agent_busy",
        }

    # ========================================================
    # DISPATCH
    # ========================================================
    #
    # Aqui dois Workers ainda podem chegar juntos.
    #
    # Isso é esperado.
    #
    # A proteção definitiva acontece dentro de
    # _executar_robot(), no claim atômico queued -> running.
    # ========================================================

    contexto_log = (
        obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=user_id,
        )
    )

    logger.info(
        "Worker tentando claim da execução queued",
        extra={
            "event":
                "queued_execution_claim_attempt",
            **contexto_log,
            "status":
                "queued",
        }
    )

    try:

        resultado = _executar_robot(
            agent_id=agent_id,
            request=ExecutionRequest(
                source_type=source_type,
                robot_id=robot_id,
                project_id=project_id,
                execution_id=execution_id,
                user_id=user_id,
            )
        )

    except Exception as error:

        logger.exception(
            "Exceção durante dispatch da Queue",
            extra={
                "event":
                    "queued_execution_dispatch_exception",
                **contexto_log,
                "status":
                    "error",
                "error_type":
                    type(error).__name__,
                "error_message":
                    str(error),
            }
        )

        # Só altera se continuar running.
        db = SessionLocal()

        try:

            linhas = (
                db.query(Execution)
                .filter(
                    Execution.id == execution_id,
                    Execution.status == "running",
                )
                .update(
                    {
                        Execution.status:
                            "error",

                        Execution.finished_at:
                            __import__(
                                "datetime"
                            ).datetime.now(),

                        Execution.error_message:
                            (
                                "Erro no processamento "
                                f"da fila: {error}"
                            ),
                    },
                    synchronize_session=False,
                )
            )

            if linhas == 1:
                db.commit()
            else:
                db.rollback()

        finally:

            db.close()

        return {
            "status": "error",
            "message": str(error),
        }

    # ========================================================
    # OUTRO WORKER VENCEU
    # ========================================================
# ========================================================
    # OUTRA EXECUTION RESERVOU O AGENT
    # ========================================================
    #
    # A Execution atual continua queued.
    #
    # Isso pode acontecer quando outro processo do Control
    # Room venceu a disputa por uma Execution diferente
    # destinada ao mesmo Agent.
    # ========================================================

    if resultado.get(
        "agent_busy"
    ):

        logger.info(
            "Agent reservado por outra execução",
            extra={
                "event":
                    "queued_execution_agent_busy",
                **contexto_log,
                "status":
                    "waiting",
            }
        )

        return {
            "status": "waiting",
            "reason": "agent_reserved",
        }
    if resultado.get(
        "claim_lost"
    ):

        logger.info(
            "Claim da Queue vencido por outro Worker",
            extra={
                "event":
                    "queued_execution_claim_lost",
                **contexto_log,
                "status":
                    "claim_lost",
            }
        )

        return {
            "status": "claim_lost"
        }

    # ========================================================
    # ERRO APÓS CLAIM
    # ========================================================

    if resultado.get("status") == "error":

        # _executar_robot já possui sua própria finalização.
        # Esta atualização é somente uma defesa condicional.
        db = SessionLocal()

        try:

            linhas = (
                db.query(Execution)
                .filter(
                    Execution.id == execution_id,
                    Execution.status == "running",
                )
                .update(
                    {
                        Execution.status:
                            "error",

                        Execution.finished_at:
                            __import__(
                                "datetime"
                            ).datetime.now(),

                        Execution.error_message:
                            resultado.get(
                                "message",
                                (
                                    "Falha ao processar "
                                    "execução da fila."
                                ),
                            ),
                    },
                    synchronize_session=False,
                )
            )

            if linhas == 1:
                db.commit()
            else:
                db.rollback()

        finally:

            db.close()

        return {
            "status": "error",
            "message": resultado.get("message"),
        }

    logger.info(
        "Execution retirada da fila",
        extra={
            "event":
                "queued_execution_dispatched",
            **contexto_log,
            "status":
                "running",
        }
    )

    return {
        "status": "dispatched",
        "execution_id": execution_id,
    }
# ============================================================
# RECONCILIA EXECUÇÕES RUNNING
# ============================================================

def reconciliar_execucoes_running():
    """
    Verifica execuções que continuam como "running" no banco.

    O objetivo NÃO é aplicar timeout ao Robot.

    O objetivo é recuperar callbacks finais perdidos consultando
    o estado persistido em memória pelo Agent.

    Uma execução somente será finalizada quando o Agent informar
    resultado terminal para o MESMO execution_id.
    """

    db = SessionLocal()

    try:

        execution_ids = [
            execution_id
            for (execution_id,) in (
                db.query(
                    Execution.id
                )
                .filter(
                    Execution.status == "running"
                )
                .order_by(
                    Execution.id.asc()
                )
                .all()
            )
        ]

    finally:

        db.close()

    for execution_id in execution_ids:

        try:

            reconciliar_execucao_running(
                execution_id=execution_id
            )

        except Exception as error:

            # Uma falha de reconciliação não pode derrubar
            # o Worker da Queue.
            logger.exception(
                "Falha ao reconciliar Execution running",
                extra={
                    "event": (
                        "execution_reconciliation_failed"
                    ),
                    "execution_id": execution_id,
                    "error_type": type(error).__name__,
                }
            )

# ============================================================
# CICLO ÚNICO DA QUEUE
# ============================================================

def processar_ciclo_fila():
    """
    Processa um lote da fila.

    Não deixa a fila inteira bloqueada porque a Execution mais
    antiga pertence a um Agent ocupado.
    """
    # ========================================================
    # 1. RECONCILIA EXECUÇÕES ABERTAS
    # ========================================================
    #
    # Fazemos isso antes de despachar a fila.
    #
    # Dessa forma uma Execution "running" cujo callback final
    # foi perdido pode ser corrigida antes de bloquear novas
    # execuções destinadas ao mesmo Agent.
    # ========================================================

    reconciliar_execucoes_running()
    execucoes = buscar_execucoes_fila()

    if not execucoes:
        return 0

    processadas = 0

    # Evita tentar enviar duas Executions para o mesmo Agent
    # durante a mesma passagem do Worker.
    agents_processados = set()

    for dados in execucoes:

        agent_id = dados["agent_id"]

        if agent_id in agents_processados:
            continue

        resultado = (
            _processar_execucao_queued(
                dados
            )
        )

        status = resultado.get(
            "status"
        )

        if status == "dispatched":

            agents_processados.add(
                agent_id
            )

            processadas += 1

        elif status == "claim_lost":

            # Outro Worker consumiu.
            continue

        elif status == "error":

            processadas += 1

    return processadas


# ============================================================
# WORKER
# ============================================================

def worker_fila_execucoes():

    logger.info(
        "Worker da fila iniciado",
        extra={
            "event":
                "execution_queue_worker_started",
            "status":
                "running",
        }
    )

    while True:

        try:

            processar_ciclo_fila()

        except Exception as error:

            logger.exception(
                "Erro inesperado no Worker da fila",
                extra={
                    "event":
                        "execution_queue_worker_error",
                    "status":
                        "error",
                    "error_type":
                        type(error).__name__,
                    "error_message":
                        str(error),
                }
            )

        time.sleep(
            QUEUE_POLL_SECONDS
        )


# ============================================================
# START CONTROLADO
# ============================================================

thread_fila = None
thread_fila_lock = threading.Lock()


def iniciar_worker_fila():
    """
    Inicia no máximo um Worker da Queue dentro deste processo.

    Vários processos ainda podem possuir Workers próprios.
    Isso é suportado pelo claim atômico no banco.
    """

    global thread_fila

    with thread_fila_lock:

        if (
            thread_fila is not None
            and thread_fila.is_alive()
        ):
            return

        thread_fila = threading.Thread(
            target=worker_fila_execucoes,
            daemon=True,
            name="RPA-Execution-Queue",
        )

        thread_fila.start()