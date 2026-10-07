# ============================================================
# DEVELOPMENT PROJECT IMPORT - SESSION STORE
# ============================================================
#
# Mantém temporariamente o pacote analisado entre:
#
#     POST /projects/import/analyze
#     POST /projects/import/confirm
#
# A sessão é vinculada ao usuário que enviou o pacote.
# ============================================================

from __future__ import annotations

import json
import secrets
import shutil
import time
from pathlib import Path

from packaging.project_packager import BASE_DIRECTORY


IMPORT_SESSION_TTL_SECONDS = 60 * 60

PENDING_IMPORTS_DIRECTORY = (
    BASE_DIRECTORY
    / "storage"
    / "development_project_imports"
    / "pending"
)

PENDING_IMPORTS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


def gerar_import_token() -> str:
    """Gera token opaco para uma importação ainda não confirmada."""

    return secrets.token_hex(24)


def obter_diretorio_sessao(
    import_token: str,
) -> Path:
    """Resolve o diretório físico de uma sessão sem aceitar caminhos."""

    token = str(import_token or "").strip().lower()

    if (
        len(token) != 48
        or any(ch not in "0123456789abcdef" for ch in token)
    ):
        raise ValueError("Token de importação inválido.")

    return PENDING_IMPORTS_DIRECTORY / token


def carregar_manifesto(
    import_token: str,
    *,
    user_id: int,
) -> tuple[Path, dict]:
    """Carrega e valida ownership e expiração da sessão."""

    session_dir = obter_diretorio_sessao(
        import_token
    )

    manifest_path = session_dir / "manifest.json"

    if not manifest_path.is_file():
        raise FileNotFoundError(
            "A importação pendente não foi encontrada."
        )

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "O estado temporário da importação está inválido."
        ) from error

    if int(manifest.get("user_id", -1)) != int(user_id):
        raise PermissionError(
            "A importação pertence a outro usuário."
        )

    created_at = float(
        manifest.get("created_at_epoch", 0)
    )

    if time.time() - created_at > IMPORT_SESSION_TTL_SECONDS:
        remover_sessao(
            import_token
        )

        raise TimeoutError(
            "A análise do pacote expirou. Envie o arquivo novamente."
        )

    return session_dir, manifest


def remover_sessao(
    import_token: str,
) -> None:
    """Remove uma sessão temporária inteira."""

    session_dir = obter_diretorio_sessao(
        import_token
    )

    if session_dir.exists():
        shutil.rmtree(session_dir)


def limpar_sessoes_expiradas() -> None:
    """Limpa sessões antigas de forma best-effort."""

    agora = time.time()

    for session_dir in PENDING_IMPORTS_DIRECTORY.iterdir():
        if not session_dir.is_dir():
            continue

        manifest_path = session_dir / "manifest.json"

        try:
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )

            created_at = float(
                manifest.get("created_at_epoch", 0)
            )

            if agora - created_at > IMPORT_SESSION_TTL_SECONDS:
                shutil.rmtree(session_dir)

        except Exception:
            # Sessão corrompida/órfã não deve impedir uma nova análise.
            # A limpeza periódica definitiva poderá ser externalizada
            # futuramente sem alterar o contrato do importador.
            continue
