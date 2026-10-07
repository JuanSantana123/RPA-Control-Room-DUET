"""Persistência segura de imagens anexadas aos comentários de projetos."""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from development.repository import BASE_DIRECTORY
from development.comment_attachment_storage import (
    limpar_anexo_pendente_expirado_pos_commit,
    limpar_anexo_pendente_excluido_pos_commit,
)
from models import AutomationProject, ProjectCommentAttachment


logger = logging.getLogger("control_room.development.comment_attachments")

ATTACHMENT_REPOSITORY = BASE_DIRECTORY / "storage" / "project_comment_attachments"
ATTACHMENT_REPOSITORY.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_ATTACHMENTS_PER_COMMENT = 5
CHUNK_SIZE = 64 * 1024

IMAGE_SIGNATURES = {
    "image/png": ("png", lambda value: value.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/jpeg": ("jpg", lambda value: value.startswith(b"\xff\xd8\xff")),
    "image/gif": ("gif", lambda value: value.startswith((b"GIF87a", b"GIF89a"))),
    "image/webp": ("webp", lambda value: value.startswith(b"RIFF") and value[8:12] == b"WEBP"),
}


def serializar_anexo(anexo: ProjectCommentAttachment) -> dict:
    return {
        "id": anexo.id,
        "project_id": anexo.project_id,
        "comment_id": anexo.comment_id,
        "name": anexo.original_name,
        "media_type": anexo.media_type,
        "size_bytes": anexo.size_bytes,
        "created_at": anexo.created_at.isoformat() if anexo.created_at else None,
    }


def _limpar_pendentes_expirados(project_id: int, user_id: int, db: Session) -> None:
    cutoff = datetime.utcnow() - timedelta(hours=24)
    stale = (
        db.query(ProjectCommentAttachment)
        .filter(
            ProjectCommentAttachment.project_id == project_id,
            ProjectCommentAttachment.uploaded_by == user_id,
            ProjectCommentAttachment.comment_id.is_(None),
            ProjectCommentAttachment.created_at < cutoff,
        )
        .all()
    )
    if not stale:
        return

    cleanup_targets = [
        (
            attachment.id,
            attachment.storage_key,
            ATTACHMENT_REPOSITORY / attachment.storage_key,
        )
        for attachment in stale
    ]

    for attachment in stale:
        db.delete(
            attachment
        )

    db.commit()

    for (
        attachment_id,
        storage_key,
        path,
    ) in cleanup_targets:

        limpar_anexo_pendente_expirado_pos_commit(
            path=path,
            project_id=project_id,
            attachment_id=attachment_id,
            storage_key=storage_key,
            user_id=user_id,
        )


def _detectar_imagem(header: bytes) -> tuple[str, str] | None:
    for media_type, (extension, matcher) in IMAGE_SIGNATURES.items():
        if matcher(header):
            return media_type, extension
    return None


def _estrutura_imagem_valida(media_type: str, header: bytes, tail: bytes, size: int) -> bool:
    """Rejeita arquivos truncados ou disfarçados sem decodificar conteúdo."""

    if media_type == "image/png":
        return len(header) >= 24 and header[12:16] == b"IHDR" and tail.endswith(b"IEND\xaeB`\x82")
    if media_type == "image/jpeg":
        return size >= 4 and tail.endswith(b"\xff\xd9")
    if media_type == "image/gif":
        return size >= 14 and tail.endswith(b";")
    if media_type == "image/webp":
        declared_size = int.from_bytes(header[4:8], "little") + 8 if len(header) >= 12 else 0
        return len(header) >= 16 and header[12:16] in {b"VP8 ", b"VP8L", b"VP8X"} and declared_size == size
    return False


async def criar_anexo_comentario_service(
    project_id: int,
    file: UploadFile,
    db: Session,
    usuario,
) -> dict:
    projeto = (
        db.query(AutomationProject)
        .filter(AutomationProject.id == project_id, AutomationProject.is_active == 1)
        .first()
    )
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    _limpar_pendentes_expirados(project_id, usuario.id, db)

    declared_type = (file.content_type or "").lower()
    if declared_type not in IMAGE_SIGNATURES:
        raise HTTPException(
            status_code=415,
            detail="Formato não suportado. Envie uma imagem PNG, JPEG, GIF ou WebP.",
        )

    pending_count = (
        db.query(ProjectCommentAttachment)
        .filter(
            ProjectCommentAttachment.project_id == project_id,
            ProjectCommentAttachment.uploaded_by == usuario.id,
            ProjectCommentAttachment.comment_id.is_(None),
        )
        .count()
    )
    if pending_count >= MAX_ATTACHMENTS_PER_COMMENT:
        raise HTTPException(
            status_code=409,
            detail="Remova uma imagem pendente antes de anexar outra. O limite é de 5 imagens por comentário.",
        )

    first_chunk = await file.read(CHUNK_SIZE)
    detected = _detectar_imagem(first_chunk)
    if not detected or detected[0] != declared_type:
        raise HTTPException(
            status_code=415,
            detail="O conteúdo do arquivo não corresponde ao formato de imagem informado.",
        )

    media_type, extension = detected
    project_directory = ATTACHMENT_REPOSITORY / str(project_id)
    project_directory.mkdir(parents=True, exist_ok=True)
    storage_key = f"{project_id}/{uuid4().hex}.{extension}"
    destination = ATTACHMENT_REPOSITORY / storage_key
    size = 0
    tail = b""

    try:
        with destination.open("xb") as output:
            chunk = first_chunk
            while chunk:
                size += len(chunk)
                if size > MAX_IMAGE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="A imagem excede o limite de 5 MB.",
                    )
                output.write(chunk)
                tail = (tail + chunk)[-16:]
                chunk = await file.read(CHUNK_SIZE)

        if not _estrutura_imagem_valida(media_type, first_chunk, tail, size):
            raise HTTPException(
                status_code=415,
                detail="A imagem está corrompida, incompleta ou utiliza uma estrutura não reconhecida.",
            )

        original_name = Path(file.filename or f"imagem.{extension}").name[:255]
        anexo = ProjectCommentAttachment(
            project_id=project_id,
            uploaded_by=usuario.id,
            original_name=original_name,
            media_type=media_type,
            size_bytes=size,
            storage_key=storage_key,
        )
        db.add(anexo)
        db.commit()
        db.refresh(anexo)

        logger.info(
            "Imagem de comentário enviada",
            extra={
                "event": "development_comment_attachment_uploaded",
                "project_id": project_id,
                "attachment_id": anexo.id,
                "user_id": usuario.id,
                "size_bytes": size,
                "status": "success",
            },
        )
        return {"status": "success", "attachment": serializar_anexo(anexo)}
    except HTTPException:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        logger.exception(
            "Falha ao persistir imagem de comentário",
            extra={"event": "development_comment_attachment_failed", "project_id": project_id, "user_id": usuario.id},
        )
        raise HTTPException(status_code=500, detail="Não foi possível anexar a imagem.")
    finally:
        await file.close()


