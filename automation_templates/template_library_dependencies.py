# ============================================================
# AUTOMATION TEMPLATES - LIBRARY DEPENDENCIES
# ============================================================
#
# Responsável somente pela camada de dependências entre:
#
#     AutomationTemplateVersion
#             ↓
#     TemplateVersionLibraryDependency
#             ↓
#     Library / LibraryVersion
#
# Este módulo NÃO cria versões de Template e NÃO manipula ZIPs.
# Ele concentra validação, consulta, serialização e cópia do
# snapshot de Libraries para evitar duplicação de regra.
# ============================================================

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    Library,
    LibraryVersion,
    TemplateVersionLibraryDependency,
)


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def serializar_dependencia_template_library(
    dependency: TemplateVersionLibraryDependency,
    library: Library,
    version: LibraryVersion,
) -> dict:
    """
    Serializa uma Library vinculada a uma versão específica
    de Template.
    """

    return {
        "dependency_id": dependency.id,
        "template_version_id": dependency.template_version_id,
        "library_id": library.id,
        "name": library.name,
        "import_name": library.import_name,
        "description": library.description,
        "library_version_id": version.id,
        "version": version.version,
        "production_version_id": library.production_version_id,
        "is_production":
            library.production_version_id == version.id,
        "library_is_active":
            bool(library.is_active),
        "version_is_active":
            bool(version.is_active),
        "created_by": dependency.created_by,
        "created_at": (
            dependency.created_at.isoformat()
            if dependency.created_at
            else None
        ),
    }


# ============================================================
# CONSULTA
# ============================================================

def carregar_dependencias_template_version(
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
    Carrega o snapshot de Libraries pertencente a uma versão
    imutável de Template.
    """

    return (
        db.query(
            TemplateVersionLibraryDependency,
            Library,
            LibraryVersion,
        )
        .join(
            Library,
            Library.id ==
                TemplateVersionLibraryDependency.library_id,
        )
        .outerjoin(
            LibraryVersion,
            LibraryVersion.id ==
                Library.production_version_id,
        )
        .filter(
            TemplateVersionLibraryDependency.template_version_id ==
                template_version_id
        )
        .order_by(
            Library.name.asc(),
            Library.id.asc(),
        )
        .all()
    )

def serializar_dependencia_template_library(
    dependency: TemplateVersionLibraryDependency,
    library: Library,
    production_version: LibraryVersion | None,
) -> dict:
    """
    Serializa uma Library pertencente a uma versão de Template.

    O Template NÃO fixa LibraryVersion.

    A LibraryVersion retornada aqui representa apenas a versão
    atualmente vigente em Produção e serve para informação do
    frontend. Ela não pertence ao snapshot funcional do Template.
    """

    return {
        "dependency_id": dependency.id,
        "template_version_id": dependency.template_version_id,

        "library_id": library.id,
        "name": library.name,
        "import_name": library.import_name,
        "description": library.description,

        # Mantidos no contrato HTTP para compatibilidade com o
        # frontend, porém representam a Produção atual e não uma
        # versão persistida no Template.
        "library_version_id": (
            production_version.id
            if production_version
            else None
        ),
        "version": (
            production_version.version
            if production_version
            else None
        ),

        "production_version_id":
            library.production_version_id,

        "is_production":
            production_version is not None,

        "library_is_active":
            bool(library.is_active),

        "version_is_active": (
            bool(production_version.is_active)
            if production_version
            else False
        ),

        "created_by": dependency.created_by,

        "created_at": (
            dependency.created_at.isoformat()
            if dependency.created_at
            else None
        ),
    }


# ============================================================
# CONSULTA
# ============================================================

def carregar_dependencias_template_version(
    db: Session,
    template_version_id: int,
) -> list[
    tuple[
        TemplateVersionLibraryDependency,
        Library,
        LibraryVersion | None,
    ]
]:
    """
    Carrega as Libraries pertencentes a uma versão imutável
    de Template.

    O snapshot contém somente a identidade da Library.

    A LibraryVersion retornada é resolvida dinamicamente através
    de Library.production_version_id e NÃO faz parte do snapshot.
    """

    return (
        db.query(
            TemplateVersionLibraryDependency,
            Library,
            LibraryVersion,
        )
        .join(
            Library,
            Library.id ==
                TemplateVersionLibraryDependency.library_id,
        )
        .outerjoin(
            LibraryVersion,
            LibraryVersion.id ==
                Library.production_version_id,
        )
        .filter(
            TemplateVersionLibraryDependency.template_version_id ==
                template_version_id
        )
        .order_by(
            Library.name.asc(),
            Library.id.asc(),
        )
        .all()
    )


def serializar_dependencias_template_version(
    db: Session,
    template_version_id: int,
) -> list[dict]:
    """
    Retorna as Libraries de uma versão de Template prontas
    para o contrato HTTP.
    """

    return [
        serializar_dependencia_template_library(
            dependency,
            library,
            production_version,
        )
        for dependency, library, production_version
        in carregar_dependencias_template_version(
            db,
            template_version_id,
        )
    ]

# ============================================================
# VALIDAÇÃO DE UMA NOVA COMPOSIÇÃO
# ============================================================

def resolver_selecoes_template_libraries(
    db: Session,
    selections: list[dict],
) -> list[
    tuple[
        Library,
        LibraryVersion,
    ]
]:
    """
    Valida Libraries selecionadas para uma nova versão de Template.

    REGRA DE DOMÍNIO
    ----------------
    O Template registra somente Library.id.

    Library.production_version_id é consultado aqui apenas para:
    - garantir que a Library está utilizável;
    - fornecer informação de Produção ao restante do fluxo;
    - manter compatibilidade com o contrato atual.

    A LibraryVersion NÃO será persistida no Template.
    """

    if len(selections) > 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "Um Template não pode possuir mais de "
                "100 Libraries nesta operação."
            ),
        )

    try:
        library_ids = [
            int(item["library_id"])
            for item in selections
        ]
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=(
                "A composição de Libraries possui "
                "um library_id inválido."
            ),
        ) from error

    if len(library_ids) != len(set(library_ids)):
        raise HTTPException(
            status_code=400,
            detail=(
                "Uma mesma Library não pode aparecer "
                "mais de uma vez no Template."
            ),
        )

    if not library_ids:
        return []

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

    resolved: list[
        tuple[
            Library,
            LibraryVersion,
        ]
    ] = []

    # Mantém a ordem enviada pelo frontend.
    for library_id in library_ids:

        library = libraries_by_id.get(
            library_id
        )

        if library is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Library #{library_id} não foi encontrada."
                ),
            )

        if not library.is_active:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A Library "{library.name}" está desativada.'
                ),
            )

        if library.production_version_id is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A Library "{library.name}" não possui '
                    "versão vigente em Produção."
                ),
            )

        production_version = (
            db.query(LibraryVersion)
            .filter(
                LibraryVersion.id ==
                    library.production_version_id,
                LibraryVersion.library_id ==
                    library.id,
            )
            .first()
        )

        if production_version is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A versão de Produção da Library '
                    f'"{library.name}" não foi encontrada.'
                ),
            )

        if not production_version.is_active:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A versão de Produção da Library '
                    f'"{library.name}" está desativada.'
                ),
            )

        resolved.append(
            (
                library,
                production_version,
            )
        )

    return resolved

# ============================================================
# SNAPSHOT
# ============================================================
def copiar_dependencias_template_version(
    *,
    db: Session,
    source_template_version_id: int,
    target_template_version_id: int,
    created_by: int,
) -> None:
    """
    Copia somente a composição de Libraries entre versões
    de Template.

    Nenhuma LibraryVersion é copiada ou fixada.

    Nenhum commit é realizado aqui.
    """

    dependencies = (
        db.query(
            TemplateVersionLibraryDependency
        )
        .filter(
            TemplateVersionLibraryDependency.template_version_id ==
                source_template_version_id
        )
        .all()
    )

    for dependency in dependencies:
        db.add(
            TemplateVersionLibraryDependency(
                template_version_id=
                    target_template_version_id,

                library_id=
                    dependency.library_id,

                # Campo legado permanece NULL em vínculos novos.
                legacy_library_version_id=
                    None,

                created_by=
                    created_by,
            )
        )

def registrar_composicao_template_version(
    *,
    db: Session,
    template_version_id: int,
    resolved_libraries: list[
        tuple[
            Library,
            LibraryVersion,
        ]
    ],
    created_by: int,
) -> None:
    """
    Registra quais Libraries pertencem à nova versão de Template.

    A versão vigente em Produção foi validada anteriormente,
    porém NÃO é persistida no Template.
    """

    for library, _production_version in resolved_libraries:

        db.add(
            TemplateVersionLibraryDependency(
                template_version_id=
                    template_version_id,

                library_id=
                    library.id,

                # Somente histórico legado usa este campo.
                legacy_library_version_id=
                    None,

                created_by=
                    created_by,
            )
        )