# ============================================================
# DEVELOPMENT - LIBRARY IMPORT SERVICE
# ============================================================
#
# Responsabilidade:
#
# - importar um ZIP de Library diretamente para um
#   AutomationProject em Desenvolvimento;
# - validar o pacote utilizando as regras oficiais de Libraries;
# - criar uma nova identidade de Library quando o namespace ainda
#   não existir;
# - reutilizar a identidade global quando a Library já estiver
#   publicada;
# - criar a Working Copy dentro de:
#
#       workspaces/<project_id>/_libraries/<import_name>
#
# - NÃO publicar LibraryVersion;
# - NÃO promover nada para Produção.
#
# A publicação continua sendo responsabilidade exclusiva do Release.
# ============================================================


import logging
import os
import shutil
import tempfile
import zipfile

from pathlib import Path

from fastapi import (
    HTTPException,
    UploadFile,
)

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    Library,
    LibraryVersion,
    ProjectLibraryDependency,
    ProjectLibraryDraft,
)

from development.checkout_service import (
    exigir_checkout_workspace,
)

from development.repository import (
    garantir_workspace,
    montar_arvore_workspace,
)

from development.workspace_core import (
    draft_has_changes,
    draft_path,
    draft_workspace_value,
)

from libraries.repository import (
    MAX_LIBRARY_ZIP_SIZE,
    TEMP_REPOSITORY,
    UPLOAD_CHUNK_SIZE,
)

from libraries.validators import (
    validar_import_name,
    validar_zip_biblioteca,
)

from security.artifacts import (
    normalizar_membro_zip,
)


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# METADADOS
# ============================================================

def _normalizar_nome(
    name: str,
) -> str:
    """
    Normaliza e valida o nome amigável da Library.
    """

    nome = name.strip()

    if not nome:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome da biblioteca não pode ficar vazio."
            ),
        )

    if len(nome) > 255:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome da biblioteca não pode ultrapassar "
                "255 caracteres."
            ),
        )

    return nome


def _normalizar_descricao(
    description: str | None,
) -> str | None:
    """
    Normaliza a descrição opcional da Library.
    """

    descricao = (
        description.strip()
        if description
        else None
    )

    if (
        descricao is not None
        and len(descricao) > 5000
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A descrição não pode ultrapassar "
                "5000 caracteres."
            ),
        )

    return descricao


# ============================================================
# PROJETO
# ============================================================

def _obter_projeto_para_importacao(
    project_id: int,
    db: Session,
) -> AutomationProject:
    """
    Obtém e bloqueia o AutomationProject durante a importação.

    O lock evita alterações concorrentes na composição das
    Libraries do mesmo projeto.
    """

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id == project_id,
            AutomationProject.is_active == 1,
        )
        .with_for_update()
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    return projeto


# ============================================================
# COLISÕES DO WORKSPACE
# ============================================================

def _validar_namespace_no_workspace(
    project_id: int,
    import_name: str,
    workspace_path: Path,
) -> Path:
    """
    Garante que o namespace não colida com código do próprio
    projeto nem com outra Working Copy.
    """

    projeto_package = (
        workspace_path /
        import_name
    )

    projeto_module = (
        workspace_path /
        f"{import_name}.py"
    )

    if (
        projeto_package.exists()
        or projeto_module.exists()
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe código do projeto utilizando este "
                "namespace na raiz."
            ),
        )

    target = draft_path(
        project_id,
        import_name,
    )

    if target.exists():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma Working Copy utilizando este "
                "namespace neste projeto."
            ),
        )

    return target


# ============================================================
# UPLOAD TEMPORÁRIO
# ============================================================

