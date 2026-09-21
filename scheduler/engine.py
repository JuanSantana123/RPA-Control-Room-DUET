# ============================================================
# DUET CORE - SCHEDULER - ENGINE
# ============================================================
#
# Responsabilidade:
#
# - inicializar próximas execuções;
# - localizar Schedules vencidos;
# - materializar ocorrências na fila;
# - recuperar ocorrências vencidas após restart;
# - manter apenas uma thread Scheduler por processo.
#
# A proteção global contra múltiplos PROCESSOS não depende
# desta thread: a idempotência real está no banco através de
# Execution.schedule_run_id UNIQUE.
# ============================================================

import logging
import threading
import time

from datetime import datetime

from database import SessionLocal
from models import Schedule

from scheduler.calculations import (
    calcular_proxima_execucao,
)

from scheduler.execution import (
    executar_agendamento,
)


logger = logging.getLogger(
    "control_room"
)


SCHEDULER_POLL_SECONDS = 5


# ============================================================
# INICIALIZA SCHEDULES SEM PRÓXIMA EXECUÇÃO
# ============================================================

def _inicializar_proximas_execucoes(
    agora: datetime,
):
    """
    Inicializa proxima_execucao somente para Schedules ativos
    que ainda não possuem valor persistido.

    Isso também permite recuperar corretamente Schedules
    existentes depois do restart do Control Room.
    """

    db = SessionLocal()

    try:

        schedules = (
            db.query(Schedule)
            .filter(
                Schedule.ativo == 1,
                Schedule.proxima_execucao.is_(None),
            )
            .all()
        )

        alterado = False

        for schedule in schedules:

            proxima = calcular_proxima_execucao(
                schedule,
                agora,
            )

            if proxima is not None:

                schedule.proxima_execucao = proxima
                alterado = True

        if alterado:
            db.commit()

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ============================================================
# BUSCA SCHEDULES VENCIDOS
# ============================================================

def _buscar_schedules_vencidos(
    agora: datetime,
):
    """
    Retorna somente IDs.

    Objetos SQLAlchemy não atravessam a fronteira da sessão.
    """

    db = SessionLocal()

    try:

        schedules = (
            db.query(Schedule)
            .filter(
                Schedule.ativo == 1,
                Schedule.proxima_execucao.isnot(None),
                Schedule.proxima_execucao <= agora,
            )
            .order_by(
                Schedule.proxima_execucao.asc(),
                Schedule.id.asc(),
            )
            .all()
        )

        return [
            schedule.id
            for schedule in schedules
        ]

    finally:

        db.close()


# ============================================================
# CICLO ÚNICO
# ============================================================

def processar_ciclo_scheduler():
    """
    Executa uma passagem completa do Scheduler.

    Função separada do while para facilitar validação e teste
    sem precisar criar uma thread infinita.
    """

    agora = datetime.now()

    _inicializar_proximas_execucoes(
        agora
    )

    schedule_ids = (
        _buscar_schedules_vencidos(
            agora
        )
    )

    for schedule_id in schedule_ids:

        resultado = executar_agendamento(
            schedule_id
        )

        # O resultado fica registrado de forma estruturada.
        logger.info(
            "Ciclo do Scheduler processou agendamento",
            extra={
                "event":
                    "scheduler_schedule_processed",
                "schedule_id":
                    schedule_id,
                "result_status":
                    (
                        resultado.get("status")
                        if isinstance(resultado, dict)
                        else None
                    ),
                "status":
                    "success",
            }
        )


# ============================================================
# LOOP
# ============================================================

def scheduler_loop():

    logger.info(
        "Scheduler iniciado",
        extra={
            "event": "scheduler_worker_started",
            "status": "running",
        }
    )

    while True:

        try:

            processar_ciclo_scheduler()

        except Exception as error:

            logger.exception(
                "Erro no ciclo do Scheduler",
                extra={
                    "event":
                        "scheduler_cycle_failed",
                    "status":
                        "error",
                    "error_type":
                        type(error).__name__,
                    "error_message":
                        str(error),
                }
            )

        time.sleep(
            SCHEDULER_POLL_SECONDS
        )


# ============================================================
# START CONTROLADO
# ============================================================

scheduler_thread = None
scheduler_thread_lock = threading.Lock()


def iniciar_scheduler():
    """
    Inicia no máximo uma thread Scheduler dentro do processo.

    A proteção entre processos é feita pelo banco através
    da identidade única da ocorrência.
    """

    global scheduler_thread

    with scheduler_thread_lock:

        if (
            scheduler_thread is not None
            and scheduler_thread.is_alive()
        ):
            return

        scheduler_thread = threading.Thread(
            target=scheduler_loop,
            daemon=True,
            name="RPA-Scheduler",
        )

        scheduler_thread.start()