# ============================================================
# LIBRARIES - FOLDERS SERVICE
# ============================================================
#
# Regras de negócio relacionadas à organização do catálogo
# global de Libraries.
#
# RESPONSABILIDADES:
#
# - retornar a árvore Folder -> Library;
# - listar pastas;
# - criar pastas;
# - renomear/mover pastas;
# - desativar pastas vazias;
# - mover Libraries entre pastas.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints FastAPI.
# RBAC continuará sendo responsabilidade de api/libraries.py.
#
# Os métodos recebem:
#
#     db
#         sessão SQLAlchemy fornecida pelo router.
#
#     usuario
#         usuário autenticado fornecido pelo router.
#
# Dessa forma, a regra de negócio deixa de depender diretamente
# de Depends(), require_permission() ou get_db().
# ============================================================


import logging

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    Library,
    LibraryFolder,
)

from schemas.libraries import (
    LibraryFolderCreate,
    LibraryFolderUpdate,
    LibraryMoveRequest,
)

from libraries.serializers import (
    construir_arvore_bibliotecas,
    serializar_library,
    serializar_library_folder,
)

from libraries.validators import (
    obter_library_folder_or_404,
    obter_library_or_404,
    validar_destino_pasta,
    validar_nome_pasta,
    validar_nome_pasta_unico,
)


# Mesmo logger utilizado pelo restante do Control Room.
logger = logging.getLogger(
    "control_room"
)


# ============================================================
# CATÁLOGO - ÁRVORE
# ============================================================

def obter_arvore_bibliotecas_service(
    include_inactive: bool,
    db: Session,
) -> dict:
    """
    Retorna a árvore organizacional completa do catálogo.

    Esta árvore representa somente:

        LibraryFolder
            ↓
        Library

    A estrutura interna dos arquivos Python de uma Library não
    participa desta operação.

    include_inactive=False:
        retorna somente folders e Libraries ativos.
    """

    folder_query = (
        db.query(LibraryFolder)
    )

    library_query = (
        db.query(Library)
    )

    if not include_inactive:

        folder_query = folder_query.filter(
            LibraryFolder.is_active == 1
        )

        library_query = library_query.filter(
            Library.is_active == 1
        )

    folders = (
        folder_query
        .order_by(
            func.lower(
                LibraryFolder.name
            ).asc(),
            LibraryFolder.id.asc(),
        )
        .all()
    )

    libraries = (
        library_query
        .order_by(
            func.lower(
                Library.name
            ).asc(),
            Library.id.asc(),
        )
        .all()
    )

    tree = construir_arvore_bibliotecas(
        folders,
        libraries,
    )

    return {
        "status": "success",
        "total_folders": len(folders),
        "total_libraries": len(libraries),
        "tree": tree,
    }


# ============================================================
# CATÁLOGO - LISTAR PASTAS
# ============================================================

def listar_pastas_bibliotecas_service(
    include_inactive: bool,
    db: Session,
) -> dict:
    """
    Retorna a lista plana de LibraryFolders.

    Essa representação continua útil para:

    - seletores;
    - breadcrumbs;
    - manutenção do catálogo.
    """

    consulta = (
        db.query(LibraryFolder)
    )

    if not include_inactive:

        consulta = consulta.filter(
            LibraryFolder.is_active == 1
        )

    folders = (
        consulta
        .order_by(
            func.lower(
                LibraryFolder.name
            ).asc(),
            LibraryFolder.id.asc(),
        )
        .all()
    )

    return {
        "status": "success",
        "total": len(folders),
        "folders": [
            serializar_library_folder(
                folder
            )
            for folder in folders
        ],
    }


# ============================================================
# CATÁLOGO - CRIAR PASTA
# ============================================================

