# ============================================================
# AUTOMATION TEMPLATES - SERVICE
# ============================================================
#
# Responsável pelas regras de negócio e armazenamento físico
# dos Templates de automação do DUET CORE.
#
# Conceito desta primeira versão:
#
# - um Template possui identidade estável;
# - cada upload gera uma versão IMUTÁVEL;
# - a nova versão publicada passa a ser a versão atual;
# - novos projetos usam, por padrão, a versão atual;
# - projetos já criados NÃO são alterados quando o Template evolui;
# - não existem placeholders nesta etapa.
#
# Estrutura física:
#
# storage/
# └── templates/
#     └── {template_id}/
#         └── {version}/
#             └── template.zip
#
# O ZIP armazenado é o snapshot imutável daquela versão.
# ============================================================

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import stat
import tempfile
import zipfile

from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    AutomationTemplate,
    AutomationTemplateVersion,
)

from automation_templates.template_library_dependencies import (
    copiar_dependencias_template_version,
    registrar_composicao_template_version,
    resolver_selecoes_template_libraries,
)

from development.repository import (
    validar_workspace_fisico,
)

from automation_templates.publication_observability import (
    registrar_falha_publicacao_template,
)

# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# REPOSITÓRIO FÍSICO
# ============================================================

BASE_DIRECTORY = Path(
    os.path.abspath(__file__)
).parent.parent

TEMPLATES_REPOSITORY = (
    BASE_DIRECTORY /
    "storage" /
    "templates"
)

TEMPLATES_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True,
)

TEMP_REPOSITORY = (
    TEMPLATES_REPOSITORY /
    ".tmp"
)

TEMP_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LIMITES
# ============================================================

# Limite do ZIP recebido pelo Control Room.
MAX_TEMPLATE_ZIP_SIZE = (
    100 *
    1024 *
    1024
)

# Limite da soma dos arquivos descompactados.
#
# Evita que um ZIP pequeno expanda para um volume excessivo.
MAX_TEMPLATE_UNCOMPRESSED_SIZE = (
    500 *
    1024 *
    1024
)

# Quantidade máxima inicial de entradas no ZIP.
MAX_TEMPLATE_MEMBERS = 5000

UPLOAD_CHUNK_SIZE = (
    1024 *
    1024
)


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def serializar_template_version(
    version: AutomationTemplateVersion,
    *,
    current_version_id: int | None = None,
) -> dict:
    """
    Serializa uma versão publicada do Template.

    artifact_path não é enviado ao frontend porque representa
    um caminho interno do servidor.
    """

    return {
        "id":
            version.id,

        "template_id":
            version.template_id,

        "version":
            version.version,

        "filename":
            version.filename,

        "file_hash":
            version.file_hash,

        "published_by":
            version.published_by,

        "published_at": (
            version.published_at.isoformat()
            if version.published_at
            else None
        ),

        "is_current":
            version.id == current_version_id,
    }


def serializar_template(
    template: AutomationTemplate,
    *,
    versions: list[AutomationTemplateVersion] | None = None,
) -> dict:
    """
    Serializa os metadados públicos de um Template.
    """

    version_map = {
        version.id: version
        for version in (versions or [])
    }

    current_version = (
        version_map.get(
            template.current_version_id
        )
        if template.current_version_id
        else None
    )

    return {
        "id":
            template.id,

        "name":
            template.name,

        "description":
            template.description,

        "current_version_id":
            template.current_version_id,

        "current_version": (
            current_version.version
            if current_version
            else None
        ),

        "created_by":
            template.created_by,

        "created_at": (
            template.created_at.isoformat()
            if template.created_at
            else None
        ),

        "updated_at": (
            template.updated_at.isoformat()
            if template.updated_at
            else None
        ),

        "is_active":
            bool(
                template.is_active
            ),

        "versions": [
            serializar_template_version(
                version,
                current_version_id=
                    template.current_version_id,
            )
            for version in (
                versions or []
            )
        ],
    }


# ============================================================
# CONSULTAS AUXILIARES
# ============================================================

def obter_template_or_404(
    db: Session,
    template_id: int,
    *,
    somente_ativo: bool = False,
    lock: bool = False,
) -> AutomationTemplate:
    """
    Localiza um Template pelo ID.
    """

    query = (
        db.query(
            AutomationTemplate
        )
        .filter(
            AutomationTemplate.id ==
                template_id
        )
    )

    if somente_ativo:
        query = query.filter(
            AutomationTemplate.is_active == 1
        )

    if lock:
        query = query.with_for_update()

    template = query.first()

    if not template:
        raise HTTPException(
            status_code=404,
            detail="Template não encontrado.",
        )

    return template


def obter_template_version_or_404(
    db: Session,
    version_id: int,
    *,
    somente_template_ativo: bool = False,
) -> tuple[
    AutomationTemplate,
    AutomationTemplateVersion,
]:
    """
    Localiza uma versão e seu Template proprietário.
    """

    version = (
        db.query(
            AutomationTemplateVersion
        )
        .filter(
            AutomationTemplateVersion.id ==
                version_id
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail=(
                "Versão do Template não encontrada."
            ),
        )

    template = obter_template_or_404(
        db,
        version.template_id,
        somente_ativo=
            somente_template_ativo,
    )

    return (
        template,
        version,
    )


# ============================================================
# VALIDAÇÃO DO ZIP
# ============================================================

def _normalizar_nome_membro_zip(
    filename: str,
) -> PurePosixPath:
    """
    Normaliza o caminho interno do ZIP para validação.
    """

    return PurePosixPath(
        filename.replace(
            "\\",
            "/",
        )
    )


def validar_zip_template(
    zip_path: Path,
) -> None:
    """
    Valida segurança e estrutura mínima do Template.

    Aceita duas formas:

    1. Arquivos diretamente na raiz:
           main.py
           requirements.txt
           src/...

    2. Uma única pasta externa:
           MeuTemplate/
               main.py
               requirements.txt
               src/...

       Essa pasta externa será removida na instanciação para
       que o Workspace receba diretamente o conteúdo do projeto.

    Requisito mínimo:
        main.py precisa existir na raiz lógica do Template.
    """

    try:
        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as archive:

            members = archive.infolist()

            if not members:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O ZIP do Template está vazio."
                    ),
                )

            if (
                len(members) >
                MAX_TEMPLATE_MEMBERS
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O ZIP possui itens demais para "
                        "ser utilizado como Template."
                    ),
                )

            total_uncompressed = 0
            file_paths: list[
                PurePosixPath
            ] = []

            for member in members:

                path = (
                    _normalizar_nome_membro_zip(
                        member.filename
                    )
                )

                if not path.parts:
                    continue

                # --------------------------------------------
                # ZIP SLIP / CAMINHOS ABSOLUTOS
                # --------------------------------------------

                if path.is_absolute():
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "O ZIP contém caminho absoluto "
                            "não permitido."
                        ),
                    )

                if ".." in path.parts:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "O ZIP contém caminho relativo "
                            "inseguro."
                        ),
                    )

                if ":" in path.parts[0]:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "O ZIP contém caminho inválido."
                        ),
                    )

                # --------------------------------------------
                # SYMLINK
                # --------------------------------------------

                unix_mode = (
                    member.external_attr >>
                    16
                )

                if stat.S_ISLNK(
                    unix_mode
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Links simbólicos não são "
                            "permitidos em Templates."
                        ),
                    )

                # --------------------------------------------
                # ZIP BOMB BÁSICO
                # --------------------------------------------

                if not member.is_dir():
                    total_uncompressed += (
                        member.file_size
                    )

                    if (
                        total_uncompressed >
                        MAX_TEMPLATE_UNCOMPRESSED_SIZE
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "O conteúdo descompactado do "
                                "Template excede o limite "
                                "permitido."
                            ),
                        )

                    file_paths.append(
                        path
                    )

            if not file_paths:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O ZIP do Template não possui arquivos."
                    ),
                )

            # --------------------------------------------
            # IDENTIFICA RAIZ LÓGICA
            # --------------------------------------------

            has_root_main = any(
                path ==
                    PurePosixPath(
                        "main.py"
                    )
                for path in file_paths
            )

            if has_root_main:
                return

            top_level_names = {
                path.parts[0]
                for path in file_paths
                if path.parts
            }

            # Quando existe exatamente uma pasta externa,
            # aceitamos main.py dentro dela e removemos essa
            # pasta durante a criação do projeto.
            if len(
                top_level_names
            ) == 1:

                wrapper = next(
                    iter(
                        top_level_names
                    )
                )

                wrapped_main = (
                    PurePosixPath(
                        wrapper
                    ) /
                    "main.py"
                )

                if any(
                    path ==
                        wrapped_main
                    for path in file_paths
                ):
                    return

            raise HTTPException(
                status_code=400,
                detail=(
                    "O Template precisa possuir main.py "
                    "na raiz do projeto."
                ),
            )

    except HTTPException:
        raise

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail=(
                "O arquivo enviado não é um ZIP válido."
            ),
        )


# ============================================================
# HASH / CAMINHOS
# ============================================================

def calcular_sha256(
    file_path: Path,
) -> str:
    """
    Calcula SHA-256 do ZIP completo.
    """

    digest = hashlib.sha256()

    with file_path.open(
        "rb",
    ) as file_handle:

        while True:

            chunk = file_handle.read(
                UPLOAD_CHUNK_SIZE
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def montar_artifact_path_relativo(
    template_id: int,
    version: int,
) -> Path:
    """
    Monta o caminho relativo persistido no banco.
    """

    return (
        Path("storage") /
        "templates" /
        str(template_id) /
        str(version) /
        "template.zip"
    )


def resolver_artifact_path(
    artifact_path: str,
) -> Path:
    """
    Resolve o artefato salvo garantindo que continue dentro da
    raiz física de Templates do Control Room.
    """

    raw_path = Path(
        artifact_path
    )

    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    else:
        resolved = (
            BASE_DIRECTORY /
            raw_path
        ).resolve()

    repository_root = (
        TEMPLATES_REPOSITORY.resolve()
    )

    try:
        resolved.relative_to(
            repository_root
        )
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail=(
                "O artefato do Template possui "
                "caminho interno inválido."
            ),
        )

    return resolved


# ============================================================
# UPLOAD
# ============================================================

async def salvar_upload_temporario(
    upload: UploadFile,
) -> Path:
    """
    Persiste o UploadFile temporariamente para validação.

    O arquivo temporário é sempre removido pelo chamador.
    """

    filename = (
        upload.filename or ""
    ).strip()

    if not filename.lower().endswith(
        ".zip"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "O Template deve ser enviado em "
                "um arquivo .zip."
            ),
        )

    temporary_path = (
        TEMP_REPOSITORY /
        (
            f"{uuid4().hex}"
            ".zip"
        )
    )

    total_size = 0

    try:
        with temporary_path.open(
            "wb",
        ) as destination:

            while True:

                chunk = await upload.read(
                    UPLOAD_CHUNK_SIZE
                )

                if not chunk:
                    break

                total_size += len(
                    chunk
                )

                if (
                    total_size >
                    MAX_TEMPLATE_ZIP_SIZE
                ):
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "O ZIP do Template excede "
                            "o limite de 100 MiB."
                        ),
                    )

                destination.write(
                    chunk
                )

        validar_zip_template(
            temporary_path
        )

        return temporary_path

    except Exception:

        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass

        raise


# ============================================================
# LISTAGEM
# ============================================================

def listar_templates_service(
    db: Session,
    *,
    include_inactive: bool = False,
) -> dict:
    """
    Lista Templates e suas versões.
    """

    query = (
        db.query(
            AutomationTemplate
        )
    )

    if not include_inactive:
        query = query.filter(
            AutomationTemplate.is_active == 1
        )

    templates = (
        query
        .order_by(
            AutomationTemplate.name.asc(),
            AutomationTemplate.id.asc(),
        )
        .all()
    )

    template_ids = [
        template.id
        for template in templates
    ]

    versions_by_template: dict[
        int,
        list[AutomationTemplateVersion],
    ] = {
        template_id: []
        for template_id in template_ids
    }

    if template_ids:

        versions = (
            db.query(
                AutomationTemplateVersion
            )
            .filter(
                AutomationTemplateVersion.template_id.in_(
                    template_ids
                )
            )
            .order_by(
                AutomationTemplateVersion.template_id.asc(),
                AutomationTemplateVersion.version.desc(),
            )
            .all()
        )

        for version in versions:
            versions_by_template[
                version.template_id
            ].append(
                version
            )

    return {
        "status":
            "success",

        "templates": [
            serializar_template(
                template,
                versions=
                    versions_by_template.get(
                        template.id,
                        [],
                    ),
            )
            for template in templates
        ],
    }


def listar_templates_disponiveis_service(
    db: Session,
) -> dict:
    """
    Retorna somente Templates utilizáveis na criação de projetos.

    Um Template sem versão atual não é disponibilizado.
    """

    result = listar_templates_service(
        db,
        include_inactive=False,
    )

    result["templates"] = [
        template
        for template in result["templates"]
        if (
            template.get(
                "current_version_id"
            )
            is not None
        )
    ]

    return result


# ============================================================
# CRIAÇÃO DO TEMPLATE
# ============================================================

async def criar_template_service(
    *,
    name: str,
    description: str | None,
    file: UploadFile,
    libraries: list[dict] | None = None,
    db: Session,
    usuario,
) -> dict:
    """
    Cria um Template e publica automaticamente sua versão 1.
    """

    normalized_name = (
        name or ""
    ).strip()

    normalized_description = (
        description.strip()
        if description and description.strip()
        else None
    )

    if not normalized_name:
        raise HTTPException(
            status_code=400,
            detail=(
                "O nome do Template não pode "
                "ficar vazio."
            ),
        )

    duplicate = (
        db.query(
            AutomationTemplate
        )
        .filter(
            func.lower(
                AutomationTemplate.name
            ) ==
            normalized_name.lower()
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um Template com esse nome."
            ),
        )

    temporary_path = (
        await salvar_upload_temporario(
            file
        )
    )

    template_directory = None

    try:

        # --------------------------------------------------------
        # COMPOSIÇÃO INICIAL DE LIBRARIES
        # --------------------------------------------------------
        #
        # Na criação do Template, ausência do campo e [] possuem o
        # mesmo significado: a v1 nasce sem Libraries.
        #
        # Quando houver seleção, validamos todas as LibraryVersions
        # antes de persistir o snapshot da versão.
        # --------------------------------------------------------

        resolved_libraries = (
            resolver_selecoes_template_libraries(
                db,
                libraries or [],
            )
        )

        template = AutomationTemplate(
            name=normalized_name,
            description=
                normalized_description,
            current_version_id=None,
            created_by=
                usuario.id,
            is_active=1,
        )

        db.add(
            template
        )

        # Precisamos do ID antes de definir a pasta física.
        db.flush()

        version_number = 1

        artifact_relative = (
            montar_artifact_path_relativo(
                template.id,
                version_number,
            )
        )

        artifact_absolute = (
            BASE_DIRECTORY /
            artifact_relative
        ).resolve()

        template_directory = (
            artifact_absolute.parent.parent
        )

        artifact_absolute.parent.mkdir(
            parents=True,
            exist_ok=False,
        )

        shutil.copy2(
            temporary_path,
            artifact_absolute,
        )

        version = AutomationTemplateVersion(
            template_id=
                template.id,
            version=
                version_number,
            filename=(
                file.filename or
                "template.zip"
            ),
            artifact_path=
                str(
                    artifact_relative
                ),
            file_hash=
                calcular_sha256(
                    artifact_absolute
                ),
            published_by=
                usuario.id,
        )

        db.add(
            version
        )

        db.flush()

        # --------------------------------------------------------
        # SNAPSHOT ATÔMICO DAS LIBRARIES DA v1
        # --------------------------------------------------------
        #
        # As dependências são gravadas antes do mesmo commit que
        # confirma Template + TemplateVersion. Assim não existe uma
        # v1 parcialmente criada sem a composição solicitada.
        # --------------------------------------------------------

        registrar_composicao_template_version(
            db=db,
            template_version_id=
                version.id,
            resolved_libraries=
                resolved_libraries,
            created_by=
                usuario.id,
        )

        template.current_version_id = (
            version.id
        )

        db.commit()

        db.refresh(
            template
        )

        db.refresh(
            version
        )

        logger.info(
            "Template de automação criado",
            extra={
                "event":
                    "automation_template_created",
                "template_id":
                    template.id,
                "template_version":
                    version.version,
                "user_id":
                    usuario.id,
                "status":
                    "success",
            },
        )

        return {
            "status":
                "success",

            "message":
                "Template criado com sucesso.",

            "template":
                serializar_template(
                    template,
                    versions=[
                        version
                    ],
                ),
        }

    except HTTPException:

        db.rollback()

        if template_directory:
            shutil.rmtree(
                template_directory,
                ignore_errors=True,
            )

        raise

    except IntegrityError as error:

        db.rollback()

        if template_directory:
            shutil.rmtree(
                template_directory,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível criar o Template "
                "porque os dados já existem."
            ),
        ) from error

    except Exception as error:

        db.rollback()

        if template_directory:
            shutil.rmtree(
                template_directory,
                ignore_errors=True,
            )

        logger.exception(
            "Falha ao criar Template",
            extra={
                "event":
                    "automation_template_create_failed",
                "user_id":
                    getattr(
                        usuario,
                        "id",
                        None,
                    ),
                "status":
                    "error",
                "error_type":
                    type(error).__name__,
                "error_message":
                    str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível criar o Template."
            ),
        ) from error

    finally:

        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass


# ============================================================
# NOVA VERSÃO
# ============================================================

async def publicar_nova_versao_template_service(
    *,
    template_id: int,
    file: UploadFile,
    libraries: list[dict] | None = None,
    db: Session,
    usuario,
) -> dict:
    """
    Publica a próxima versão inteira do Template.

    A versão é incrementada automaticamente:
        1 -> 2 -> 3 -> ...

    A nova versão passa a ser a versão atual.
    """

    temporary_path = (
        await salvar_upload_temporario(
            file
        )
    )

    version_directory = None

    try:

        template = obter_template_or_404(
            db,
            template_id,
            somente_ativo=True,
            lock=True,
        )

        # Guardamos a origem antes de trocar current_version_id.
        source_template_version_id = (
            template.current_version_id
        )

        # --------------------------------------------------------
        # COMPOSIÇÃO SOLICITADA
        # --------------------------------------------------------
        #
        # None  -> frontend não enviou o campo; herda a composição
        #          da versão atual para manter compatibilidade.
        # []    -> usuário removeu todas as Libraries.
        # [...] -> usa exatamente as versões selecionadas.
        # --------------------------------------------------------

        resolved_libraries = None

        if libraries is not None:
            resolved_libraries = (
                resolver_selecoes_template_libraries(
                    db,
                    libraries,
                )
            )

        max_version = (
            db.query(
                func.max(
                    AutomationTemplateVersion.version
                )
            )
            .filter(
                AutomationTemplateVersion.template_id ==
                    template.id
            )
            .scalar()
        )

        next_version = (
            int(
                max_version or 0
            ) +
            1
        )

        artifact_relative = (
            montar_artifact_path_relativo(
                template.id,
                next_version,
            )
        )

        artifact_absolute = (
            BASE_DIRECTORY /
            artifact_relative
        ).resolve()

        version_directory = (
            artifact_absolute.parent
        )

        artifact_absolute.parent.mkdir(
            parents=True,
            exist_ok=False,
        )

        shutil.copy2(
            temporary_path,
            artifact_absolute,
        )

        version = AutomationTemplateVersion(
            template_id=
                template.id,
            version=
                next_version,
            filename=(
                file.filename or
                "template.zip"
            ),
            artifact_path=
                str(
                    artifact_relative
                ),
            file_hash=
                calcular_sha256(
                    artifact_absolute
                ),
            published_by=
                usuario.id,
        )

        db.add(
            version
        )

        db.flush()

        # --------------------------------------------------------
        # SNAPSHOT ATÔMICO DAS LIBRARIES
        # --------------------------------------------------------
        #
        # Campo ausente mantém o comportamento histórico e herda a
        # composição da versão atual. Campo presente substitui a
        # composição integralmente, inclusive quando vier como [].
        # --------------------------------------------------------

        if libraries is None:

            if source_template_version_id is not None:
                copiar_dependencias_template_version(
                    db=db,
                    source_template_version_id=
                        source_template_version_id,
                    target_template_version_id=
                        version.id,
                    created_by=
                        usuario.id,
                )

        else:
            registrar_composicao_template_version(
                db=db,
                template_version_id=
                    version.id,
                resolved_libraries=
                    resolved_libraries or [],
                created_by=
                    usuario.id,
            )

        # A versão recém-publicada passa a ser a atual.
        template.current_version_id = (
            version.id
        )

        db.commit()

        db.refresh(
            template
        )

        db.refresh(
            version
        )

        logger.info(
            "Nova versão de Template publicada",
            extra={
                "event":
                    "automation_template_version_published",
                "template_id":
                    template.id,
                "template_version":
                    version.version,
                "user_id":
                    usuario.id,
                "status":
                    "success",
            },
        )

        versions = (
            db.query(
                AutomationTemplateVersion
            )
            .filter(
                AutomationTemplateVersion.template_id ==
                    template.id
            )
            .order_by(
                AutomationTemplateVersion.version.desc()
            )
            .all()
        )

        return {
            "status":
                "success",

            "message": (
                f"Versão v{version.version} "
                "publicada com sucesso."
            ),

            "template":
                serializar_template(
                    template,
                    versions=versions,
                ),
        }

    except HTTPException:

        db.rollback()

        if version_directory:
            shutil.rmtree(
                version_directory,
                ignore_errors=True,
            )

        raise

    except IntegrityError as error:

        db.rollback()

        if version_directory:
            shutil.rmtree(
                version_directory,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "A nova versão do Template não "
                "pôde ser registrada."
            ),
        ) from error

    except Exception as error:

        db.rollback()

        if version_directory:
            shutil.rmtree(
                version_directory,
                ignore_errors=True,
            )

        registrar_falha_publicacao_template(
            template_id=template_id,
            user_id=getattr(
                usuario,
                "id",
                None,
            ),
            error=error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível publicar a nova "
                "versão do Template."
            ),
        ) from error

    finally:

        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass


# ============================================================
# METADADOS
# ============================================================

def atualizar_template_service(
    *,
    template_id: int,
    name: str | None,
    description: str | None,
    is_active: bool | None,
    db: Session,
    usuario,
) -> dict:
    """
    Atualiza apenas metadados do Template.

    O código do Template nunca é sobrescrito por este método.
    Para alterar código, publique uma nova versão.
    """

    template = obter_template_or_404(
        db,
        template_id,
        lock=True,
    )

    if name is not None:

        normalized_name = name.strip()

        if not normalized_name:
            raise HTTPException(
                status_code=400,
                detail=(
                    "O nome do Template não pode "
                    "ficar vazio."
                ),
            )

        duplicate = (
            db.query(
                AutomationTemplate
            )
            .filter(
                AutomationTemplate.id !=
                    template.id,

                func.lower(
                    AutomationTemplate.name
                ) ==
                    normalized_name.lower(),
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Já existe um Template com esse nome."
                ),
            )

        template.name = (
            normalized_name
        )

    if description is not None:
        template.description = (
            description.strip() or
            None
        )

    if is_active is not None:
        template.is_active = (
            1
            if is_active
            else 0
        )

    try:
        db.commit()

        db.refresh(
            template
        )

    except IntegrityError as error:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível atualizar o Template."
            ),
        ) from error

    versions = (
        db.query(
            AutomationTemplateVersion
        )
        .filter(
            AutomationTemplateVersion.template_id ==
                template.id
        )
        .order_by(
            AutomationTemplateVersion.version.desc()
        )
        .all()
    )

    logger.info(
        "Template atualizado",
        extra={
            "event":
                "automation_template_updated",
            "template_id":
                template.id,
            "user_id":
                usuario.id,
            "status":
                "success",
        },
    )

    return {
        "status":
            "success",

        "template":
            serializar_template(
                template,
                versions=versions,
            ),
    }


