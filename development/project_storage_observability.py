# ============================================================
# DEVELOPMENT - PROJECT STORAGE OBSERVABILITY
# ============================================================
#
# Eventos técnicos relacionados à consistência física dos
# Workspaces de AutomationProjects.
#
# Este módulo NÃO:
#
# - cria ou remove Workspaces;
# - executa rollback;
# - acessa banco de dados;
# - possui regras de negócio.
# ============================================================

import logging


logger = logging.getLogger("control_room")


def registrar_falha_limpeza_workspace_rollback_criacao(
    *,
    project_id: int,
    project_name: str,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha crítica ao remover o Workspace depois de
    rollback da criação de um AutomationProject.

    Nesse cenário, a criação foi revertida no banco, mas podem
    permanecer arquivos físicos órfãos no storage.
    """

    logger.exception(
        "Falha ao limpar Workspace após rollback da criação do projeto",
        extra={
            "event": "project.workspace.rollback_cleanup.failed",
            "category": "SYSTEM",
            "component": "development_project_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "cleanup_project_workspace_after_create_rollback",
            "reason": "rollback_workspace_cleanup_failed",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,
            "resource_name": project_name,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )

def registrar_falha_restauracao_workspace_exclusao_permanente(
    *,
    project_id: int,
    user_id: int | None,
    workspace_path: str,
    staged_workspace_path: str,
    error: Exception,
) -> None:
    """
    Registra falha ao restaurar o Workspace depois que a
    exclusão permanente falhou e o banco sofreu rollback.

    Nesse cenário, o registro continua existindo no banco,
    mas o Workspace pode permanecer no caminho temporário.
    """

    logger.exception(
        "Falha ao restaurar Workspace após rollback da exclusão permanente",
        extra={
            "event": "project.workspace.rollback_restore.failed",
            "category": "SYSTEM",
            "component": "development_project_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "restore_project_workspace_after_delete_rollback",
            "reason": "rollback_restore_failed",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,
            "resource_name": (
                f"{staged_workspace_path} -> {workspace_path}"
            ),

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_falha_limpeza_workspace_exclusao_permanente(
    *,
    project_id: int,
    user_id: int | None,
    staged_workspace_path: str,
    error: Exception,
) -> None:
    """
    Registra falha ao remover fisicamente o Workspace temporário
    depois que a exclusão permanente já foi confirmada no banco.
    """

    logger.exception(
        "Projeto removido do banco, mas Workspace físico não foi limpo",
        extra={
            "event": "project.workspace.cleanup.failed",
            "category": "SYSTEM",
            "component": "development_project_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "cleanup_deleted_project_workspace",
            "reason": "post_commit_workspace_cleanup_failed",

            "actor_user_id": user_id,

            "resource_type": "automation_project",
            "resource_id": project_id,
            "resource_name": staged_workspace_path,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def registrar_falha_limpeza_anexos_projeto_excluido(
    *,
    project_id: int,
    user_id: int | None,
    error: Exception,
) -> None:
    """
    Registra falha ao remover os anexos de comentários depois que
    o AutomationProject já foi excluído permanentemente do banco.
    """

    logger.exception(
        "Projeto removido, mas anexos de comentários não foram limpos",
        extra={
            "event": "project.comment_attachments.cleanup.failed",
            "category": "SYSTEM",
            "component": "development_project_storage",
            "ui_visible": True,
            "status": "failed",
            "action": "cleanup_deleted_project_comment_attachments",
            "reason": "post_commit_attachment_cleanup_failed",

            "actor_user_id": user_id,

            "resource_type": "project_comment_attachments",
            "resource_id": project_id,

            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )