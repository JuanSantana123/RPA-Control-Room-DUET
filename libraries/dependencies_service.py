# ============================================================
# LIBRARIES - DEPENDENCIES SERVICE
# ============================================================
#
# Regras de negócio das Libraries utilizadas por projetos de
# Desenvolvimento.
#
# RESPONSABILIDADES:
#
# - listar dependências;
# - listar Libraries publicadas disponíveis;
# - adicionar várias Libraries atomicamente;
# - adicionar uma Library;
# - trocar a versão fixada;
# - remover uma Library do projeto.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints.
# Depends() e RBAC permanecem em api/libraries.py.
# ============================================================


import logging

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from development.workspace_core import (
    commit_dependency_change,
    draft_workspace_value,
)

from models import (
    Library,
    LibraryVersion,
    ProjectLibraryDependency,
    ProjectLibraryDraft,
)

from schemas.libraries import (
    ProjectLibraryDependenciesBulkCreate,
    ProjectLibraryDependencyCreate,
    ProjectLibraryDependencyUpdate,
)

from libraries.repository import (
    BASE_DIRECTORY,
)

from libraries.serializers import (
    serializar_dependencia,
    serializar_library,
    serializar_library_version,
)

from libraries.snapshot_service import (
    resolver_artefato_versao_publicada,
)

from libraries.validators import (
    calcular_sha256,
    exigir_checkout_projeto,
    obter_library_or_404,
    obter_projeto_ativo_or_404,
    validar_zip_biblioteca,
)


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR DEPENDÊNCIAS DO PROJETO
# ============================================================

def listar_dependencias_projeto_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Lista as LibraryVersions fixadas no AutomationProject.

    Operação somente leitura: não exige Checkout.
    """

    obter_projeto_ativo_or_404(
        db,
        project_id,
    )

    dependencias = (
        db.query(ProjectLibraryDependency)
        .filter(
            ProjectLibraryDependency.project_id
            == project_id
        )
        .order_by(
            ProjectLibraryDependency.id.asc()
        )
        .all()
    )

    return {
        "status": "success",
        "project_id": project_id,
        "total": len(dependencias),
        "dependencies": [
            serializar_dependencia(
                db,
                dependency,
            )
            for dependency in dependencias
        ],
    }


# ============================================================
# LIBRARIES DISPONÍVEIS PARA O PROJETO
# ============================================================

def listar_bibliotecas_disponiveis_projeto_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Retorna Libraries publicadas disponíveis para o projeto.

    Regras:

    - Library ativa;
    - precisa possuir versão em Produção;
    - somente versões ativas são oferecidas;
    - Produção é a versão padrão;
    - versões anteriores permanecem disponíveis;
    - informa se a Library já está no projeto.
    """

    obter_projeto_ativo_or_404(
        db,
        project_id,
    )

    dependencias = (
        db.query(ProjectLibraryDependency)
        .filter(
            ProjectLibraryDependency.project_id
            == project_id
        )
        .all()
    )

    dependencias_por_library = {
        dependency.library_id:
            dependency
        for dependency in dependencias
    }

    libraries = (
        db.query(Library)
        .filter(
            Library.is_active == 1,
            Library.production_version_id.isnot(None),
        )
        .order_by(
            func.lower(
                Library.name
            ).asc(),
            Library.id.asc(),
        )
        .all()
    )

    if not libraries:

        return {
            "status": "success",
            "project_id": project_id,
            "total": 0,
            "libraries": [],
        }

    library_ids = [
        library.id
        for library in libraries
    ]

    versions = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.library_id.in_(
                library_ids
            ),
            LibraryVersion.is_active == 1,
        )
        .order_by(
            LibraryVersion.published_at.desc(),
            LibraryVersion.id.desc(),
        )
        .all()
    )

    versions_por_library: dict[
        int,
        list[LibraryVersion]
    ] = {
        library_id: []
        for library_id in library_ids
    }

    for version in versions:

        versions_por_library.setdefault(
            version.library_id,
            [],
        ).append(
            version
        )

    resultado = []

    for library in libraries:

        library_versions = (
            versions_por_library.get(
                library.id,
                [],
            )
        )

        # A versão vigente em Produção será a seleção padrão
        # apresentada pelo Studio.
        production_version = next(
            (
                version
                for version in library_versions
                if version.id
                == library.production_version_id
            ),
            None,
        )

        # Defesa contra dados históricos inconsistentes.
        if production_version is None:

            logger.warning(
                "Library publicada sem versão de Produção utilizável",
                extra={
                    "event":
                        "library_catalog_invalid_production",
                    "library_id":
                        library.id,
                    "production_version_id":
                        library.production_version_id,
                },
            )

            continue

        dependency = (
            dependencias_por_library.get(
                library.id
            )
        )

        resultado.append({
            "library":
                serializar_library(
                    library
                ),

            "default_version_id":
                production_version.id,

            "production_version":
                serializar_library_version(
                    production_version,
                    library.production_version_id,
                ),

            "already_added":
                dependency is not None,

            "current_dependency": (
                serializar_dependencia(
                    db,
                    dependency,
                )
                if dependency
                else None
            ),

            "versions": [
                serializar_library_version(
                    version,
                    library.production_version_id,
                )
                for version
                in library_versions
            ],
        })

    return {
        "status": "success",
        "project_id": project_id,
        "total": len(resultado),
        "libraries": resultado,
    }


# ============================================================
# ADICIONAR LIBRARIES EM LOTE
# ============================================================

def adicionar_dependencias_projeto_em_lote_service(
    project_id: int,
    request: ProjectLibraryDependenciesBulkCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Adiciona uma ou várias LibraryVersions ao projeto.

    ATOMICIDADE:

        todas válidas -> grava todas;
        uma inválida  -> não grava nenhuma.

    Existe apenas UM commit para o lote inteiro.
    """

    version_ids = (
        request.library_version_ids
    )

    # --------------------------------------------------------
    # VALIDAÇÃO BÁSICA
    # --------------------------------------------------------

    if not version_ids:

        raise HTTPException(
            status_code=400,
            detail=(
                "Selecione pelo menos uma biblioteca."
            ),
        )

    if len(version_ids) != len(
        set(version_ids)
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A mesma versão foi informada "
                "mais de uma vez."
            ),
        )

    # Também bloqueia a linha do projeto com FOR UPDATE.
    obter_projeto_ativo_or_404(
        db,
        project_id,
    )

    exigir_checkout_projeto(
        db,
        project_id,
        usuario.id,
    )

    # --------------------------------------------------------
    # CARREGA AS VERSÕES
    # --------------------------------------------------------

    versions = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id.in_(
                version_ids
            )
        )
        .all()
    )

    versions_por_id = {
        version.id:
            version
        for version in versions
    }

    missing_version_ids = [
        version_id
        for version_id in version_ids
        if version_id
        not in versions_por_id
    ]

    if missing_version_ids:

        raise HTTPException(
            status_code=404,
            detail={
                "message":
                    "Uma ou mais versões de biblioteca "
                    "não foram encontradas.",

                "library_version_ids":
                    missing_version_ids,
            },
        )

    # Mantém a ordem enviada pelo frontend.
    selected_versions = [
        versions_por_id[
            version_id
        ]
        for version_id in version_ids
    ]

    inactive_versions = [
        version.id
        for version in selected_versions
        if not version.is_active
    ]

    if inactive_versions:

        raise HTTPException(
            status_code=409,
            detail={
                "message":
                    "Uma ou mais versões selecionadas "
                    "estão desativadas.",

                "library_version_ids":
                    inactive_versions,
            },
        )

    # --------------------------------------------------------
    # UMA VERSÃO POR LIBRARY
    # --------------------------------------------------------

    selected_library_ids = [
        version.library_id
        for version in selected_versions
    ]

    if len(selected_library_ids) != len(
        set(selected_library_ids)
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Não é possível selecionar duas versões "
                "da mesma biblioteca na mesma operação."
            ),
        )

    # --------------------------------------------------------
    # CARREGA AS LIBRARIES
    # --------------------------------------------------------

    libraries = (
        db.query(Library)
        .filter(
            Library.id.in_(
                selected_library_ids
            )
        )
        .all()
    )

    libraries_por_id = {
        library.id:
            library
        for library in libraries
    }

    selected_libraries: list[Library] = []

    for version in selected_versions:

        library = (
            libraries_por_id.get(
                version.library_id
            )
        )

        if not library:

            raise HTTPException(
                status_code=404,
                detail=(
                    "A biblioteca pertencente a uma "
                    "das versões não foi encontrada."
                ),
            )

        if not library.is_active:

            raise HTTPException(
                status_code=409,
                detail=(
                    f'A biblioteca "{library.name}" '
                    "está desativada."
                ),
            )

        if library.production_version_id is None:

            raise HTTPException(
                status_code=409,
                detail=(
                    f'A biblioteca "{library.name}" '
                    "ainda não possui versão em Produção."
                ),
            )

        selected_libraries.append(
            library
        )

    # Defesa adicional contra namespaces conflitantes.
    selected_import_names = [
        library.import_name
        for library in selected_libraries
    ]

    if len(selected_import_names) != len(
        set(selected_import_names)
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "As bibliotecas selecionadas possuem "
                "namespaces Python conflitantes."
            ),
        )

    # --------------------------------------------------------
    # DEPENDÊNCIAS JÁ EXISTENTES
    # --------------------------------------------------------

    existing_dependencies = (
        db.query(ProjectLibraryDependency)
        .filter(
            ProjectLibraryDependency.project_id
            == project_id,

            ProjectLibraryDependency.library_id.in_(
                selected_library_ids
            ),
        )
        .all()
    )

    if existing_dependencies:

        existing_names = []

        for dependency in existing_dependencies:

            library = (
                libraries_por_id.get(
                    dependency.library_id
                )
            )

            existing_names.append(
                library.name
                if library
                else str(
                    dependency.library_id
                )
            )

        raise HTTPException(
            status_code=409,
            detail={
                "message":
                    "Uma ou mais bibliotecas selecionadas "
                    "já pertencem ao projeto.",

                "libraries":
                    existing_names,
            },
        )

    # --------------------------------------------------------
    # DRAFT ÓRFÃO
    # --------------------------------------------------------

    existing_drafts = (
        db.query(ProjectLibraryDraft)
        .filter(
            ProjectLibraryDraft.project_id
            == project_id,

            ProjectLibraryDraft.library_id.in_(
                selected_library_ids
            ),
        )
        .all()
    )

    if existing_drafts:

        raise HTTPException(
            status_code=409,
            detail=(
                "Existe uma Working Copy inconsistente para "
                "uma das bibliotecas selecionadas. "
                "A operação foi bloqueada para não sobrescrever código."
            ),
        )

    # --------------------------------------------------------
    # VALIDA TODOS OS SNAPSHOTS ANTES DE GRAVAR
    # --------------------------------------------------------

    for version, library in zip(
        selected_versions,
        selected_libraries,
    ):

        artifact_path = (
            resolver_artefato_versao_publicada(
                version
            )
        )

        # O ZIP físico precisa continuar idêntico ao snapshot
        # publicado originalmente.
        if calcular_sha256(
            artifact_path
        ) != version.file_hash:

            raise HTTPException(
                status_code=409,
                detail=(
                    f'A integridade da biblioteca '
                    f'"{library.name}" '
                    f'{version.version} é inválida.'
                ),
            )

        validar_zip_biblioteca(
            artifact_path,
            library.import_name,
        )

        # Caminho oficial:
        #
        # workspaces/<project_id>/_libraries/<import_name>
        workspace_value = (
            draft_workspace_value(
                project_id,
                library.import_name,
            )
        )

        local_draft_path = (
            BASE_DIRECTORY
            / workspace_value
        ).resolve()

        # Compatibilidade defensiva com namespace eventualmente
        # existente diretamente na raiz do projeto.
        root_namespace_path = (
            local_draft_path
            .parent
            .parent
            / library.import_name
        )

        if (
            local_draft_path.exists()
            or root_namespace_path.exists()
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    f'Já existe código local usando o namespace '
                    f'"{library.import_name}". '
                    "A biblioteca não foi adicionada para evitar "
                    "sobrescrever arquivos do projeto."
                ),
            )

    # --------------------------------------------------------
    # GRAVA O LOTE
    # --------------------------------------------------------

    dependencies = []

    try:

        for version, library in zip(
            selected_versions,
            selected_libraries,
        ):

            dependency = (
                ProjectLibraryDependency(
                    project_id=
                        project_id,

                    library_id=
                        library.id,

                    library_version_id=
                        version.id,

                    added_by=
                        usuario.id,
                )
            )

            # Working Copy lógica.
            #
            # O conteúdo físico será materializado posteriormente
            # pelo fluxo ensure_drafts().
            draft = (
                ProjectLibraryDraft(
                    project_id=
                        project_id,

                    library_id=
                        library.id,

                    base_library_version_id=
                        version.id,

                    workspace_path=
                        draft_workspace_value(
                            project_id,
                            library.import_name,
                        ),

                    is_modified=0,

                    created_by=
                        usuario.id,

                    updated_by=None,
                )
            )

            db.add(
                dependency
            )

            db.add(
                draft
            )

            dependencies.append(
                dependency
            )

        # Valida PK/FK/UNIQUE sem confirmar a transação.
        db.flush()

        # CRÍTICO:
        #
        # Um único commit para TODO o lote.
        #
        # Não substituir por commit_dependency_change().
        db.commit()

        for dependency in dependencies:

            db.refresh(
                dependency
            )

        logger.info(
            "Bibliotecas adicionadas ao projeto em lote",
            extra={
                "event":
                    "project_library_dependencies_bulk_added",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "total":
                    len(dependencies),

                "status":
                    "success",
            },
        )

        return {
            "status": "success",

            "message": (
                f"{len(dependencies)} "
                "biblioteca(s) adicionada(s) "
                "ao projeto com sucesso."
            ),

            "project_id":
                project_id,

            "total":
                len(dependencies),

            "dependencies": [
                serializar_dependencia(
                    db,
                    dependency,
                )
                for dependency
                in dependencies
            ],
        }

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível adicionar o lote porque "
                "uma das bibliotecas já possui vínculo ou "
                "Working Copy conflitante no projeto."
            ),
        )

    except HTTPException:

        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao adicionar bibliotecas em lote",
            extra={
                "event":
                    "project_library_dependencies_bulk_add_failed",

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
                "Não foi possível adicionar "
                "as bibliotecas ao projeto."
            ),
        )


# ============================================================
# ADICIONAR UMA LIBRARY
# ============================================================

def adicionar_dependencia_projeto_service(
    project_id: int,
    request: ProjectLibraryDependencyCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Adiciona uma LibraryVersion exata ao projeto.

    Exige projeto ativo e Checkout pertencente ao usuário.
    """

    obter_projeto_ativo_or_404(
        db,
        project_id,
    )

    exigir_checkout_projeto(
        db,
        project_id,
        usuario.id,
    )

    version = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id
            == request.library_version_id
        )
        .first()
    )

    if not version:

        raise HTTPException(
            status_code=404,
            detail="Versão da biblioteca não encontrada.",
        )

    if not version.is_active:

        raise HTTPException(
            status_code=409,
            detail=(
                "Esta versão está desativada e não pode ser adicionada "
                "a novos projetos."
            ),
        )

    library = obter_library_or_404(
        db,
        version.library_id,
    )

    if not library.is_active:

        raise HTTPException(
            status_code=409,
            detail=(
                "A biblioteca está desativada e não pode ser adicionada "
                "a novos projetos."
            ),
        )

    existente = (
        db.query(ProjectLibraryDependency)
        .filter(
            ProjectLibraryDependency.project_id
            == project_id,
            ProjectLibraryDependency.library_id
            == library.id,
        )
        .first()
    )

    if existente:

        atual = serializar_dependencia(
            db,
            existente,
        )

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "O projeto já utiliza esta biblioteca. "
                    "Use a operação de troca de versão."
                ),
                "current_dependency": atual,
            },
        )

    dependency = ProjectLibraryDependency(
        project_id=project_id,
        library_id=library.id,
        library_version_id=version.id,
        added_by=usuario.id,
    )

    draft = ProjectLibraryDraft(
        project_id=project_id,
        library_id=library.id,
        base_library_version_id=version.id,
        workspace_path=draft_workspace_value(
            project_id,
            library.import_name,
        ),
        is_modified=0,
        created_by=usuario.id,
        updated_by=None,
    )

    try:

        db.add(
            dependency
        )

        db.add(
            draft
        )

        # Neste fluxo individual mantemos o mecanismo original,
        # que sincroniza a mudança de composição do projeto.
        commit_dependency_change(
            db,
            project_id,
            library,
        )

        db.refresh(
            dependency
        )

        logger.info(
            "Biblioteca adicionada ao projeto",
            extra={
                "event":
                    "project_library_dependency_added",
                "user_id":
                    usuario.id,
                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Biblioteca adicionada ao projeto com sucesso."
            ),
            "dependency": serializar_dependencia(
                db,
                dependency,
            ),
        }

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "O projeto já possui uma versão desta biblioteca."
            ),
        )

    except HTTPException:
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao adicionar biblioteca ao projeto",
            extra={
                "event":
                    "project_library_dependency_add_failed",
                "user_id":
                    usuario.id,
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
                "Não foi possível adicionar a biblioteca ao projeto."
            ),
        )


