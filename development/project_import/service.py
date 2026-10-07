# ============================================================
# DEVELOPMENT PROJECT IMPORT - SERVICE
# ============================================================
#
# Fluxo em duas etapas:
#
# 1. analyze
#    - recebe ZIP;
#    - valida segurança/integridade;
#    - lista arquivos .py;
#    - NÃO cria AutomationProject.
#
# 2. confirm
#    - exige EntryPoint informado pelo usuário;
#    - revalida o pacote;
#    - extrai para staging;
#    - cria AutomationProject + Workspace na mesma transação;
#    - NÃO cria Checkout automaticamente.
# ============================================================

from __future__ import annotations

import hashlib
import logging
import shutil
import time
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from development.entrypoint_service import (
    normalizar_entrypoint_path,
)
from development.project_import.archive_inventory import (
    listar_arquivos_python_zip,
    sugerir_entrypoint,
)
from development.project_import.session_store import (
    PENDING_IMPORTS_DIRECTORY,
    carregar_manifesto,
    gerar_import_token,
    limpar_sessoes_expiradas,
    remover_sessao,
)
from development.projects_service import (
    criar_projeto_service,
)
from packaging.project_packager import (
    WORKSPACE_REPOSITORY,
)
from schemas.development import (
    AutomationProjectCreate,
)
from schemas.development_project_import import (
    DevelopmentProjectImportConfirmRequest,
)
from security.artifacts import (
    ArtifactSecurityError,
    MAX_UPLOAD_SIZE,
    normalizar_membro_zip,
    validar_nome_zip,
    validar_zip,
)


logger = logging.getLogger("control_room")

UPLOAD_CHUNK_SIZE = 1024 * 1024


def _calcular_sha256(
    file_path: Path,
) -> str:
    """Calcula SHA-256 sem carregar o pacote inteiro na memória."""

    digest = hashlib.sha256()

    with file_path.open("rb") as stream:
        while True:
            chunk = stream.read(UPLOAD_CHUNK_SIZE)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


async def _salvar_upload_zip(
    file: UploadFile,
    destination: Path,
) -> None:
    """Persiste UploadFile com limite explícito de tamanho."""

    total = 0

    with destination.open("xb") as output:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_SIZE)

            if not chunk:
                break

            total += len(chunk)

            if total > MAX_UPLOAD_SIZE:
                raise ArtifactSecurityError(
                    "Pacote excede o tamanho máximo permitido."
                )

            output.write(chunk)


def _extrair_zip_seguro(
    zip_path: Path,
    destination: Path,
) -> None:
    """Extrai o ZIP já validado sem utilizar extractall()."""

    validar_zip(zip_path)

    destination.mkdir(
        parents=True,
        exist_ok=False,
    )

    destination_resolved = destination.resolve()

    with zipfile.ZipFile(zip_path, "r") as pacote:
        for info in pacote.infolist():
            logical_path = normalizar_membro_zip(
                info.filename
            )

            target = (
                destination
                / Path(*logical_path.parts)
            ).resolve()

            if (
                target != destination_resolved
                and destination_resolved not in target.parents
            ):
                raise ArtifactSecurityError(
                    "Pacote contém caminho fora da área de importação."
                )

            if info.is_dir():
                target.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                continue

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with (
                pacote.open(info, "r") as source,
                target.open("xb") as output,
            ):
                shutil.copyfileobj(
                    source,
                    output,
                    length=UPLOAD_CHUNK_SIZE,
                )