def excluir_anexo_pendente_service(
    project_id: int,
    attachment_id: int,
    db: Session,
    usuario,
) -> dict:
    anexo = (
        db.query(ProjectCommentAttachment)
        .filter(
            ProjectCommentAttachment.id == attachment_id,
            ProjectCommentAttachment.project_id == project_id,
            ProjectCommentAttachment.uploaded_by == usuario.id,
            ProjectCommentAttachment.comment_id.is_(None),
        )
        .first()
    )
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo pendente não encontrado.")

    storage_key = anexo.storage_key

    path = (
        ATTACHMENT_REPOSITORY /
        storage_key
    )

    db.delete(
        anexo
    )

    db.commit()

    limpar_anexo_pendente_excluido_pos_commit(
        path=path,
        project_id=project_id,
        attachment_id=attachment_id,
        storage_key=storage_key,
        user_id=usuario.id,
    )

    return {
        "status": "success",
        "message": "Imagem removida.",
    }


def obter_anexo_comentario_service(
    project_id: int,
    attachment_id: int,
    db: Session,
) -> tuple[Path, str, str]:
    anexo = (
        db.query(ProjectCommentAttachment)
        .filter(
            ProjectCommentAttachment.id == attachment_id,
            ProjectCommentAttachment.project_id == project_id,
            ProjectCommentAttachment.comment_id.is_not(None),
        )
        .first()
    )
    if not anexo:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    path = (ATTACHMENT_REPOSITORY / anexo.storage_key).resolve()
    root = ATTACHMENT_REPOSITORY.resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")
    return path, anexo.media_type, anexo.original_name


def remover_repositorio_anexos_projeto(project_id: int) -> None:
    """Remove anexos físicos depois da exclusão definitiva já confirmada."""

    project_directory = (ATTACHMENT_REPOSITORY / str(project_id)).resolve()
    root = ATTACHMENT_REPOSITORY.resolve()
    if project_directory.parent != root:
        raise RuntimeError("Diretório de anexos inválido.")
    if project_directory.exists():
        shutil.rmtree(project_directory)
