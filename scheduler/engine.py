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

from datetime import datetime

from core.timezone import local_now_naive

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

from scheduler.observability import (
    registrar_falha_ciclo_scheduler,
    registrar_timeout_parada_scheduler,
)

SCHEDULER_POLL_SECONDS = 5
scheduler_stop_event = threading.Event()


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

    agora = local_now_naive()

    _inicializar_proximas_execucoes(
        agora
    )

    schedule_ids = (
        _buscar_schedules_vencidos(
            agora
        )
    )

    for schedule_id in schedule_ids:

        executar_agendamento(
            schedule_id
        )


# ============================================================
# LOOP
# ============================================================

def scheduler_loop():

    logger.info(
        "Scheduler iniciado",
        extra={
            "event": "scheduler.worker.started",
            "category": "SYSTEM",
            "component": "scheduler",
            "ui_visible": False,
            "status": "running",
        },
    )

    while not scheduler_stop_event.is_set():

        try:

            processar_ciclo_scheduler()

        except Exception as error:

            registrar_falha_ciclo_scheduler(
                error=error,
            )

        scheduler_stop_event.wait(SCHEDULER_POLL_SECONDS)

    logger.info(
        "Scheduler finalizado",
        extra={
            "event": "scheduler.worker.stopped",
            "category": "SYSTEM",
            "component": "scheduler",
            "ui_visible": False,
            "status": "stopped",
        },
    )


# ============================================================
# START CONTROLADO
# ============================================================

scheduler_thread = None
scheduler_thread_lock = threading.Lock()


def scheduler_esta_ativo():
    return scheduler_thread is not None and scheduler_thread.is_alive()


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

        scheduler_stop_event.clear()
        scheduler_thread.start()


def parar_scheduler(timeout_seconds=10):
    """Solicita encerramento cooperativo e aguarda a thread do Scheduler."""

    global scheduler_thread

    with scheduler_thread_lock:
        current_thread = scheduler_thread
        if current_thread is None:
            return
        scheduler_stop_event.set()

    current_thread.join(timeout=timeout_seconds)

    if current_thread.is_alive():

        registrar_timeout_parada_scheduler()

        return

    with scheduler_thread_lock:
        if scheduler_thread is current_thread:
            scheduler_thread = None
