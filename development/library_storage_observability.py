# ============================================================
# DEVELOPMENT - LIBRARY STORAGE OBSERVABILITY
# ============================================================
#
# Eventos técnicos relacionados à consistência física das
# Working Copies de Libraries dentro de AutomationProjects.
#
# Este módulo NÃO:
#
# - altera arquivos;
# - executa rollback;
# - acessa banco de dados;
# - possui regras de negócio.
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_falha_restauracao_working_copy_library(
    *,
    project_id: int,
    library_id: int,
    import_name: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha crítica ao restaurar uma Working Copy após
    rollback da exclusão de uma Library.

    Nesse cenário, o banco já sofreu rollback, mas o filesystem
    pode não ter retornado ao estado anterior.
    """

    logger.exception(
        "Falha ao restaurar Working Copy de Library após rollback",
        extra={
            "event": "library.working_copy.restore.failed",
            "category": "SYSTEM",
            "component": "development_library_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "restore_library_working_copy",
            "reason": "rollback_restore_failed",

            "actor_user_id": user_id,

            "resource_type": "library_working_copy",
            "resource_id": library_id,

            # Mantém também o contexto do projeto sem criar
            # novos campos específicos no formatter global.
            "resource_name": (
                f"{import_name} @ project:{project_id}"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )

def registrar_falha_limpeza_working_copy_importacao(
    *,
    project_id: int,
    library_id: int | None,
    import_name: str,
    user_id: int | None,
    workspace_path: str,
    error: Exception,
) -> None:
    """
    Registra falha ao remover uma Working Copy materializada
    depois que a importação da Library sofreu rollback.

    Nesse cenário, o banco foi revertido, mas arquivos físicos
    da Library podem permanecer no Workspace.
    """

    logger.exception(
        "Falha ao limpar Working Copy após rollback da importação",
        extra={
            "event": "library.working_copy.rollback_cleanup.failed",
            "category": "SYSTEM",
            "component": "development_library_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "cleanup_imported_library_working_copy",
            "reason": "rollback_working_copy_cleanup_failed",

            "actor_user_id": user_id,

            "resource_type": "library_working_copy",
            "resource_id": library_id,
            "resource_name": (
                f"{import_name} @ project:{project_id}"
            ),

            "workspace_path": workspace_path,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )