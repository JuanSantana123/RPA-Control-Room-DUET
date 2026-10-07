# ============================================================
# DEVELOPMENT - LIBRARY IMPORT STORAGE
# ============================================================
#
# Responsável exclusivamente pela compensação física da
# Working Copy durante rollback de importação de Library.
#
# Este módulo NÃO:
#
# - executa rollback de banco;
# - importa ZIP;
# - cria Library ou Draft;
# - contém regras de publicação.
# ============================================================

import shutil

from pathlib import Path

from development.library_storage_observability import (
    registrar_falha_limpeza_working_copy_importacao,
)


def limpar_working_copy_importada_apos_rollback(
    *,
    target_materialized: bool,
    target: Path | None,
    project_id: int,
    library_id: int | None,
    import_name: str,
    user_id: int | None,
) -> None:
    """
    Remove a Working Copy que chegou a ser materializada antes
    de uma falha transacional na importação.

    A falha desta compensação não substitui o erro original.
    Ela é registrada separadamente como inconsistência entre
    banco e filesystem.
    """

    if (
        not target_materialized
        or target is None
    ):
        return

    if (
        not target.exists()
        and not target.is_symlink()
    ):
        return

    try:
        shutil.rmtree(
            target
        )

    except Exception as error:
        registrar_falha_limpeza_working_copy_importacao(
            project_id=project_id,
            library_id=library_id,
            import_name=import_name,
            user_id=user_id,
            workspace_path=str(target),
            error=error,
        )