async def _salvar_upload_temporario(
    file: UploadFile,
) -> Path:
    """
    Persiste o UploadFile temporariamente antes de validar o ZIP.

    O arquivo permanece fora do Workspace até passar por todas
    as validações estruturais.
    """

    filename = (
        file.filename or ""
    ).strip()

    if not filename.lower().endswith(
        ".zip"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A biblioteca precisa ser enviada "
                "em um arquivo ZIP."
            ),
        )

    temp_fd, temp_name = (
        tempfile.mkstemp(
            prefix="development_library_import_",
            suffix=".zip",
            dir=TEMP_REPOSITORY,
        )
    )

    os.close(
        temp_fd
    )

    temp_path = Path(
        temp_name
    )

    total_bytes = 0

    try:

        with temp_path.open(
            "wb"
        ) as temp_file:

            while True:

                chunk = await file.read(
                    UPLOAD_CHUNK_SIZE
                )

                if not chunk:
                    break

                total_bytes += len(
                    chunk
                )

                if (
                    total_bytes >
                    MAX_LIBRARY_ZIP_SIZE
                ):

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "O ZIP da biblioteca ultrapassa "
                            "o limite de 50 MB."
                        ),
                    )

                temp_file.write(
                    chunk
                )

        if total_bytes == 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "O arquivo enviado está vazio."
                ),
            )

        return temp_path

    except Exception:

        if temp_path.exists():

            try:
                temp_path.unlink()
            except OSError:
                pass

        raise


# ============================================================
# EXTRAÇÃO PARA STAGING
# ============================================================

def _extrair_library_para_staging(
    zip_path: Path,
    import_name: str,
    staging_root: Path,
) -> Path:
    """
    Extrai somente o namespace validado para uma área temporária.

    validar_zip_biblioteca() já garante que todo o conteúdo
    pertence ao import_name e aplica as proteções estruturais
    compartilhadas pelo domínio Libraries.
    """

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as arquivo_zip:

        for membro in arquivo_zip.infolist():

            caminho = normalizar_membro_zip(
                membro.filename
            )

            if not caminho.parts:
                continue

            destino = staging_root.joinpath(
                *caminho.parts
            )

            if membro.is_dir():

                destino.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                continue

            destino.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with (
                arquivo_zip.open(
                    membro,
                    "r",
                ) as origem,
                destino.open(
                    "wb"
                ) as saida,
            ):

                shutil.copyfileobj(
                    origem,
                    saida,
                )

    namespace_path = (
        staging_root /
        import_name
    )

    if not namespace_path.is_dir():

        raise HTTPException(
            status_code=400,
            detail=(
                "O namespace da biblioteca não foi "
                "encontrado após a extração."
            ),
        )

    return namespace_path


# ============================================================
# RESOLVER IDENTIDADE DA LIBRARY
# ============================================================

def _resolver_library(
    *,
    name: str,
    import_name: str,
    description: str | None,
    db: Session,
    usuario,
) -> tuple[
    Library,
    LibraryVersion | None,
    bool,
]:
    """
    Resolve a identidade global do namespace.

    Retorno:
        Library
        LibraryVersion base ou None
        is_new

    Casos:

    namespace inexistente:
        cria Library inativa e sem versão.

    namespace publicado:
        reutiliza Library e sua versão vigente de Produção.

    namespace existente mas ainda não publicado:
        bloqueia a operação para evitar que dois projetos
        assumam a mesma identidade nova.
    """

    library = (
        db.query(Library)
        .filter(
            func.lower(
                Library.import_name
            ) == import_name.lower()
        )
        .with_for_update()
        .first()
    )

    # --------------------------------------------------------
    # NOVA IDENTIDADE
    # --------------------------------------------------------

    if library is None:

        library = Library(
            name=name,
            import_name=import_name,
            description=description,
            folder_id=None,
            production_version_id=None,
            created_by=usuario.id,

            # Ainda não existe versão publicada.
            is_active=0,
        )

        db.add(
            library
        )

        db.flush()

        return (
            library,
            None,
            True,
        )

    # --------------------------------------------------------
    # IDENTIDADE EXISTENTE SEM PRODUÇÃO
    # --------------------------------------------------------

    if (
        library.production_version_id
        is None
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "Este import_name já pertence a uma biblioteca "
                "ainda não publicada em outro fluxo de "
                "Desenvolvimento."
            ),
        )

    # --------------------------------------------------------
    # LIBRARY ARQUIVADA / DESATIVADA
    # --------------------------------------------------------

    if not library.is_active:

        raise HTTPException(
            status_code=409,
            detail=(
                "A biblioteca existe, mas está arquivada. "
                "Reative-a no catálogo antes de utilizá-la "
                "em Desenvolvimento."
            ),
        )

    production_version = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id ==
                library.production_version_id,

            LibraryVersion.library_id ==
                library.id,

            LibraryVersion.is_active == 1,
        )
        .first()
    )

    if production_version is None:

        raise HTTPException(
            status_code=409,
            detail=(
                "A biblioteca possui uma versão de Produção "
                "inválida ou indisponível."
            ),
        )

    return (
        library,
        production_version,
        False,
    )


# ============================================================
# GARANTIR AUSÊNCIA NO PROJETO
# ============================================================

def _validar_library_nao_adicionada(
    project_id: int,
    library_id: int,
    db: Session,
) -> None:
    """
    Impede que o mesmo projeto possua dois vínculos/drafts da
    mesma Library.
    """

    dependency = (
        db.query(ProjectLibraryDependency)
        .filter(
            ProjectLibraryDependency.project_id ==
                project_id,

            ProjectLibraryDependency.library_id ==
                library_id,
        )
        .first()
    )

    draft = (
        db.query(ProjectLibraryDraft)
        .filter(
            ProjectLibraryDraft.project_id ==
                project_id,

            ProjectLibraryDraft.library_id ==
                library_id,
        )
        .first()
    )

    if (
        dependency is not None
        or draft is not None
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "Esta biblioteca já está adicionada "
                "ao projeto."
            ),
        )


# ============================================================
# IMPORTAR ZIP PARA DEVELOPMENT
# ============================================================

async def importar_biblioteca_projeto_service(
    *,
    project_id: int,
    name: str,
    import_name: str,
    description: str | None,
    file: UploadFile,
    db: Session,
    usuario,
) -> dict:
    """
    Importa uma Library diretamente para a Working Copy de um
    AutomationProject.

    Esta operação nunca cria LibraryVersion.

    Library nova:
        Library(is_active=0)
        ProjectLibraryDraft(base=None)

    Library já publicada:
        reutiliza a Library
        ProjectLibraryDependency(production version)
        ProjectLibraryDraft(base=production version)

    O código somente chega ao Workspace depois de o ZIP passar
    pelas validações oficiais do domínio Libraries.
    """

    temp_path: Path | None = None
    staging_root: Path | None = None
    target: Path | None = None

    target_materialized = False

    try:

        # ====================================================
        # PROJETO + CHECKOUT
        # ====================================================

        _obter_projeto_para_importacao(
            project_id=project_id,
            db=db,
        )

        exigir_checkout_workspace(
            project_id=project_id,
            user_id=usuario.id,
            db=db,
        )

        # ====================================================
        # METADADOS
        # ====================================================

        nome = _normalizar_nome(
            name
        )

        namespace = validar_import_name(
            import_name
        )

        descricao = _normalizar_descricao(
            description
        )

        # ====================================================
        # WORKSPACE
        # ====================================================

        workspace_path = garantir_workspace(
            project_id
        )

        target = _validar_namespace_no_workspace(
            project_id=project_id,
            import_name=namespace,
            workspace_path=workspace_path,
        )

        # ====================================================
        # RECEBER + VALIDAR ZIP
        # ====================================================

        temp_path = (
            await _salvar_upload_temporario(
                file
            )
        )

        validar_zip_biblioteca(
            temp_path,
            namespace,
        )

        # ====================================================
        # STAGING FÍSICO
        # ====================================================

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        staging_root = Path(
            tempfile.mkdtemp(
                prefix=(
                    f".duet-import-"
                    f"{namespace}-"
                ),
                dir=target.parent,
            )
        )

        namespace_staging = (
            _extrair_library_para_staging(
                zip_path=temp_path,
                import_name=namespace,
                staging_root=staging_root,
            )
        )

        # ====================================================
        # RESOLVER IDENTIDADE
        # ====================================================

        (
            library,
            base_version,
            is_new,
        ) = _resolver_library(
            name=nome,
            import_name=namespace,
            description=descricao,
            db=db,
            usuario=usuario,
        )

        _validar_library_nao_adicionada(
            project_id=project_id,
            library_id=library.id,
            db=db,
        )

        # ====================================================
        # DEPENDÊNCIA PUBLICADA
        # ====================================================

        dependency = None

        if base_version is not None:

            dependency = ProjectLibraryDependency(
                project_id=project_id,
                library_id=library.id,
                library_version_id=base_version.id,
                added_by=usuario.id,
            )

            db.add(
                dependency
            )

            db.flush()

        # ====================================================
        # MATERIALIZAR WORKING COPY
        # ====================================================

        os.replace(
            namespace_staging,
            target,
        )

        target_materialized = True

        # ====================================================
        # ALTERAÇÃO REAL
        # ====================================================

        if base_version is None:

            is_modified = True

        else:

            is_modified = draft_has_changes(
                project_id,
                library,
                base_version,
            )

        # ====================================================
        # DRAFT
        # ====================================================

        draft = ProjectLibraryDraft(
            project_id=project_id,
            library_id=library.id,

            base_library_version_id=(
                base_version.id
                if base_version
                else None
            ),

            workspace_path=
                draft_workspace_value(
                    project_id,
                    namespace,
                ),

            is_modified=(
                1
                if is_modified
                else 0
            ),

            created_by=usuario.id,
            updated_by=usuario.id,
        )

        db.add(
            draft
        )

        db.flush()

        # ====================================================
        # COMMIT ÚNICO
        # ====================================================

        db.commit()

        db.refresh(
            library
        )

        db.refresh(
            draft
        )

        if dependency is not None:
            db.refresh(
                dependency
            )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Biblioteca importada para Development",
            extra={
                "event":
                    "development_library_imported",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "library_id":
                    library.id,

                "import_name":
                    library.import_name,

                "is_new":
                    is_new,

                "base_library_version_id": (
                    base_version.id
                    if base_version
                    else None
                ),

                "status":
                    "success",
            },
        )

        # ====================================================
        # RETORNO
        # ====================================================

        return {
            "status":
                "success",

            "message":
                "Biblioteca importada para o projeto com sucesso.",

            "library": {
                "library_id":
                    library.id,

                "name":
                    library.name,

                "import_name":
                    library.import_name,

                "description":
                    library.description,

                "state": (
                    "new"
                    if is_new
                    else "linked"
                ),

                "is_new":
                    is_new,

                "is_modified":
                    is_modified,

                "dependency_id": (
                    dependency.id
                    if dependency
                    else None
                ),

                "library_version_id": (
                    base_version.id
                    if base_version
                    else None
                ),

                "version": (
                    base_version.version
                    if base_version
                    else None
                ),

                "production_version_id":
                    library.production_version_id,

                "draft_id":
                    draft.id,
            },

            "tree":
                montar_arvore_workspace(
                    workspace_path,
                    workspace_path,
                ),
        }

    # ========================================================
    # ERRO DE NEGÓCIO
    # ========================================================

    except HTTPException:

        db.rollback()

        if (
            target_materialized
            and target is not None
            and target.exists()
        ):

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

        raise

    # ========================================================
    # CONFLITO DE INTEGRIDADE
    # ========================================================

    except IntegrityError as error:

        db.rollback()

        if (
            target_materialized
            and target is not None
            and target.exists()
        ):

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível importar a biblioteca porque "
                "o namespace ou vínculo foi criado por outra "
                "operação concorrente."
            ),
        ) from error

    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception as error:

        db.rollback()

        if (
            target_materialized
            and target is not None
            and target.exists()
        ):

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

        logger.exception(
            "Falha ao importar biblioteca para Development",
            extra={
                "event":
                    "development_library_import_failed",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

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
                "Não foi possível importar a biblioteca "
                "para o projeto."
            ),
        ) from error

    # ========================================================
    # LIMPEZA
    # ========================================================

    finally:

        try:
            await file.close()
        except Exception:
            pass

        if (
            temp_path is not None
            and temp_path.exists()
        ):

            try:
                temp_path.unlink()
            except OSError:
                pass

        if (
            staging_root is not None
            and staging_root.exists()
        ):

            shutil.rmtree(
                staging_root,
                ignore_errors=True,
            )