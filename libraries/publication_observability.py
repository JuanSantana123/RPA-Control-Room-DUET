# ============================================================
# LIBRARIES - PUBLICATION OBSERVABILITY
# ============================================================
#
# Eventos técnicos relevantes relacionados à publicação de
# LibraryVersions.
#
# Este módulo NÃO contém regra de negócio nem persistência.
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_falha_publicacao_library(
    *,
    library_id: int,
    version: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha técnica inesperada durante a publicação de
    uma nova LibraryVersion em Produção.
    """

    logger.exception(
        "Falha ao publicar versão da biblioteca",
        extra={
            "event": "library.publication.failed",
            "category": "SYSTEM",
            "component": "library_publication",
            "ui_visible": True,
            "status": "failed",
            "action": "publish_library_version",
            "reason": "unexpected_error",

            "actor_user_id": user_id,

            "resource_type": "library",
            "resource_id": library_id,

            "library_version": version,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )