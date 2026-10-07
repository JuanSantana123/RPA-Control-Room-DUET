# ============================================================
# OBSERVABILIDADE - SCHEDULER
# ============================================================
#
# Centraliza eventos técnicos importantes relacionados ao
# Scheduler do DUET.
#
# Este módulo NÃO:
#
# - executa agendamentos;
# - altera schedules;
# - cria executions;
# - controla o loop do Scheduler.
#
# O objetivo é manter observabilidade separada das regras
# de negócio e do mecanismo de execução.
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA NO CICLO PRINCIPAL DO SCHEDULER
# ============================================================

def registrar_falha_ciclo_scheduler(
    *,
    error: Exception,
) -> None:
    """
    Registra uma falha técnica não tratada durante um ciclo
    do Scheduler.

    Como existe uma exceção real, o traceback completo é
    preservado para diagnóstico.
    """

    logger.exception(
        "Erro no ciclo do Scheduler",
        extra={
            "event": "scheduler.cycle.failed",
            "category": "SYSTEM",
            "component": "scheduler",
            "ui_visible": True,

            "status": "failed",
            "action": "process_scheduler_cycle",
            "reason": "scheduler_cycle_failed",

            "resource_type": "scheduler",

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )

# ============================================================
# FALHA NA MATERIALIZAÇÃO DE OCORRÊNCIA
# ============================================================

def registrar_falha_materializacao_ocorrencia_scheduler(
    *,
    schedule_id: int,
    error: Exception,
) -> None:
    """
    Registra falha técnica durante a materialização de uma
    ocorrência de agendamento.

    Como existe uma exceção real, o traceback completo é
    preservado para diagnóstico.
    """

    logger.exception(
        "Falha ao materializar ocorrência do Scheduler",
        extra={
            "event": "schedule.occurrence.materialization.failed",
            "category": "SYSTEM",
            "component": "scheduler",
            "ui_visible": True,

            "status": "failed",
            "action": "materialize_schedule_occurrence",
            "reason": "schedule_occurrence_materialization_failed",

            "schedule_id": schedule_id,

            "resource_type": "schedule",
            "resource_id": schedule_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )

# ============================================================
# ROBOT DO AGENDAMENTO NÃO ENCONTRADO
# ============================================================

def registrar_robot_agendamento_nao_encontrado(
    *,
    schedule_id: int,
    robot_id: int,
) -> None:
    """
    Registra inconsistência em que um agendamento referencia
    um Robot que não pôde ser localizado.

    Não existe exceção neste cenário, portanto nenhum traceback
    artificial é gerado.
    """

    logger.error(
        "Robot do agendamento não encontrado",
        extra={
            "event": "schedule.robot.not_found",
            "category": "SYSTEM",
            "component": "scheduler",
            "ui_visible": True,

            "status": "failed",
            "action": "resolve_schedule_robot",
            "reason": "schedule_robot_not_found",

            "schedule_id": schedule_id,
            "robot_id": robot_id,

            "resource_type": "schedule",
            "resource_id": schedule_id,
        },
    )


# ============================================================
# ROBOT SEM VERSÃO PUBLICADA
# ============================================================

def registrar_robot_sem_versao_publicada(
    *,
    schedule_id: int,
    robot_id: int,
) -> None:
    """
    Registra inconsistência em que um Schedule referencia um
    Robot existente, mas sem versão publicada para execução.

    Não existe exceção neste cenário, portanto nenhum traceback
    é gerado.
    """

    logger.error(
        "Robot do agendamento não possui versão publicada",
        extra={
            "event": "schedule.robot.version.missing",
            "category": "SYSTEM",
            "component": "scheduler",
            "ui_visible": True,

            "status": "failed",
            "action": "resolve_robot_version",
            "reason": "robot_version_missing",

            "schedule_id": schedule_id,
            "robot_id": robot_id,

            "resource_type": "schedule",
            "resource_id": schedule_id,
        },
    )

# ============================================================
# TIMEOUT AO FINALIZAR SCHEDULER
# ============================================================

def registrar_timeout_parada_scheduler() -> None:
    """
    Registra quando a thread do Scheduler não consegue
    finalizar dentro do prazo definido para shutdown.

    Não existe exceção neste cenário, portanto nenhum
    traceback artificial é gerado.
    """

    logger.warning(
        "Scheduler não finalizou dentro do prazo",
        extra={
            "event": "scheduler.stop.timeout",
            "category": "SYSTEM",
            "component": "scheduler",
            "ui_visible": True,

            "status": "failed",
            "action": "stop_scheduler",
            "reason": "scheduler_stop_timeout",

            "resource_type": "scheduler",
        },
    )