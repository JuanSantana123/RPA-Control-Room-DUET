# ============================================================
# DUET CORE - SCHEDULER - MATERIALIZAÇÃO DE OCORRÊNCIAS
# ============================================================
#
# Responsabilidade:
#
# Transformar UMA ocorrência vencida de um Schedule em uma
# Execution persistida com status "queued".
#
# A criação da Execution e o avanço do Schedule acontecem
# dentro da MESMA transação.
#
# Garantias:
#
# - uma ocorrência possui um schedule_run_id determinístico;
# - a mesma ocorrência não pode gerar duas Executions;
# - Schedule só avança se a Execution for persistida;
# - se a transação falhar, ambos permanecem inalterados;
# - após reinício, a Queue continua processando a Execution;
# - Schedule "once" é consumido uma única vez;
# - múltiplas ocorrências do mesmo Schedule continuam podendo
#   gerar várias Executions queued;
# - Agent offline NÃO elimina a ocorrência.
# ============================================================

import logging

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from database import SessionLocal

from models import (
    Schedule,
    Agent,
    Robot,
    Execution,
)

from scheduler.calculations import (
    proxima_execucao_apos_execucao,
)


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# IDENTIFICADOR DA OCORRÊNCIA
# ============================================================

def _criar_schedule_run_id(
    schedule_id: int,
    scheduled_for: datetime,
) -> str:
    """
    Cria o identificador determinístico de uma ocorrência.

    Exemplo:

        Schedule 23
        ocorrência 2026-09-19 14:30:00

        23:2026-09-19T14:30:00.000000

    Como Execution.schedule_run_id possui UNIQUE no banco,
    duas instâncias do Scheduler tentando materializar a mesma
    ocorrência disputarão exatamente a mesma chave.
    """

    return (
        f"{schedule_id}:"
        f"{scheduled_for.isoformat(timespec='microseconds')}"
    )


# ============================================================
# ESCOLHA DO AGENT
# ============================================================

def _selecionar_agent(
    db,
    schedule,
):
    """
    Resolve o Agent que ficará associado à Execution.

    IMPORTANTE:

    O Agent NÃO precisa estar idle e também NÃO precisa estar
    online neste momento.

    O Scheduler produz trabalho para a fila. A disponibilidade
    operacional será verificada pelo Worker.

    Isso permite:

        Agent offline
            -> Execution continua queued.

        Agent ocupado
            -> Execution continua queued.

        várias ocorrências
            -> várias Executions queued.

    Um Agent administrativamente inativo não recebe trabalho novo.
    """

    # --------------------------------------------------------
    # AGENT ESPECÍFICO
    # --------------------------------------------------------

    if schedule.agent_id:

        return (
            db.query(Agent)
            .filter(
                Agent.agent_id == schedule.agent_id,
                Agent.is_active == 1,
            )
            .first()
        )
    # ========================================================
    # --------------------------------------------------------
    # SELEÇÃO AUTOMÁTICA
    # --------------------------------------------------------
    #
    # Preferimos um Agent online, mas a ausência de um Agent
    # online não deve fazer a ocorrência desaparecer.
    # --------------------------------------------------------

    agent = (
        db.query(Agent)
        .filter(
            Agent.is_active == 1,
            Agent.status == "online",
        )
        .order_by(
            Agent.name.asc()
        )
        .first()
    )

    if agent:
        return agent

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------
    #
    # Se todos os Agents ativos estiverem offline, escolhemos
    # deterministicamente um deles e deixamos a Execution
    # aguardando na Queue.
    # --------------------------------------------------------

    return (
        db.query(Agent)
        .filter(
            Agent.is_active == 1,
        )
        .order_by(
            Agent.name.asc()
        )
        .first()
    )


# ============================================================
# MATERIALIZAR OCORRÊNCIA
# ============================================================

