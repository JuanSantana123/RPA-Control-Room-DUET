# ============================================================
# AUTOMATION TEMPLATES - PUBLICATION OBSERVABILITY
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_falha_publicacao_template(
    *,
    template_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada durante a publicação de
    uma nova versão de Template.
    """

    logger.exception(
        "Falha ao publicar versão do Template",
        extra={
            "event": "template.publication.failed",
            "category": "SYSTEM",
            "component": "template_publication",
            "ui_visible": True,
            "status": "failed",
            "action": "publish_template_version",
            "reason": "unexpected_error",

            "actor_user_id": user_id,

            "resource_type": "automation_template",
            "resource_id": template_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )