# ============================================================
# DEVELOPMENT - COMMENT ATTACHMENT STORAGE
# ============================================================
#
# Responsável pela limpeza física pós-commit dos anexos
# de comentários.
#
# IMPORTANTE:
#
# Quando estas funções são chamadas, o banco já confirmou
# a remoção do registro. Portanto uma falha no filesystem:
#
# - não executa rollback falso;
# - não altera o resultado funcional da operação;
# - é registrada como inconsistência de storage.
# ============================================================

from pathlib import Path

from development.comment_attachment_storage_observability import (
    registrar_falha_limpeza_anexo_pendente_expirado,
    registrar_falha_limpeza_anexo_pendente_excluido,
)


def _remover_arquivo_pos_commit(
    *,
    path: Path,
    registrar_falha,
    project_id: int,
    attachment_id: int,
    storage_key: str,
    user_id: int | None,
) -> None:
    """
    Remove um arquivo cujo registro já foi confirmado como
    excluído no banco.

    A exceção física não deve substituir o resultado principal
    da operação transacional já concluída.
    """

    try:
        path.unlink(
            missing_ok=True
        )

    except Exception as error:
        registrar_falha(
            project_id=project_id,
            attachment_id=attachment_id,
            storage_key=storage_key,
            user_id=user_id,
            error=error,
        )


def limpar_anexo_pendente_expirado_pos_commit(
    *,
    path: Path,
    project_id: int,
    attachment_id: int,
    storage_key: str,
    user_id: int | None,
) -> None:
    """Remove fisicamente um anexo pendente expirado."""

    _remover_arquivo_pos_commit(
        path=path,
        registrar_falha=
            registrar_falha_limpeza_anexo_pendente_expirado,
        project_id=project_id,
        attachment_id=attachment_id,
        storage_key=storage_key,
        user_id=user_id,
    )


def limpar_anexo_pendente_excluido_pos_commit(
    *,
    path: Path,
    project_id: int,
    attachment_id: int,
    storage_key: str,
    user_id: int | None,
) -> None:
    """Remove fisicamente um anexo pendente excluído pelo usuário."""

    _remover_arquivo_pos_commit(
        path=path,
        registrar_falha=
            registrar_falha_limpeza_anexo_pendente_excluido,
        project_id=project_id,
        attachment_id=attachment_id,
        storage_key=storage_key,
        user_id=user_id,
    )