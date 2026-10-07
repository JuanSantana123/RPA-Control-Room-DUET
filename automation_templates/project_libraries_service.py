# ============================================================
# AUTOMATION TEMPLATES - PROJECT LIBRARIES SERVICE
# ============================================================
#
# Integra o snapshot de Libraries de uma AutomationTemplateVersion
# com um AutomationProject durante a CRIAÇÃO do projeto.
#
# RESPONSABILIDADES:
#
# - ler TemplateVersionLibraryDependency da versão escolhida;
# - validar Library e LibraryVersion exatas;
# - preservar a versão fixada pelo Template;
# - criar ProjectLibraryDependency;
# - criar ProjectLibraryDraft limpo;
# - materializar as Libraries em _libraries;
# - participar da transação externa sem executar commit próprio.
#
# IMPORTANTE:
#
# Este service é propositalmente diferente do fluxo interativo de
# Libraries utilizado pelo Studio.
#
# Durante a criação do projeto ainda não existe Checkout para o usuário.
# Portanto este fluxo NÃO pode chamar endpoints/services que:
#
# - exijam Checkout;
# - executem commit próprio;
# - tratem a inclusão como uma edição posterior do projeto.
#
# O commit pertence exclusivamente a development.projects_service.
# ============================================================

from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from development.workspace_core import (
    draft_path,
    draft_workspace_value,
    ensure_drafts,
)

from libraries.snapshot_service import (
    resolver_artefato_versao_publicada,
)

from libraries.validators import (
    calcular_sha256,
    validar_zip_biblioteca,
)

from models import (
    Library,
    LibraryVersion,
    ProjectLibraryDependency,
    ProjectLibraryDraft,
    TemplateVersionLibraryDependency,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# ERROS DE CONSISTÊNCIA DO SNAPSHOT
# ============================================================

def _snapshot_invalido(
    detail: str,
) -> HTTPException:
    """
    Retorna um conflito funcional para snapshots de Template que não
    podem mais ser utilizados com segurança em um projeto novo.

    409 é utilizado porque a versão do Template existe, porém sua
    composição de Libraries está inconsistente ou indisponível.
    """

    return HTTPException(
        status_code=409,
        detail=detail,
    )


# ============================================================
# CARREGAR E VALIDAR SNAPSHOT
# ============================================================

def _carregar_libraries_template(
    *,
    db: Session,
    template_version_id: int,
) -> list[
    tuple[
        TemplateVersionLibraryDependency,
        Library,
        LibraryVersion,
    ]
]:
    """
    Resolve as Libraries de uma versão de Template para a criação
    de um novo AutomationProject.

    REGRA DE DOMÍNIO
    ----------------
    TemplateVersionLibraryDependency guarda somente library_id.

    Neste exato momento é resolvida a LibraryVersion vigente em
    Produção através de Library.production_version_id.

    O ProjectLibraryDependency criado depois deste método fixa
    essa LibraryVersion para o novo projeto.
    """

    snapshots = (
        db.query(
            TemplateVersionLibraryDependency
        )
        .filter(
            TemplateVersionLibraryDependency.template_version_id
            == template_version_id
        )
        .order_by(
            TemplateVersionLibraryDependency.id.asc()
        )
        .all()
    )

    if not snapshots:
        return []

    library_ids = [
        snapshot.library_id
        for snapshot in snapshots
    ]

    # Defesa adicional contra dados históricos inconsistentes.
    if len(library_ids) != len(set(library_ids)):
        raise _snapshot_invalido(
            "A versão do Template possui a mesma biblioteca "
            "mais de uma vez."
        )

    libraries = (
        db.query(Library)
        .filter(
            Library.id.in_(library_ids)
        )
        .all()
    )

    libraries_by_id = {
        library.id: library
        for library in libraries
    }

    # Primeiro validamos todas as Libraries e coletamos somente
    # os production_version_id atuais.
    production_version_ids: list[int] = []

    for snapshot in snapshots:

        library = libraries_by_id.get(
            snapshot.library_id
        )

        if library is None:
            raise _snapshot_invalido(
                "Uma Library utilizada pela versão do Template "
                "não foi encontrada."
            )

        if not library.is_active:
            raise _snapshot_invalido(
                f'A biblioteca "{library.name}" utilizada pelo '
                "Template está desativada para novos projetos."
            )

        if library.production_version_id is None:
            raise _snapshot_invalido(
                f'A biblioteca "{library.name}" utilizada pelo '
                "Template não possui versão vigente em Produção."
            )

        production_version_ids.append(
            library.production_version_id
        )

    versions = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id.in_(
                production_version_ids
            )
        )
        .all()
    )

    versions_by_id = {
        version.id: version
        for version in versions
    }

    result: list[
        tuple[
            TemplateVersionLibraryDependency,
            Library,
            LibraryVersion,
        ]
    ] = []

    for snapshot in snapshots:

        library = libraries_by_id[
            snapshot.library_id
        ]

        production_version = versions_by_id.get(
            library.production_version_id
        )

        if production_version is None:
            raise _snapshot_invalido(
                f'A versão vigente em Produção da biblioteca '
                f'"{library.name}" não foi encontrada.'
            )

        if production_version.library_id != library.id:
            raise _snapshot_invalido(
                f'A versão vigente em Produção da biblioteca '
                f'"{library.name}" pertence a outra Library.'
            )

        if not production_version.is_active:
            raise _snapshot_invalido(
                f'A versão {production_version.version} da '
                f'biblioteca "{library.name}" está desativada.'
            )

        result.append(
            (
                snapshot,
                library,
                production_version,
            )
        )

    return result
# ============================================================
# VALIDAR ARTEFATOS E NAMESPACES
# ============================================================

def _validar_libraries_no_workspace(
    *,
    project_id: int,
    libraries: list[tuple[
        TemplateVersionLibraryDependency,
        Library,
        LibraryVersion,
    ]],
) -> None:
    """
    Valida todos os snapshots antes de criar linhas de dependência.

    Também impede que o ZIP do Template contenha código local com o
    mesmo namespace de uma Library declarada na composição da versão.
    Isso evita aceitar silenciosamente código diferente do snapshot
    publicado da Library.
    """

    for _, library, version in libraries:

        artifact_path = (
            resolver_artefato_versao_publicada(
                version
            )
        )

        if calcular_sha256(
            artifact_path
        ) != version.file_hash:
            raise _snapshot_invalido(
                f'A integridade da biblioteca "{library.name}" '
                f'{version.version} é inválida.'
            )

        validar_zip_biblioteca(
            artifact_path,
            library.import_name,
        )

        target = draft_path(
            project_id,
            library.import_name,
        )

        workspace_root = (
            target.parent.parent
        )

        root_namespace = (
            workspace_root /
            library.import_name
        )

        root_module = (
            workspace_root /
            f"{library.import_name}.py"
        )

        if (
            target.exists()
            or root_namespace.exists()
            or root_module.exists()
        ):
            raise _snapshot_invalido(
                f'O Template já contém código utilizando o namespace '
                f'"{library.import_name}". Remova esse código do ZIP '
                "do Template e mantenha a Library somente na composição "
                "versionada."
            )


# ============================================================
# APLICAR LIBRARIES DO TEMPLATE AO NOVO PROJETO
# ============================================================

def aplicar_bibliotecas_template_ao_projeto(
    *,
    db: Session,
    project_id: int,
    template_version_id: int,
    user_id: int,
) -> int:
    """
    Aplica ao projeto as LibraryVersions fixadas na versão do Template.

    TRANSAÇÃO:

    - NÃO executa commit;
    - NÃO executa rollback;
    - utiliza db.flush() somente para validar PK/FK/UNIQUE;
    - o chamador é responsável pela transação completa.

    Isso permite que:

        AutomationProject
        + Workspace do Template
        + ProjectLibraryDependency
        + ProjectLibraryDraft
        + _libraries

    sejam confirmados ou descartados como uma única operação lógica.
    """

    libraries = _carregar_libraries_template(
        db=db,
        template_version_id=
            template_version_id,
    )

    if not libraries:
        return 0

    _validar_libraries_no_workspace(
        project_id=project_id,
        libraries=libraries,
    )

    for _, library, version in libraries:

        dependency = (
            ProjectLibraryDependency(
                project_id=
                    project_id,
                library_id=
                    library.id,
                library_version_id=
                    version.id,
                added_by=
                    user_id,
            )
        )

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
                    user_id,
                updated_by=None,
            )
        )

        db.add(
            dependency
        )

        db.add(
            draft
        )

    # Valida as referências no banco ainda dentro da transação externa.
    db.flush()

    # Materializa imediatamente as Libraries para que o projeto recém-
    # criado já nasça completo tanto no Studio quanto no Developer Bridge.
    ensure_drafts(
        db,
        project_id,
    )

    # Confirma que a materialização física realmente aconteceu.
    for _, library, _ in libraries:

        target = draft_path(
            project_id,
            library.import_name,
        )

        if not target.is_dir():
            raise RuntimeError(
                "A Library fixada pelo Template não foi "
                f'materializada: {library.import_name}'
            )

    logger.info(
        "Libraries do Template aplicadas ao novo projeto",
        extra={
            "event":
                "template_project_libraries_applied",
            "project_id":
                project_id,
            "template_version_id":
                template_version_id,
            "total":
                len(libraries),
            "user_id":
                user_id,
            "status":
                "success",
        },
    )

    return len(libraries)
