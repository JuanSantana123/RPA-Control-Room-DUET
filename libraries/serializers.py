# ============================================================
# LIBRARIES - SERIALIZERS
# ============================================================
#
# Serializadores compartilhados pelo domínio global de Libraries.
#
# RESPONSABILIDADES:
#
# - transformar models SQLAlchemy em dicionários da API;
# - preservar exatamente os campos já utilizados pelo frontend;
# - construir a árvore organizacional de pastas + Libraries;
# - enriquecer dependências de projetos com dados da Library
#   e da LibraryVersion correspondente.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints FastAPI.
# Este módulo NÃO realiza commit/rollback.
# Este módulo NÃO altera registros no banco.
# ============================================================


from sqlalchemy.orm import Session

from models import (
    Library,
    LibraryFolder,
    LibraryVersion,
    ProjectLibraryDependency,
)


# ============================================================
# LIBRARY FOLDER
# ============================================================

def serializar_library_folder(
    folder: LibraryFolder,
) -> dict:
    """
    Serializa os metadados básicos de uma pasta do catálogo.
    """

    return {
        "id": folder.id,
        "name": folder.name,
        "parent_id": folder.parent_id,
        "created_by": folder.created_by,
        "created_at": (
            folder.created_at.isoformat()
            if folder.created_at
            else None
        ),
        "updated_at": (
            folder.updated_at.isoformat()
            if folder.updated_at
            else None
        ),
        "is_active": bool(
            folder.is_active
        ),
    }


# ============================================================
# LIBRARY
# ============================================================

def serializar_library(
    library: Library,
) -> dict:
    """
    Serializa os metadados da Library.

    production_version_id:
        identifica a LibraryVersion atualmente vigente em
        Produção.
    """

    return {
        "id": library.id,
        "name": library.name,
        "import_name": library.import_name,
        "description": library.description,
        "folder_id": library.folder_id,
        "production_version_id": (
            library.production_version_id
        ),
        "created_by": library.created_by,
        "created_at": (
            library.created_at.isoformat()
            if library.created_at
            else None
        ),
        "updated_at": (
            library.updated_at.isoformat()
            if library.updated_at
            else None
        ),
        "is_active": bool(
            library.is_active
        ),
    }


# ============================================================
# LIBRARY VERSION
# ============================================================

def serializar_library_version(
    version: LibraryVersion,
    production_version_id: int | None = None,
) -> dict:
    """
    Serializa uma LibraryVersion publicada.

    artifact_path NÃO é retornado ao frontend porque representa
    um caminho interno do servidor.

    O download continuará ocorrendo através de endpoint
    autenticado.

    production_version_id:
        permite identificar se esta LibraryVersion é a versão
        atualmente vigente em Produção.
    """

    return {
        "id": version.id,
        "library_id": version.library_id,
        "version": version.version,
        "source_type": version.source_type,
        "source_robot_id": version.source_robot_id,
        "source_robot_version": version.source_robot_version,
        "source_path": version.source_path,
        "file_hash": version.file_hash,
        "published_by": version.published_by,
        "published_at": (
            version.published_at.isoformat()
            if version.published_at
            else None
        ),
        "is_active": bool(
            version.is_active
        ),

        # True somente quando esta versão é a versão atualmente
        # apontada pela Library como vigente em Produção.
        "is_production": (
            production_version_id == version.id
        ),
    }


# ============================================================
# PROJECT LIBRARY DEPENDENCY
# ============================================================

def serializar_dependencia(
    db: Session,
    dependency: ProjectLibraryDependency,
) -> dict:
    """
    Serializa uma dependência de Library do AutomationProject.

    Além dos IDs armazenados na dependência, consulta:

    - Library;
    - LibraryVersion.

    Isso mantém o contrato amigável já utilizado pelo frontend.
    """

    library = (
        db.query(Library)
        .filter(
            Library.id
            == dependency.library_id
        )
        .first()
    )

    version = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id
            == dependency.library_version_id
        )
        .first()
    )

    return {
        "id": dependency.id,
        "project_id": dependency.project_id,
        "library_id": dependency.library_id,

        "library_name": (
            library.name
            if library
            else None
        ),

        "import_name": (
            library.import_name
            if library
            else None
        ),

        "library_version_id":
            dependency.library_version_id,

        "version": (
            version.version
            if version
            else None
        ),

        "version_is_active": (
            bool(version.is_active)
            if version
            else False
        ),

        # Indica se a versão fixada no projeto é também a versão
        # atualmente vigente em Produção.
        "version_is_production": (
            bool(
                library
                and version
                and library.production_version_id == version.id
            )
        ),

        "production_version_id": (
            library.production_version_id
            if library
            else None
        ),

        "added_by": dependency.added_by,

        "created_at": (
            dependency.created_at.isoformat()
            if dependency.created_at
            else None
        ),

        "updated_at": (
            dependency.updated_at.isoformat()
            if dependency.updated_at
            else None
        ),
    }


# ============================================================
# ÁRVORE DO CATÁLOGO
# ============================================================

def construir_arvore_bibliotecas(
    folders: list[LibraryFolder],
    libraries: list[Library],
) -> list[dict]:
    """
    Monta uma árvore unificada para o frontend.

    Cada nó possui:

        type = "folder"
            LibraryFolder.

        type = "library"
            Library.

    Regras:

    - pastas aparecem antes de Libraries;
    - ordenação por nome;
    - ID funciona como critério final de desempate;
    - pastas sem pai presente na consulta vão para a raiz;
    - Libraries sem pasta presente na consulta vão para a raiz.

    Essa última regra evita que um registro desapareça da
    interface caso exista alguma inconsistência histórica.
    """

    folder_nodes = {}

    # --------------------------------------------------------
    # CRIA OS NÓS DAS PASTAS
    # --------------------------------------------------------

    for folder in folders:

        folder_nodes[folder.id] = {
            "type": "folder",
            **serializar_library_folder(
                folder
            ),
            "children": [],
        }

    root_nodes = []

    # --------------------------------------------------------
    # CONECTA AS PASTAS
    # --------------------------------------------------------

    for folder in folders:

        node = folder_nodes[
            folder.id
        ]

        if (
            folder.parent_id is not None
            and folder.parent_id in folder_nodes
        ):

            folder_nodes[
                folder.parent_id
            ]["children"].append(
                node
            )

        else:

            # Pasta raiz ou pasta cujo pai não está presente na
            # consulta atual.
            root_nodes.append(
                node
            )

    # --------------------------------------------------------
    # CONECTA AS LIBRARIES
    # --------------------------------------------------------

    for library in libraries:

        node = {
            "type": "library",
            **serializar_library(
                library
            ),
        }

        if (
            library.folder_id is not None
            and library.folder_id in folder_nodes
        ):

            folder_nodes[
                library.folder_id
            ]["children"].append(
                node
            )

        else:

            # Library na raiz ou cujo folder_id não está presente
            # na consulta atual.
            root_nodes.append(
                node
            )

    # --------------------------------------------------------
    # ORDENAÇÃO RECURSIVA
    # --------------------------------------------------------

    def ordenar_nos(
        nodes: list[dict],
    ) -> None:
        """
        Ordena cada nível da árvore:

        1. folders;
        2. Libraries;
        3. nome;
        4. ID.
        """

        nodes.sort(
            key=lambda item: (
                0
                if item["type"] == "folder"
                else 1,
                item["name"].lower(),
                item["id"],
            )
        )

        for item in nodes:

            if item["type"] == "folder":

                ordenar_nos(
                    item["children"]
                )

    ordenar_nos(
        root_nodes
    )

    return root_nodes