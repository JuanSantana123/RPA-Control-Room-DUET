# ============================================================
# DUET CORE - ROBOTS - REGRAS DO PACOTE IMPORTADO
# ============================================================
#
# Responsabilidade:
# - interpretar o manifesto de origem;
# - listar arquivos Python;
# - validar/normalizar o EntryPoint;
# - decidir qual EntryPoint será usado na importação.
#
# Este módulo NÃO:
# - grava banco;
# - cria RobotVersion;
# - escreve ZIP;
# - conhece FastAPI router.
# ============================================================

from __future__ import annotations

import json

from pathlib import PurePosixPath

from fastapi import HTTPException

from releases.service import MANIFEST


# ============================================================
# MANIFESTO DE ORIGEM
# ============================================================

def read_import_source_manifest(
    contents: dict[str, bytes],
    *,
    consume: bool,
) -> dict | None:
    """
    Lê o duet-release.json existente no pacote.

    consume=True:
        remove o manifesto original do conteúdo para que o
        importador possa gerar o manifesto local posteriormente.

    consume=False:
        apenas consulta, sem alterar o conteúdo.
    """

    if MANIFEST not in contents:
        return None

    raw_manifest = (
        contents.pop(MANIFEST)
        if consume
        else contents[MANIFEST]
    )

    try:
        manifest = json.loads(
            raw_manifest
        )

    except Exception as error:
        raise HTTPException(
            status_code=409,
            detail="O duet-release.json do pacote é inválido.",
        ) from error

    if not isinstance(manifest, dict):
        raise HTTPException(
            status_code=409,
            detail="O duet-release.json do pacote é inválido.",
        )

    if manifest.get("schema_version") != 1:
        raise HTTPException(
            status_code=409,
            detail=(
                "A versão do manifesto do pacote "
                "não é suportada."
            ),
        )

    return manifest


# ============================================================
# NORMALIZAÇÃO DO ENTRYPOINT
# ============================================================

def normalize_import_entrypoint(
    value: object,
) -> str:
    """
    Normaliza e valida um caminho relativo de EntryPoint.

    Exemplos válidos:

        executar.py
        src/processar.py
        robo/src/main.py
    """

    raw = str(
        value or ""
    ).strip().replace(
        "\\",
        "/",
    )

    if not raw:
        raise HTTPException(
            status_code=400,
            detail=(
                "Selecione um arquivo Python como EntryPoint."
            ),
        )

    path = PurePosixPath(
        raw
    )

    if (
        path.is_absolute()
        or raw.startswith("/")
        or any(
            part in {
                "",
                ".",
                "..",
            }
            for part in path.parts
        )
        or (
            path.parts
            and ":" in path.parts[0]
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "O EntryPoint informado possui um caminho inválido."
            ),
        )

    if path.suffix.lower() != ".py":
        raise HTTPException(
            status_code=400,
            detail=(
                "O EntryPoint precisa apontar para um arquivo .py."
            ),
        )

    return path.as_posix()


# ============================================================
# ARQUIVOS PYTHON
# ============================================================

def list_import_python_files(
    contents: dict[str, bytes],
) -> list[str]:
    """
    Lista todos os arquivos .py presentes no pacote.
    """

    python_files = [
        path
        for path in contents.keys()
        if path.lower().endswith(".py")
    ]

    return sorted(
        python_files,
        key=str.casefold,
    )


# ============================================================
# SUGESTÃO VISUAL
# ============================================================

def suggest_import_entrypoint(
    python_files: list[str],
) -> str | None:
    """
    Apenas sugere um EntryPoint.

    A sugestão NÃO equivale à seleção automática.
    """

    if "main.py" in python_files:
        return "main.py"

    main_candidates = [
        path
        for path in python_files
        if PurePosixPath(path).name.casefold()
        == "main.py"
    ]

    if main_candidates:
        return main_candidates[0]

    return None


# ============================================================
# ENTRYPOINT CONFIGURADO NO PACOTE
# ============================================================

def get_manifest_entrypoint(
    source_manifest: dict | None,
) -> str | None:

    if not source_manifest:
        return None

    raw_entrypoint = (
        source_manifest.get(
            "entrypoint_path"
        )
    )

    if not raw_entrypoint:
        return None

    return normalize_import_entrypoint(
        raw_entrypoint
    )


# ============================================================
# RESOLVER ENTRYPOINT EFETIVO
# ============================================================

def resolve_import_entrypoint(
    *,
    contents: dict[str, bytes],
    source_manifest: dict | None,
    requested_entrypoint: str | None,
) -> str:
    """
    Define o EntryPoint que será gravado na nova RobotVersion.

    Pacote DUET moderno:
        preserva obrigatoriamente o EntryPoint original.

    ZIP Python comum / pacote legado:
        exige escolha explícita do usuário.
    """

    configured_entrypoint = (
        get_manifest_entrypoint(
            source_manifest
        )
    )

    # --------------------------------------------------------
    # PACOTE DUET COM ENTRYPOINT DEFINIDO
    # --------------------------------------------------------

    if configured_entrypoint:

        if configured_entrypoint not in contents:
            raise HTTPException(
                status_code=409,
                detail=(
                    "O pacote não contém o EntryPoint "
                    "registrado no duet-release.json: "
                    f"{configured_entrypoint}."
                ),
            )

        if requested_entrypoint:

            normalized_requested = (
                normalize_import_entrypoint(
                    requested_entrypoint
                )
            )

            if (
                normalized_requested
                != configured_entrypoint
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Este pacote DUET já possui um EntryPoint "
                        "imutável definido no Release: "
                        f"{configured_entrypoint}."
                    ),
                )

        return configured_entrypoint

    # --------------------------------------------------------
    # ZIP PYTHON COMUM / PACOTE LEGADO
    # --------------------------------------------------------

    entrypoint_path = (
        normalize_import_entrypoint(
            requested_entrypoint
        )
    )

    if entrypoint_path not in contents:
        raise HTTPException(
            status_code=409,
            detail=(
                "O EntryPoint selecionado não existe "
                "no pacote analisado: "
                f"{entrypoint_path}."
            ),
        )

    return entrypoint_path