# ============================================================
# TROCAR VERSÃO
# ============================================================

def trocar_versao_projeto_service(
    project_id: int,
    library_id: int,
    request: ProjectLibraryDependencyUpdate,
    db: Session,
    usuario,
) -> dict:
    """
    Troca explicitamente a versão fixada de uma Library.

    Não existe atualização automática para latest.
    """

    obter_projeto_ativo_or_404(
        db,
        project_id,
    )

    exigir_checkout_projeto(
        db,
        project_id,
        usuario.id,
    )

    dependency = (
        db.query(ProjectLibraryDependency)
        .filter(
            ProjectLibraryDependency.project_id
            == project_id,
            ProjectLibraryDependency.library_id
            == library_id,
        )
        .first()
    )

    if not dependency:

        raise HTTPException(
            status_code=404,
            detail=(
                "Esta biblioteca não está vinculada ao projeto."
            ),
        )

    version = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id
            == request.library_version_id,
            LibraryVersion.library_id
            == library_id,
        )
        .first()
    )

    if not version:

        raise HTTPException(
            status_code=404,
            detail=(
                "A versão informada não pertence a esta biblioteca."
            ),
        )

    if not version.is_active:

        raise HTTPException(
            status_code=409,
            detail=(
                "A versão informada está desativada."
            ),
        )

    library = obter_library_or_404(
        db,
        library_id,
    )

    if not library.is_active:

        raise HTTPException(
            status_code=409,
            detail=(
                "A biblioteca está desativada."
            ),
        )

    if (
        dependency.library_version_id
        == version.id
    ):

        return {
            "status": "success",
            "message": (
                "O projeto já utiliza esta versão."
            ),
            "already_using_version": True,
            "dependency": serializar_dependencia(
                db,
                dependency,
            ),
        }

    old_version = db.get(
        LibraryVersion,
        dependency.library_version_id,
    )

    dependency.library_version_id = (
        version.id
    )

    dependency.added_by = (
        usuario.id
    )

    draft = (
        db.query(ProjectLibraryDraft)
        .filter(
            ProjectLibraryDraft.project_id
            == project_id,
            ProjectLibraryDraft.library_id
            == library_id,
        )
        .first()
    )

    if draft:

        draft.base_library_version_id = (
            version.id
        )

        draft.is_modified = 0
        draft.updated_by = usuario.id

    else:

        draft = ProjectLibraryDraft(
            project_id=project_id,
            library_id=library.id,
            base_library_version_id=version.id,
            workspace_path=draft_workspace_value(
                project_id,
                library.import_name,
            ),
            is_modified=0,
            created_by=usuario.id,
            updated_by=None,
        )

        db.add(
            draft
        )

    try:

        commit_dependency_change(
            db,
            project_id,
            library,
            old_version,
        )

        db.refresh(
            dependency
        )

        logger.info(
            "Versão de biblioteca alterada no projeto",
            extra={
                "event":
                    "project_library_dependency_updated",
                "user_id":
                    usuario.id,
                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Versão da biblioteca atualizada com sucesso."
            ),
            "already_using_version": False,
            "dependency": serializar_dependencia(
                db,
                dependency,
            ),
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao trocar versão de biblioteca",
            extra={
                "event":
                    "project_library_dependency_update_failed",
                "user_id":
                    usuario.id,
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
                "Não foi possível atualizar a versão da biblioteca."
            ),
        )


