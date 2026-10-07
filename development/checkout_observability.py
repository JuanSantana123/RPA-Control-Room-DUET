# ============================================================
# DEVELOPMENT - CHECKOUT OBSERVABILITY
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_checkout_ocupado(
    *,
    project_id: int,
    actor_user_id: int,
    owner_user_id: int,
) -> None:
    """
    Registra tentativa explícita de Checkout quando outro
    usuário já possui a exclusividade do projeto.
    """

    logger.warning(
        "Checkout recusado porque o projeto já está reservado",
        extra={
            "event": "project.checkout.conflict",
            "category": "AUDIT",
            "component": "project_checkout",
            "ui_visible": True,
            "status": "conflict",
            "action": "checkout_project",
            "reason": "already_checked_out_by_other_user",

            "actor_user_id": actor_user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,
            "checkout_owner_user_id": owner_user_id,
        },
    )


def registrar_conflito_corrida_checkout(
    *,
    project_id: int,
    actor_user_id: int,
    owner_user_id: int | None,
) -> None:
    """
    Registra conflito de concorrência quando outra requisição
    adquire o Checkout entre a leitura inicial e o INSERT.
    """

    logger.warning(
        "Checkout perdido por concorrência",
        extra={
            "event": "project.checkout.conflict",
            "category": "AUDIT",
            "component": "project_checkout",
            "ui_visible": True,
            "status": "conflict",
            "action": "checkout_project",
            "reason": "checkout_race_lost",

            "actor_user_id": actor_user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,
            "checkout_owner_user_id": owner_user_id,
        },
    )

def registrar_falha_checkout_projeto(
    *,
    project_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada ao adquirir o Checkout
    exclusivo de um AutomationProject.
    """

    logger.exception(
        "Falha técnica ao realizar Checkout do projeto",
        extra={
            "event": "project.checkout.failed",
            "category": "SYSTEM",
            "component": "project_checkout",
            "ui_visible": True,
            "status": "failed",
            "action": "checkout_project",
            "reason": "unexpected_error",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_falha_checkin_projeto(
    *,
    project_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada ao liberar o Checkout
    através do Check-in normal.
    """

    logger.exception(
        "Falha técnica ao realizar Check-in do projeto",
        extra={
            "event": "project.checkin.failed",
            "category": "SYSTEM",
            "component": "project_checkout",
            "ui_visible": True,
            "status": "failed",
            "action": "checkin_project",
            "reason": "unexpected_error",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_falha_force_release_checkout(
    *,
    project_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada durante Force Release
    administrativo do Checkout.
    """

    logger.exception(
        "Falha técnica no Force Release do Checkout",
        extra={
            "event": "project.checkout.force_release.failed",
            "category": "SYSTEM",
            "component": "project_checkout",
            "ui_visible": True,
            "status": "failed",
            "action": "force_release_project_checkout",
            "reason": "unexpected_error",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )