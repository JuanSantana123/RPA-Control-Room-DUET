# ============================================================
# DEVELOPMENT - RELEASE OBSERVABILITY
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_falha_publicacao_robot(
    *,
    project_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada na publicação do Release
    de um AutomationProject para o catálogo de Robots.
    """

    logger.exception(
        "Falha ao publicar Release do Robot",
        extra={
            "event": "robot.publication.failed",
            "category": "SYSTEM",
            "component": "robot_publication",
            "ui_visible": True,
            "status": "failed",
            "action": "publish_robot_release",
            "reason": "unexpected_error",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )

def registrar_falha_previa_release(
    *,
    project_id: int,
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada durante a montagem da
    prévia de Release de um AutomationProject.

    Erros funcionais já representados por HTTPException não
    passam por este evento.
    """

    logger.exception(
        "Falha técnica ao preparar prévia de Release",
        extra={
            "event": "release.preview.failed",
            "category": "SYSTEM",
            "component": "release_preview",
            "ui_visible": True,
            "status": "failed",
            "action": "prepare_release_preview",
            "reason": "unexpected_error",

            "resource_type": "automation_project",
            "resource_id": project_id,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )