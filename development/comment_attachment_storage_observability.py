# ============================================================
# DEVELOPMENT - COMMENT ATTACHMENT STORAGE OBSERVABILITY
# ============================================================
#
# Eventos técnicos relacionados à consistência física dos
# anexos de comentários de AutomationProjects.
#
# Este módulo NÃO:
#
# - acessa banco de dados;
# - remove arquivos;
# - executa regras de negócio;
# - manipula UploadFile.
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_falha_limpeza_anexo_pendente_expirado(
    *,
    project_id: int,
    attachment_id: int,
    storage_key: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha ao remover fisicamente um anexo pendente
    expirado depois que seu registro já foi removido do banco.
    """

    logger.exception(
        "Anexo pendente expirado removido do banco, mas arquivo físico permaneceu",
        extra={
            "event": "project.comment_attachment.expired_cleanup.failed",
            "category": "SYSTEM",
            "component": "development_comment_attachment_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "cleanup_expired_pending_comment_attachment",
            "reason": "post_commit_attachment_cleanup_failed",

            "actor_user_id": user_id,

            "resource_type": "project_comment_attachment",
            "resource_id": attachment_id,
            "resource_name": storage_key,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_falha_limpeza_anexo_pendente_excluido(
    *,
    project_id: int,
    attachment_id: int,
    storage_key: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha ao remover fisicamente um anexo pendente
    depois que sua exclusão já foi confirmada no banco.
    """

    logger.exception(
        "Anexo pendente removido do banco, mas arquivo físico permaneceu",
        extra={
            "event": "project.comment_attachment.cleanup.failed",
            "category": "SYSTEM",
            "component": "development_comment_attachment_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "cleanup_deleted_pending_comment_attachment",
            "reason": "post_commit_attachment_cleanup_failed",

            "actor_user_id": user_id,

            "resource_type": "project_comment_attachment",
            "resource_id": attachment_id,
            "resource_name": storage_key,

            "project_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )