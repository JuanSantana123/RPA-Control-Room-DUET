# ============================================================
# DEVELOPMENT - WORKSPACE ASSET SERVICE
# ============================================================
#
# Responsável por arquivos não textuais ou auxiliares dentro de
# Working Copies de Libraries no DUET Studio.
#
# Este módulo NÃO abre arquivos no editor e NÃO executa conteúdo.
# Ele apenas:
# - recebe upload binário de forma atômica;
# - permite download de arquivo;
# - empacota pasta/Library em ZIP para download.
#
# Escrita exige:
# - Checkout do AutomationProject;
# - Checkout da própria Library.
#
# Leitura/download permanece disponível em modo somente leitura.
# ============================================================

import logging
import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from models import AutomationProject

from development.checkout_service import (
    exigir_checkout_workspace,
)
from development.repository import (
    garantir_workspace,
    resolver_caminho_workspace,
    validar_nome_item_workspace,
)
from development.workspace_core import (
    ensure_drafts,
)
from libraries.checkout_service import (
    exigir_checkout_biblioteca_para_caminho,
)


logger = logging.getLogger(
    "control_room"
)


UPLOAD_CHUNK_SIZE = 1024 * 1024

DEFAULT_MAX_UPLOAD_BYTES = (
    250 * 1024 * 1024
)


def _max_upload_bytes() -> int:
    raw = os.getenv(
        "DUET_WORKSPACE_ASSET_MAX_BYTES",
        str(DEFAULT_MAX_UPLOAD_BYTES),
    )

    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_UPLOAD_BYTES

    return max(
        UPLOAD_CHUNK_SIZE,
        value,
    )


@dataclass(frozen=True)
class WorkspaceAssetDownload:
    path: Path
    filename: str
    media_type: str
    temporary: bool = False

    def cleanup(self) -> None:
        if (
            self.temporary
            and self.path.exists()
        ):
            try:
                self.path.unlink()
            except OSError:
                logger.exception(
                    "Falha ao limpar ZIP temporário de download",
                    extra={
                        "event":
                            "workspace_asset_download_cleanup_failed",
                        "path":
                            str(self.path),
                    },
                )


def _obter_projeto_ativo(
    project_id: int,
    db: Session,
) -> AutomationProject:
    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id == project_id,
            AutomationProject.is_active == 1,
        )
        .first()
    )

    if not projeto:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    return projeto


def _normalizar_caminho_library(
    path: str,
) -> str:
    normalizado = (
        (path or "")
        .strip()
        .replace("\\", "/")
    )

    partes = [
        parte
        for parte in normalizado.split("/")
        if parte
    ]

    if (
        len(partes) < 2
        or partes[0] != "_libraries"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Upload e download de assets são permitidos "
                "somente dentro de uma Library do projeto."
            ),
        )

    return "/".join(partes)