def executar_agendamento(
    schedule_id: int,
):
    """
    Materializa uma ocorrência vencida na fila.

    A função NÃO chama o Agent.

    A unidade transacional é:

        Schedule vencido
                +
        Execution queued
                +
        avanço do Schedule

    Tudo é confirmado em um único commit.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. CARREGA SCHEDULE ATIVO
        # ====================================================

        schedule = (
            db.query(Schedule)
            .filter(
                Schedule.id == schedule_id,
                Schedule.ativo == 1,
                Schedule.proxima_execucao.isnot(None),
            )
            .first()
        )

        if not schedule:

            return {
                "status": "ignored",
                "message": (
                    "Agendamento inexistente, inativo "
                    "ou sem próxima execução."
                ),
                "schedule_id": schedule_id,
            }

        agora = datetime.now()

        # Ainda não venceu.
        if schedule.proxima_execucao > agora:

            return {
                "status": "ignored",
                "message": "Agendamento ainda não venceu.",
                "schedule_id": schedule_id,
            }

        # ====================================================
        # 2. A OCORRÊNCIA É A DATA PROGRAMADA
        # ====================================================
        #
        # NÃO usamos datetime.now() como identidade.
        #
        # Dessa forma:
        #
        # dois Workers lendo a ocorrência das 14:30
        #
        # produzirão:
        #
        #     schedule_run_id = 23:2026-...T14:30...
        #
        # e não dois IDs diferentes.
        # ====================================================

        scheduled_for = (
            schedule.proxima_execucao
        )

        schedule_run_id = (
            _criar_schedule_run_id(
                schedule.id,
                scheduled_for,
            )
        )

        # ====================================================
        # 3. IDEMPOTÊNCIA
        # ====================================================

        execucao_existente = (
            db.query(Execution)
            .filter(
                Execution.schedule_run_id
                == schedule_run_id
            )
            .first()
        )

        if execucao_existente:

            logger.info(
                "Ocorrência do Scheduler já materializada",
                extra={
                    "event":
                        "schedule_occurrence_already_materialized",
                    "schedule_id":
                        schedule.id,
                    "schedule_run_id":
                        schedule_run_id,
                    "execution_id":
                        execucao_existente.id,
                    "status":
                        execucao_existente.status,
                }
            )

            return {
                "status": "duplicate",
                "schedule_id": schedule.id,
                "schedule_run_id": schedule_run_id,
                "execution_id": execucao_existente.id,
            }

        # ====================================================
        # 4. ROBOT
        # ====================================================

        robot = (
            db.query(Robot)
            .filter(
                Robot.id == schedule.robot_id
            )
            .first()
        )

        if not robot:

            logger.error(
                "Robot do agendamento não encontrado",
                extra={
                    "event":
                        "schedule_robot_not_found",
                    "schedule_id":
                        schedule.id,
                    "robot_id":
                        schedule.robot_id,
                    "status":
                        "error",
                }
            )

            return {
                "status": "error",
                "message": (
                    "Robot do agendamento não encontrado."
                ),
                "schedule_id": schedule.id,
            }

        # ====================================================
        # 5. AGENT
        # ====================================================

        agent = _selecionar_agent(
            db,
            schedule,
        )

        if not agent:

            # Não consumimos a ocorrência.
            #
            # Quando um Agent ativo voltar a existir,
            # o Scheduler encontrará a mesma ocorrência.
            logger.warning(
                "Nenhum Agent ativo disponível para materializar ocorrência",
                extra={
                    "event":
                        "schedule_no_active_agent",
                    "schedule_id":
                        schedule.id,
                    "schedule_run_id":
                        schedule_run_id,
                    "status":
                        "waiting",
                }
            )

            return {
                "status": "waiting",
                "message": "Nenhum Agent ativo disponível.",
                "schedule_id": schedule.id,
            }

        # ====================================================
        # 6. CRIA EXECUTION QUEUED
        # ====================================================
        #
        # started_at = None
        #
        # A execução ainda NÃO começou.
        #
        # O horário real de início será definido somente no
        # claim queued -> running.
        # ====================================================
        # ----------------------------------------------------
        # CONGELA A VERSÃO PUBLICADA NO MOMENTO DO AGENDAMENTO
        # ----------------------------------------------------

        robot_version = getattr(
            robot,
            "version",
            None
        )

        if robot_version is None:

            return {
                "status": "error",
                "message": (
                    "Robot não possui versão publicada "
                    "para execução."
                ),
            }
        execucao = Execution(
            source_type="robot",

            robot_id=robot.id,
            robot_version=robot_version,
            project_id=None,

            robot_name=robot.name,
            robot_filename=robot.filename,

            agent_id=agent.agent_id,

            # Preserva o usuário que criou o Schedule.
            user_id=schedule.user_id,

            # Proveniência Scheduler.
            schedule_id=schedule.id,
            schedule_run_id=schedule_run_id,

            status="queued",
            started_at=None,
            finished_at=None,
            error_message=None,
        )

        db.add(
            execucao
        )

        # flush obtém o ID sem confirmar a transação.
        db.flush()

        execution_id = execucao.id

        # ====================================================
        # ====================================================
        # 7. DEFINE O DESTINO DO SCHEDULE
        # ====================================================
        #
        # REGRA DE CICLO DE VIDA:
        #
        # Schedule representa somente planejamento futuro.
        # Execution representa o histórico permanente.
        #
        # A Execution desta ocorrência já foi criada e recebeu
        # um schedule_run_id determinístico antes deste ponto.
        #
        # Portanto:
        #
        # - "once":
        #       não possui futuro depois desta ocorrência;
        #       o Schedule é excluído fisicamente.
        #
        # - recorrente com próxima ocorrência:
        #       o Schedule permanece e avança normalmente.
        #
        # - recorrente sem próxima ocorrência possível:
        #       também não possui mais função futura;
        #       o Schedule é excluído fisicamente.
        #
        # A FK:
        #
        #     executions.schedule_id
        #         ON DELETE SET NULL
        #
        # garante que a remoção do Schedule NÃO apague a
        # Execution criada acima.
        #
        # schedule_run_id permanece preservado na Execution.
        # ====================================================

        schedule_id_historico = schedule.id
        schedule_user_id = schedule.user_id

        # ----------------------------------------------------
        # ONCE
        # ----------------------------------------------------

        if schedule.tipo == "once":

            # A única ocorrência já foi materializada.
            #
            # Não deixamos Schedule inativo/morto armazenado.
            db.delete(schedule)

        # ----------------------------------------------------
        # RECORRENTE
        # ----------------------------------------------------

        else:

            # Calcula a próxima ocorrência a partir do horário
            # PROGRAMADO, evitando drift no Scheduler.
            schedule.ultima_execucao = (
                scheduled_for
            )

            schedule.proxima_execucao = (
                proxima_execucao_apos_execucao(
                    schedule,
                    scheduled_for,
                )
            )

            # Se não existe mais nenhuma ocorrência futura,
            # este Schedule também perdeu sua finalidade.
            #
            # Nesse caso ele é removido fisicamente em vez de
            # permanecer como registro inativo no banco.
            if schedule.proxima_execucao is None:

                db.delete(schedule)

        # ====================================================
        # 8. COMMIT ÚNICO
        # ====================================================

        db.commit()

        logger.info(
            "Ocorrência do Scheduler adicionada à fila",
            extra={
                "event":
                    "schedule_occurrence_queued",
                "schedule_id":
                    schedule_id_historico,
                "schedule_run_id":
                    schedule_run_id,
                "execution_id":
                    execution_id,
                "robot_id":
                    robot.id,
                "agent_id":
                    agent.agent_id,
                "user_id":
                    schedule_user_id,
                "status":
                    "queued",
            }
        )

        return {
            "status": "queued",
            "schedule_id": schedule_id_historico,
            "schedule_run_id": schedule_run_id,
            "execution_id": execution_id,
            "agent_id": agent.agent_id,
        }

    # ========================================================
    # UNIQUE(schedule_run_id)
    # ========================================================
    #
    # Outro Scheduler pode ter vencido a corrida.
    #
    # Nesse caso NÃO é erro funcional e, principalmente,
    # NÃO criamos outra Execution.
    # ========================================================

    except IntegrityError:

        db.rollback()

        logger.info(
            "Ocorrência já consumida por outro Scheduler",
            extra={
                "event":
                    "schedule_occurrence_claim_lost",
                "schedule_id":
                    schedule_id,
                "status":
                    "duplicate",
            }
        )

        return {
            "status": "duplicate",
            "message": (
                "Ocorrência já materializada "
                "por outro Scheduler."
            ),
            "schedule_id": schedule_id,
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao materializar ocorrência do Scheduler",
            extra={
                "event":
                    "schedule_occurrence_materialization_failed",
                "schedule_id":
                    schedule_id,
                "status":
                    "error",
                "error_type":
                    type(error).__name__,
                "error_message":
                    str(error),
            }
        )

        return {
        "status": "error",
        "message": (
            "Não foi possível materializar "
            "a ocorrência do agendamento."
        ),
        "schedule_id": schedule_id,
    }

    finally:

        db.close()