async def analisar_importacao_projeto_service(
    file: UploadFile,
    usuario,
) -> dict:
    """Analisa um ZIP e cria somente uma sessão temporária."""

    limpar_sessoes_expiradas()

    import_token = gerar_import_token()
    session_dir = (
        PENDING_IMPORTS_DIRECTORY
        / import_token
    )

    try:
        original_filename = validar_nome_zip(
            file.filename or ""
        )

        # A pasta é criada aqui; salvar_manifesto() receberá depois
        # uma pasta já existente, portanto persistimos o manifesto
        # manualmente após o pacote ter sido validado.
        session_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        package_path = session_dir / "package.zip"

        await _salvar_upload_zip(
            file,
            package_path,
        )

        validar_zip(package_path)

        python_files = listar_arquivos_python_zip(
            package_path
        )

        if not python_files:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Nenhum arquivo Python (.py) foi encontrado no pacote."
                ),
            )

        suggested_entrypoint = sugerir_entrypoint(
            python_files
        )

        manifest = {
            "import_token": import_token,
            "user_id": int(usuario.id),
            "created_at_epoch": time.time(),
            "original_filename": original_filename,
            "package_filename": "package.zip",
            "package_sha256": _calcular_sha256(package_path),
            "python_files": python_files,
            "suggested_entrypoint": suggested_entrypoint,
        }

        # Persistência atômica do manifesto dentro da pasta já criada.
        temp_manifest = session_dir / "manifest.json.tmp"
        final_manifest = session_dir / "manifest.json"

        import json

        temp_manifest.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temp_manifest.replace(final_manifest)

        return {
            "status": "success",
            "import_token": import_token,
            "filename": original_filename,
            "python_files": python_files,
            "suggested_entrypoint": suggested_entrypoint,
            "entrypoint_required": True,
        }

    except HTTPException:
        if session_dir.exists():
            shutil.rmtree(
                session_dir,
                ignore_errors=True,
            )
        raise

    except ArtifactSecurityError as error:
        if session_dir.exists():
            shutil.rmtree(
                session_dir,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        if session_dir.exists():
            shutil.rmtree(
                session_dir,
                ignore_errors=True,
            )

        logger.exception(
            "Falha ao analisar pacote de projeto",
            extra={
                "event": "development_project_import_analyze_failed",
                "user_id": getattr(usuario, "id", None),
                "error_type": type(error).__name__,
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Não foi possível analisar o pacote do projeto.",
        ) from error

    finally:
        try:
            await file.close()
        except Exception:
            # Fechamento do upload é cleanup best-effort e não deve
            # substituir o resultado principal da operação.
            pass


def confirmar_importacao_projeto_service(
    request: DevelopmentProjectImportConfirmRequest,
    db: Session,
    usuario,
) -> dict:
    """Confirma o EntryPoint e cria projeto/workspace de forma transacional."""

    try:
        session_dir, manifest = carregar_manifesto(
            request.import_token,
            user_id=usuario.id,
        )
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except TimeoutError as error:
        raise HTTPException(410, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(409, str(error)) from error

    package_path = session_dir / str(
        manifest.get("package_filename", "package.zip")
    )

    if not package_path.is_file():
        raise HTTPException(
            409,
            "O pacote temporário da importação não está mais disponível.",
        )

    if _calcular_sha256(package_path) != manifest.get("package_sha256"):
        raise HTTPException(
            409,
            "O pacote temporário foi alterado após a análise.",
        )

    try:
        normalized_entrypoint = normalizar_entrypoint_path(
            request.entrypoint_path
        )
    except ValueError as error:
        raise HTTPException(400, str(error)) from error

    python_files = list(
        manifest.get("python_files") or []
    )

    python_files_by_casefold = {
        path.casefold(): path
        for path in python_files
    }

    canonical_entrypoint = python_files_by_casefold.get(
        normalized_entrypoint.casefold()
    )

    if canonical_entrypoint is None:
        raise HTTPException(
            409,
            "O EntryPoint selecionado não existe mais no pacote analisado.",
        )
    try:
        validar_zip(package_path)
    except ArtifactSecurityError as error:
        raise HTTPException(400, str(error)) from error

    staging_path = (
        session_dir
        / f"staging_{uuid.uuid4().hex}"
    )

    try:
        _extrair_zip_seguro(
            package_path,
            staging_path,
        )

        entrypoint_file = (
            staging_path
            / Path(canonical_entrypoint)
        ).resolve()

        staging_resolved = staging_path.resolve()

        if (
            not entrypoint_file.is_file()
            or (
                entrypoint_file != staging_resolved
                and staging_resolved not in entrypoint_file.parents
            )
        ):
            raise HTTPException(
                409,
                "O EntryPoint selecionado não foi materializado corretamente.",
            )

        create_request = AutomationProjectCreate(
            name=request.name,
            description=request.description,
            folder_id=request.folder_id,
            base_robot_id=None,
        )

        def materializar_workspace_importado(projeto) -> Path:
            """Materializa o conteúdo antes do commit do projeto."""

            workspace_path = (
                WORKSPACE_REPOSITORY
                / str(projeto.id)
            )

            if workspace_path.exists():
                raise RuntimeError(
                    "O Workspace de destino já existe."
                )

            try:
                shutil.copytree(
                    staging_path,
                    workspace_path,
                )

                projeto.entrypoint_path = canonical_entrypoint

                return workspace_path

            except Exception:
                if workspace_path.exists():
                    shutil.rmtree(
                        workspace_path,
                        ignore_errors=True,
                    )
                raise

        result = criar_projeto_service(
            request=create_request,
            db=db,
            usuario=usuario,
            workspace_initializer=materializar_workspace_importado,
        )

        try:
            remover_sessao(
                request.import_token
            )
        except Exception:
            logger.warning(
                "Projeto importado, mas a sessão temporária não pôde ser removida",
                extra={
                    "event": "development_project_import_cleanup_failed",
                    "user_id": usuario.id,
                    "status": "warning",
                },
            )

        return result

    finally:
        # Em caso de sucesso remover_sessao() já elimina todo o diretório.
        # Em caso de erro mantemos package.zip + manifest para permitir
        # correção/retry, mas removemos o staging parcial.
        if staging_path.exists():
            shutil.rmtree(
                staging_path,
                ignore_errors=True,
            )
