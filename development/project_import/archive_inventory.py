# ============================================================
# DEVELOPMENT PROJECT IMPORT - ZIP INVENTORY
# ============================================================
#
# Responsável somente por validar e inspecionar o conteúdo de
# um ZIP. Não cria AutomationProject e não altera Workspaces.
# ============================================================

from __future__ import annotations

import zipfile
from pathlib import Path

from security.artifacts import (
    normalizar_membro_zip,
    validar_zip,
)


def listar_arquivos_python_zip(zip_path: Path) -> list[str]:
    """Retorna todos os arquivos .py válidos presentes no ZIP."""

    validar_zip(zip_path)

    arquivos: list[str] = []

    with zipfile.ZipFile(zip_path, "r") as pacote:
        for info in pacote.infolist():
            if info.is_dir():
                continue

            caminho = normalizar_membro_zip(
                info.filename
            )

            if caminho.suffix.lower() != ".py":
                continue

            arquivos.append(
                caminho.as_posix()
            )

    return sorted(
        arquivos,
        key=str.casefold,
    )


def sugerir_entrypoint(
    python_files: list[str],
) -> str | None:
    """Sugere main.py quando existir, sem selecionar automaticamente."""

    if "main.py" in python_files:
        return "main.py"

    candidatos = [
        path
        for path in python_files
        if path.casefold().endswith("/main.py")
    ]

    if not candidatos:
        return None

    return min(
        candidatos,
        key=lambda path: (
            path.count("/"),
            path.casefold(),
        ),
    )