def definir_versao_atual_service(
    *,
    template_id: int,
    version_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Altera explicitamente qual versão do Template é a atual.

    Isso permite rollback administrativo sem apagar versões.
    """

    template = obter_template_or_404(
        db,
        template_id,
        lock=True,
    )

    version = (
        db.query(
            AutomationTemplateVersion
        )
        .filter(
            AutomationTemplateVersion.id ==
                version_id,

            AutomationTemplateVersion.template_id ==
                template.id,
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail=(
                "A versão informada não pertence "
                "ao Template."
            ),
        )

    template.current_version_id = (
        version.id
    )

    db.commit()

    db.refresh(
        template
    )

    logger.info(
        "Versão atual do Template alterada",
        extra={
            "event":
                "automation_template_current_version_changed",
            "template_id":
                template.id,
            "template_version":
                version.version,
            "user_id":
                usuario.id,
            "status":
                "success",
        },
    )

    versions = (
        db.query(
            AutomationTemplateVersion
        )
        .filter(
            AutomationTemplateVersion.template_id ==
                template.id
        )
        .order_by(
            AutomationTemplateVersion.version.desc()
        )
        .all()
    )

    return {
        "status":
            "success",

        "template":
            serializar_template(
                template,
                versions=versions,
            ),
    }


# ============================================================
# DOWNLOAD
# ============================================================

def obter_download_template_version_service(
    *,
    template_id: int,
    version_id: int,
    db: Session,
) -> tuple[
    Path,
    str,
]:
    """
    Resolve o ZIP imutável de uma versão para download.
    """

    template = obter_template_or_404(
        db,
        template_id,
    )

    version = (
        db.query(
            AutomationTemplateVersion
        )
        .filter(
            AutomationTemplateVersion.id ==
                version_id,

            AutomationTemplateVersion.template_id ==
                template.id,
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail=(
                "Versão do Template não encontrada."
            ),
        )

    artifact_path = (
        resolver_artifact_path(
            version.artifact_path
        )
    )

    if not artifact_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "O arquivo físico desta versão "
                "não foi encontrado."
            ),
        )

    expected_hash = (
        version.file_hash
    )

    actual_hash = (
        calcular_sha256(
            artifact_path
        )
    )

    if (
        expected_hash and
        actual_hash != expected_hash
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "O artefato do Template falhou "
                "na validação de integridade."
            ),
        )

    safe_name = (
        "".join(
            character
            if (
                character.isalnum() or
                character in (
                    "-",
                    "_",
                    ".",
                )
            )
            else "_"
            for character in template.name
        )
        or
        f"template_{template.id}"
    )

    download_name = (
        f"{safe_name}_v"
        f"{version.version}.zip"
    )

    return (
        artifact_path,
        download_name,
    )


# ============================================================
# INSTANCIAÇÃO DO TEMPLATE NO WORKSPACE
# ============================================================

def _extrair_zip_seguro(
    *,
    zip_path: Path,
    destination: Path,
) -> None:
    """
    Extrai um ZIP já validado sem utilizar extractall() cegamente.
    """

    destination_resolved = (
        destination.resolve()
    )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        for member in archive.infolist():

            member_path = (
                _normalizar_nome_membro_zip(
                    member.filename
                )
            )

            if not member_path.parts:
                continue

            target = (
                destination /
                Path(
                    *member_path.parts
                )
            ).resolve()

            try:
                target.relative_to(
                    destination_resolved
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O ZIP contém caminho inseguro."
                    ),
                )

            unix_mode = (
                member.external_attr >>
                16
            )

            if stat.S_ISLNK(
                unix_mode
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Links simbólicos não são "
                        "permitidos em Templates."
                    ),
                )

            if member.is_dir():
                target.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                continue

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with archive.open(
                member,
                "r",
            ) as source, target.open(
                "wb",
            ) as output:
                shutil.copyfileobj(
                    source,
                    output,
                )


def _resolver_raiz_logica_extraida(
    staging_path: Path,
) -> Path:
    """
    Remove apenas uma pasta externa única quando o ZIP foi criado
    compactando a pasta do projeto inteira.

    Não altera estruturas internas do projeto.
    """

    children = [
        child
        for child in staging_path.iterdir()
        if child.name not in (
            "__MACOSX",
        )
    ]

    root_main = (
        staging_path /
        "main.py"
    )

    if root_main.is_file():
        return staging_path

    if (
        len(children) == 1 and
        children[0].is_dir() and
        (
            children[0] /
            "main.py"
        ).is_file()
    ):
        return children[0]

    raise HTTPException(
        status_code=400,
        detail=(
            "O Template extraído não possui "
            "main.py na raiz do projeto."
        ),
    )


def instanciar_template_no_workspace(
    *,
    version: AutomationTemplateVersion,
    project_id: int,
) -> Path:
    """
    Cria o Workspace físico de um AutomationProject a partir de
    uma versão imutável de Template.

    A operação copia o código do Template somente uma vez.
    O projeto não mantém dependência física com o ZIP depois disso.
    """

    artifact_path = (
        resolver_artifact_path(
            version.artifact_path
        )
    )

    if not artifact_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "O artefato da versão do Template "
                "não foi encontrado."
            ),
        )

    actual_hash = calcular_sha256(
        artifact_path
    )

    if (
        version.file_hash and
        actual_hash != version.file_hash
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "O artefato da versão do Template "
                "falhou na validação de integridade."
            ),
        )

    workspace_path = (
        validar_workspace_fisico(
            project_id,
            permitir_inexistente=True,
        )
    )

    # Como o ID acabou de ser criado, o Workspace não deveria
    # possuir conteúdo anterior.
    if workspace_path.exists():

        if any(
            workspace_path.iterdir()
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "O Workspace do novo projeto já "
                    "possui conteúdo."
                ),
            )

        workspace_path.rmdir()

    workspace_parent = (
        workspace_path.parent
    )

    workspace_parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    staging_path = (
        workspace_parent /
        (
            f".{workspace_path.name}."
            f"template_{uuid4().hex}"
        )
    )

    try:

        staging_path.mkdir(
            parents=False,
            exist_ok=False,
        )

        _extrair_zip_seguro(
            zip_path=
                artifact_path,
            destination=
                staging_path,
        )

        logical_root = (
            _resolver_raiz_logica_extraida(
                staging_path
            )
        )

        if (
            logical_root ==
            staging_path
        ):

            # Mesmo filesystem: rename atômico do staging inteiro.
            os.replace(
                staging_path,
                workspace_path,
            )

        else:

            # O ZIP possuía uma única pasta externa.
            #
            # Movemos somente essa pasta para o nome oficial
            # do Workspace e removemos o staging residual.
            os.replace(
                logical_root,
                workspace_path,
            )

            shutil.rmtree(
                staging_path,
                ignore_errors=True,
            )

        return workspace_path

    except Exception:

        shutil.rmtree(
            staging_path,
            ignore_errors=True,
        )

        if workspace_path.exists():
            shutil.rmtree(
                workspace_path,
                ignore_errors=True,
            )

        raise