# ============================================================
# REMOVER LIBRARY DO PROJETO
# ============================================================

def remover_dependencia_projeto_service(
    project_id: int,
    library_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Remove a Library da composição do AutomationProject.

    Não remove:

    - a Library global;
    - LibraryVersions publicadas;
    - snapshots históricos.
    """

    obter_projeto_ativo_or_404(
        db,
        project_id,
    )

    exigir_checkout_projeto(
        db,
        project_id,
        usuario.id,
    )

    dependency = (
        db.query(ProjectLibraryDependency)
        .filter(
            ProjectLibraryDependency.project_id
            == project_id,
            ProjectLibraryDependency.library_id
            == library_id,
        )
        .first()
    )

    if not dependency:

        raise HTTPException(
            status_code=404,
            detail=(
                "Esta biblioteca não está vinculada ao projeto."
            ),
        )

    library = db.get(
        Library,
        library_id,
    )

    old_version = db.get(
        LibraryVersion,
        dependency.library_version_id,
    )

    draft = (
        db.query(ProjectLibraryDraft)
        .filter(
            ProjectLibraryDraft.project_id
            == project_id,
            ProjectLibraryDraft.library_id
            == library_id,
        )
        .first()
    )

    try:

        db.delete(
            dependency
        )

        if draft:

            db.delete(
                draft
            )

        commit_dependency_change(
            db,
            project_id,
            library,
            old_version,
        )

        logger.info(
            "Biblioteca removida do projeto",
            extra={
                "event":
                    "project_library_dependency_removed",
                "user_id":
                    usuario.id,
                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Biblioteca removida do projeto com sucesso."
            ),
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao remover biblioteca do projeto",
            extra={
                "event":
                    "project_library_dependency_remove_failed",
                "user_id":
                    usuario.id,
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
                "Não foi possível remover a biblioteca do projeto."
            ),
        )