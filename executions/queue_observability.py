# ============================================================
# DUET - EXECUTIONS - OBSERVABILIDADE DA FILA
# ============================================================
#
# Responsável exclusivamente pelos eventos técnicos
# relacionados à fila de Executions.
#
# Este módulo registra:
#
# - falhas durante dispatch;
# - falhas durante reconciliação;
# - falhas do Worker da fila;
# - timeout de shutdown do Worker;
# - falhas ao persistir nova Execution queued.
#
# Este módulo NÃO:
#
# - executa Robots;
# - realiza deploy para Agents;
# - prepara sessão Windows;
# - controla o loop da fila;
# - altera estado de Execution;
# - acessa banco de dados.
#
# ============================================================

import logging

from typing import Any, Mapping


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA TÉCNICA DURANTE DISPATCH
# ============================================================

def registrar_falha_dispatch_execucao(
    *,
    contexto_log: Mapping[str, Any],
    error: Exception,
) -> None:
    """
    Registra uma exceção técnica ocorrida durante o dispatch
    de uma Execution retirada da fila.

    O contexto estruturado produzido pela camada de execução
    é preservado integralmente.

    Como esta função é chamada dentro de um bloco except,
    logger.exception() preserva também o traceback real.
    """

    logger.exception(
        "Exceção durante dispatch da Queue",
        extra={
            **contexto_log,

            "event": "execution.dispatch.failed",
            "category": "SYSTEM",
            "component": "execution_queue",
            "ui_visible": True,

            "status": "failed",
            "action": "dispatch_execution",
            "reason": "execution_dispatch_exception",

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# FALHA NA RECONCILIAÇÃO
# ============================================================

def registrar_falha_reconciliacao_execucao(
    *,
    execution_id: int,
    error: Exception,
) -> None:
    """
    Registra falha técnica durante a reconciliação de uma
    Execution que permanece em estado running.

    A falha não encerra o Worker da fila.
    """

    logger.exception(
        "Falha ao reconciliar Execution running",
        extra={
            "event": "execution.reconciliation.failed",
            "category": "SYSTEM",
            "component": "execution_queue",
            "ui_visible": True,

            "status": "failed",
            "action": "reconcile_running_execution",
            "reason": "execution_reconciliation_failed",

            "execution_id": execution_id,

            "resource_type": "execution",
            "resource_id": execution_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# FALHA NO WORKER PRINCIPAL
# ============================================================

def registrar_falha_worker_fila(
    *,
    error: Exception,
) -> None:
    """
    Registra falha técnica não tratada durante um ciclo
    do Worker da fila.

    O Worker continua executando após o intervalo configurado.
    """

    logger.exception(
        "Erro inesperado no Worker da fila",
        extra={
            "event": "execution.queue.worker.failed",
            "category": "SYSTEM",
            "component": "execution_queue",
            "ui_visible": True,

            "status": "failed",
            "action": "process_execution_queue_cycle",
            "reason": "execution_queue_worker_error",

            "resource_type": "execution_queue",

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


# ============================================================
# TIMEOUT AO FINALIZAR WORKER
# ============================================================

def registrar_timeout_parada_worker_fila() -> None:
    """
    Registra quando o Worker da fila não consegue finalizar
    dentro do prazo definido para shutdown.

    Não existe exceção neste cenário.
    """

    logger.warning(
        "Worker da fila não finalizou dentro do prazo",
        extra={
            "event": "execution.queue.worker.stop.timeout",
            "category": "SYSTEM",
            "component": "execution_queue",
            "ui_visible": True,

            "status": "failed",
            "action": "stop_execution_queue_worker",
            "reason": "execution_queue_stop_timeout",

            "resource_type": "execution_queue",
        },
    )


# ============================================================
# FALHA AO CRIAR EXECUTION QUEUED
# ============================================================

def registrar_falha_criacao_fila_execucao(
    *,
    robot_id: int | None,
    robot_name: str | None,
    robot_filename: str | None,
    robot_version: int | None,
    agent_id: str | None,
    agent_name: str | None,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica ao persistir uma nova Execution
    na fila.
    """

    logger.exception(
        "Falha ao criar execução na fila",
        extra={
            "event": "execution.queue.creation.failed",
            "category": "SYSTEM",
            "component": "execution_queue",
            "ui_visible": True,

            "status": "failed",
            "action": "create_queued_execution",
            "reason": "execution_queue_creation_failed",

            "robot_id": robot_id,
            "robot_name": robot_name,
            "robot_filename": robot_filename,
            "robot_version": robot_version,

            "agent_id": agent_id,
            "agent_name": agent_name,

            "user_id": user_id,

            "resource_type": "execution_queue",

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )

# ============================================================
# WORKER INICIADO
# ============================================================

def registrar_inicio_worker_fila() -> None:
    """
    Registra lifecycle interno do Worker da fila.

    O evento permanece no arquivo físico para diagnóstico,
    mas não aparece na interface de Logs do Sistema.
    """

    logger.info(
        "Worker da fila iniciado",
        extra={
            "event": "execution.queue.worker.started",
            "category": "SYSTEM",
            "component": "execution_queue",
            "ui_visible": False,
            "status": "running",
        },
    )


# ============================================================
# WORKER FINALIZADO
# ============================================================

def registrar_parada_worker_fila() -> None:
    """
    Registra encerramento normal do Worker da fila.

    O evento permanece oculto da interface por representar
    lifecycle técnico normal.
    """

    logger.info(
        "Worker da fila finalizado",
        extra={
            "event": "execution.queue.worker.stopped",
            "category": "SYSTEM",
            "component": "execution_queue",
            "ui_visible": False,
            "status": "stopped",
        },
    )