async def enviar_asset_workspace_service(
    project_id: int,
    target_path: str,
    file: UploadFile,
    db: Session,
    usuario,
) -> dict:
    """Envia um arquivo para uma pasta já existente de Library."""

    _obter_projeto_ativo(
        project_id,
        db,
    )

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    # Garante que Working Copies publicadas estejam materializadas
    # antes de resolver a pasta de destino.
    ensure_drafts(
        db,
        project_id,
    )

    target_relativo = (
        _normalizar_caminho_library(
            target_path
        )
    )

    workspace_path = (
        garantir_workspace(
            project_id
        )
    )

    target_folder = (
        resolver_caminho_workspace(
            workspace_path,
            target_relativo,
        )
    )

    if (
        not target_folder.exists()
        or not target_folder.is_dir()
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "A pasta de destino da Library não existe."
            ),
        )

    filename = (
        validar_nome_item_workspace(
            file.filename or ""
        )
    )

    destination_relativo = (
        f"{target_relativo}/{filename}"
    )

    exigir_checkout_biblioteca_para_caminho(
        db=db,
        project_id=project_id,
        user_id=usuario.id,
        path=destination_relativo,
    )

    destination = (
        resolver_caminho_workspace(
            workspace_path,
            destination_relativo,
        )
    )

    if destination.exists():
        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um arquivo com este nome nesta pasta. "
                "Renomeie ou exclua o arquivo existente antes do upload."
            ),
        )

    temporary = (
        target_folder
        / f".{filename}.{uuid4().hex}.duet_upload"
    )

    total = 0
    max_bytes = (
        _max_upload_bytes()
    )

    try:
        with temporary.open("wb") as output:
            while True:
                chunk = await file.read(
                    UPLOAD_CHUNK_SIZE
                )

                if not chunk:
                    break

                total += len(chunk)

                if total > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "O arquivo excede o limite configurado para "
                            "upload de assets no Workspace."
                        ),
                    )

                output.write(chunk)

            output.flush()
            os.fsync(
                output.fileno()
            )

        os.replace(
            temporary,
            destination,
        )

        logger.info(
            "Asset enviado para Library",
            extra={
                "event":
                    "workspace_asset_uploaded",
                "user_id":
                    usuario.id,
                "project_id":
                    project_id,
                "workspace_path":
                    destination_relativo,
                "size":
                    total,
                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "project_id": project_id,
            "path": destination_relativo,
            "filename": filename,
            "size": total,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Falha no upload de asset da Library",
            extra={
                "event":
                    "workspace_asset_upload_failed",
                "user_id":
                    usuario.id,
                "project_id":
                    project_id,
                "workspace_path":
                    destination_relativo,
                "error_type":
                    type(error).__name__,
                "error_message":
                    str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível enviar o arquivo para a Library."
            ),
        ) from error

    finally:
        await file.close()

        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                logger.exception(
                    "Falha ao limpar upload temporário",
                    extra={
                        "event":
                            "workspace_asset_upload_cleanup_failed",
                        "path":
                            str(temporary),
                    },
                )


def _criar_zip_pasta(
    source: Path,
) -> Path:
    temp = tempfile.NamedTemporaryFile(
        prefix="duet_asset_",
        suffix=".zip",
        delete=False,
    )

    temp_path = Path(
        temp.name
    )
    temp.close()

    try:
        with zipfile.ZipFile(
            temp_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            items = sorted(
                source.rglob("*"),
                key=lambda item:
                    item.as_posix().lower(),
            )

            if not items:
                archive.writestr(
                    f"{source.name}/",
                    "",
                )

            for item in items:
                if item.is_symlink():
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Links simbólicos não podem ser baixados "
                            "como parte de uma Library."
                        ),
                    )

                relative = (
                    item.relative_to(
                        source
                    )
                )

                archive_name = (
                    (
                        Path(source.name)
                        / relative
                    ).as_posix()
                )

                if item.is_dir():
                    archive.writestr(
                        f"{archive_name}/",
                        "",
                    )
                elif item.is_file():
                    archive.write(
                        item,
                        archive_name,
                    )

        return temp_path

    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def preparar_download_asset_workspace_service(
    project_id: int,
    path: str,
    db: Session,
) -> WorkspaceAssetDownload:
    """Prepara download de arquivo ou pasta de uma Library."""

    _obter_projeto_ativo(
        project_id,
        db,
    )

    relative = (
        _normalizar_caminho_library(
            path
        )
    )

    workspace_path = (
        garantir_workspace(
            project_id
        )
    )

    ensure_drafts(
        db,
        project_id,
    )

    item = (
        resolver_caminho_workspace(
            workspace_path,
            relative,
        )
    )

    if not item.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Arquivo ou pasta da Library não encontrado."
            ),
        )

    if item.is_symlink():
        raise HTTPException(
            status_code=400,
            detail=(
                "Links simbólicos não podem ser baixados pelo Studio."
            ),
        )

    if item.is_file():
        return WorkspaceAssetDownload(
            path=item,
            filename=item.name,
            media_type="application/octet-stream",
            temporary=False,
        )

    if item.is_dir():
        zip_path = (
            _criar_zip_pasta(
                item
            )
        )

        return WorkspaceAssetDownload(
            path=zip_path,
            filename=f"{item.name}.zip",
            media_type="application/zip",
            temporary=True,
        )

    raise HTTPException(
        status_code=400,
        detail=(
            "Tipo de item não suportado para download."
        ),
    )