def criar_pasta_bibliotecas_service(
    request: LibraryFolderCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Cria uma LibraryFolder na raiz ou dentro de outra pasta.

    Não existe limite técnico de profundidade imposto por esta
    regra de negócio.
    """

    nome = validar_nome_pasta(
        request.name
    )

    # Confirma que o parent informado existe, está ativo e pode
    # ser utilizado como destino.
    validar_destino_pasta(
        db,
        request.parent_id,
    )

    # Impede duas pastas ativas com o mesmo nome no mesmo nível.
    validar_nome_pasta_unico(
        db,
        nome,
        request.parent_id,
    )

    folder = LibraryFolder(
        name=nome,
        parent_id=request.parent_id,
        created_by=usuario.id,
        is_active=1,
    )

    try:

        db.add(
            folder
        )

        db.commit()

        db.refresh(
            folder
        )

        logger.info(
            "Pasta de bibliotecas criada",
            extra={
                "event": "library_folder_created",
                "user_id": usuario.id,
                "folder_id": folder.id,
                "parent_id": folder.parent_id,
                "status": "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Pasta criada com sucesso."
            ),
            "folder": serializar_library_folder(
                folder
            ),
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao criar pasta de bibliotecas",
            extra={
                "event": "library_folder_create_failed",
                "user_id": usuario.id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível criar a pasta."
            ),
        )


# ============================================================
# CATÁLOGO - ATUALIZAR / MOVER PASTA
# ============================================================

def atualizar_pasta_bibliotecas_service(
    folder_id: int,
    request: LibraryFolderUpdate,
    db: Session,
    usuario,
) -> dict:
    """
    Renomeia e/ou move uma LibraryFolder.

    Semântica importante:

        parent_id omitido
            mantém o pai atual.

        parent_id=None enviado explicitamente
            move a pasta para a raiz.

    Por isso usamos model_dump(exclude_unset=True).
    """

    folder = obter_library_folder_or_404(
        db,
        folder_id,
        somente_ativa=True,
    )

    dados = request.model_dump(
        exclude_unset=True
    )

    if not dados:

        raise HTTPException(
            status_code=400,
            detail=(
                "Nenhum campo foi informado para atualização."
            ),
        )

    novo_nome = folder.name
    novo_parent_id = folder.parent_id

    if "name" in dados:

        novo_nome = validar_nome_pasta(
            dados["name"]
        )

    if "parent_id" in dados:

        novo_parent_id = dados[
            "parent_id"
        ]

        # Além de validar o destino, informa qual pasta está sendo
        # movida para impedir self-reference e descendentes.
        validar_destino_pasta(
            db,
            novo_parent_id,
            folder_id_movida=folder.id,
        )

    validar_nome_pasta_unico(
        db,
        novo_nome,
        novo_parent_id,
        ignorar_folder_id=folder.id,
    )

    folder.name = novo_nome
    folder.parent_id = novo_parent_id

    try:

        db.commit()

        db.refresh(
            folder
        )

        logger.info(
            "Pasta de bibliotecas atualizada",
            extra={
                "event": "library_folder_updated",
                "user_id": usuario.id,
                "folder_id": folder.id,
                "parent_id": folder.parent_id,
                "status": "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Pasta atualizada com sucesso."
            ),
            "folder": serializar_library_folder(
                folder
            ),
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao atualizar pasta de bibliotecas",
            extra={
                "event": "library_folder_update_failed",
                "user_id": usuario.id,
                "folder_id": folder_id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível atualizar a pasta."
            ),
        )


# ============================================================
# CATÁLOGO - EXCLUIR PASTA VAZIA
# ============================================================

def excluir_pasta_bibliotecas_service(
    folder_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Desativa logicamente uma LibraryFolder.

    A pasta somente pode ser desativada quando estiver vazia.

    A operação é bloqueada quando existe:

    - subpasta ativa;
    - Library ativa.

    Nenhum conteúdo é movimentado silenciosamente.
    """

    folder = obter_library_folder_or_404(
        db,
        folder_id,
    )

    # Operação idempotente:
    # excluir novamente uma pasta já inativa continua retornando
    # sucesso, sem criar nova alteração no banco.
    if not folder.is_active:

        return {
            "status": "success",
            "message": (
                "A pasta já está desativada."
            ),
            "already_inactive": True,
            "folder": serializar_library_folder(
                folder
            ),
        }

    subfolder = (
        db.query(LibraryFolder)
        .filter(
            LibraryFolder.parent_id
            == folder.id,
            LibraryFolder.is_active == 1,
        )
        .first()
    )

    if subfolder:

        raise HTTPException(
            status_code=409,
            detail=(
                "A pasta possui subpastas ativas. "
                "Mova ou exclua as subpastas antes."
            ),
        )

    library = (
        db.query(Library)
        .filter(
            Library.folder_id
            == folder.id,
            Library.is_active == 1,
        )
        .first()
    )

    if library:

        raise HTTPException(
            status_code=409,
            detail=(
                "A pasta possui bibliotecas ativas. "
                "Mova as bibliotecas antes de excluir a pasta."
            ),
        )

    # Exclusão lógica.
    folder.is_active = 0

    try:

        db.commit()

        db.refresh(
            folder
        )

        logger.info(
            "Pasta de bibliotecas desativada",
            extra={
                "event": "library_folder_deactivated",
                "user_id": usuario.id,
                "folder_id": folder.id,
                "status": "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Pasta excluída com sucesso."
            ),
            "already_inactive": False,
            "folder": serializar_library_folder(
                folder
            ),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao excluir pasta de bibliotecas",
            extra={
                "event": "library_folder_deactivate_failed",
                "user_id": usuario.id,
                "folder_id": folder_id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível excluir a pasta."
            ),
        )


# ============================================================
# CATÁLOGO - MOVER LIBRARY
# ============================================================

def mover_biblioteca_service(
    library_id: int,
    request: LibraryMoveRequest,
    db: Session,
    usuario,
) -> dict:
    """
    Move uma Library para outra LibraryFolder ou para a raiz.

    Essa operação altera somente a organização visual do catálogo.

    NÃO altera:

    - LibraryVersions;
    - dependências de projetos;
    - artefatos físicos;
    - versão vigente em Produção.
    """

    library = obter_library_or_404(
        db,
        library_id,
    )

    validar_destino_pasta(
        db,
        request.folder_id,
    )

    # Se a Library já estiver exatamente no destino solicitado,
    # preservamos a resposta idempotente existente.
    if library.folder_id == request.folder_id:

        return {
            "status": "success",
            "message": (
                "A biblioteca já está neste local."
            ),
            "already_in_folder": True,
            "library": serializar_library(
                library
            ),
        }

    library.folder_id = (
        request.folder_id
    )

    try:

        db.commit()

        db.refresh(
            library
        )

        logger.info(
            "Biblioteca movida no catálogo",
            extra={
                "event": "library_moved",
                "user_id": usuario.id,
                "library_id": library.id,
                "folder_id": library.folder_id,
                "status": "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Biblioteca movida com sucesso."
            ),
            "already_in_folder": False,
            "library": serializar_library(
                library
            ),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao mover biblioteca",
            extra={
                "event": "library_move_failed",
                "user_id": usuario.id,
                "library_id": library_id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível mover a biblioteca."
            ),
        )