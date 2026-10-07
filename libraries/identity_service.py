# ============================================================
# LIBRARIES - IDENTITY SERVICE
# ============================================================
#
# Centraliza as regras de identidade global de uma Library.
#
# REGRAS:
#
# - name é único globalmente, ignorando maiúsculas/minúsculas;
# - import_name é único globalmente;
# - Library desativada continua reservando name/import_name;
# - Library ainda não publicada no Development também reserva
#   sua identidade;
# - somente hard delete de uma Library nunca publicada libera
#   novamente esses identificadores.
#
# Este módulo NÃO realiza commit.
# ============================================================

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import (
    Library,
    LibraryVersion,
    ProjectLibraryDraft,
)


# ============================================================
# CLASSIFICAR ESTADO DA IDENTIDADE
# ============================================================

def obter_estado_identidade_library(
    db: Session,
    library: Library,
) -> str:
    """
    Retorna o estado lógico da identidade.

    Valores:

        active
            Library ativa.

        archived
            Library inativa, mas já possui histórico publicado.

        reserved
            Library inativa e ainda nunca publicada.
            Normalmente pertence a um fluxo em Development.
    """

    if library.is_active:
        return "active"

    possui_versao = (
        db.query(LibraryVersion.id)
        .filter(
            LibraryVersion.library_id
            == library.id
        )
        .first()
        is not None
    )

    # Se já houve publicação, uma Library inativa é arquivada.
    if (
        library.production_version_id is not None
        or possui_versao
    ):
        return "archived"

    # ========================================================
    # IDENTIDADE RESERVADA PELO DEVELOPMENT
    # ========================================================
    #
    # Uma Library inativa e sem versão não é necessariamente
    # uma identidade reservada.
    #
    # Só consideramos "reserved" quando existe efetivamente uma
    # Working Copy / ProjectLibraryDraft em Development.
    # ========================================================

    possui_draft_development = (
        db.query(ProjectLibraryDraft.id)
        .filter(
            ProjectLibraryDraft.library_id
            == library.id
        )
        .first()
        is not None
    )

    if possui_draft_development:
        return "reserved"

    # Library criada no catálogo global, nunca publicada e depois
    # desativada. Ela continua sendo uma identidade arquivada.
    return "archived"


# ============================================================
# BUSCAR CONFLITO POR NOME
# ============================================================

def buscar_library_por_nome(
    db: Session,
    nome: str,
    ignorar_library_id: int | None = None,
) -> Library | None:
    """
    Busca Library pelo nome amigável ignorando caixa.
    """

    query = (
        db.query(Library)
        .filter(
            func.lower(Library.name)
            == nome.strip().lower()
        )
    )

    if ignorar_library_id is not None:
        query = query.filter(
            Library.id != ignorar_library_id
        )

    return query.first()


# ============================================================
# BUSCAR CONFLITO POR IMPORT_NAME
# ============================================================

def buscar_library_por_import_name(
    db: Session,
    import_name: str,
    ignorar_library_id: int | None = None,
) -> Library | None:
    """
    Busca Library pelo namespace Python ignorando caixa.
    """

    query = (
        db.query(Library)
        .filter(
            func.lower(Library.import_name)
            == import_name.strip().lower()
        )
    )

    if ignorar_library_id is not None:
        query = query.filter(
            Library.id != ignorar_library_id
        )

    return query.first()


# ============================================================
# MENSAGEM DE CONFLITO
# ============================================================

def _criar_erro_identidade(
    *,
    campo: str,
    valor: str,
    library: Library,
    estado: str,
) -> HTTPException:
    """
    Monta mensagem consistente para conflito de identidade.
    """

    if estado == "archived":
        mensagem = (
            f'Já existe uma biblioteca desativada utilizando '
            f'{campo} "{valor}". '
            f'Reative a biblioteca "{library.name}" para continuar '
            f'utilizando esta identidade.'
        )

    elif estado == "reserved":
        mensagem = (
            f'Já existe uma biblioteca utilizando '
            f'{campo} "{valor}" em um projeto de Desenvolvimento. '
            f'Utilize a biblioteca existente em vez de criar outra.'
        )

    else:
        mensagem = (
            f'Já existe uma biblioteca utilizando '
            f'{campo} "{valor}".'
        )

    return HTTPException(
        status_code=409,
        detail={
            "code": "LIBRARY_IDENTITY_CONFLICT",
            "field": campo,
            "value": valor,
            "library_id": library.id,
            "library_name": library.name,
            "library_state": estado,
            "message": mensagem,
        },
    )


# ============================================================
# VALIDAR IDENTIDADE COMPLETA
# ============================================================

def validar_identidade_library_unica(
    *,
    db: Session,
    nome: str,
    import_name: str | None = None,
    ignorar_library_id: int | None = None,
) -> None:
    """
    Garante unicidade global do name e, quando informado,
    também do import_name.
    """

    nome_normalizado = nome.strip()

    conflito_nome = buscar_library_por_nome(
        db=db,
        nome=nome_normalizado,
        ignorar_library_id=ignorar_library_id,
    )

    if conflito_nome is not None:
        estado = obter_estado_identidade_library(
            db,
            conflito_nome,
        )

        raise _criar_erro_identidade(
            campo="name",
            valor=nome_normalizado,
            library=conflito_nome,
            estado=estado,
        )

    if import_name is None:
        return

    import_name_normalizado = import_name.strip()

    conflito_import = buscar_library_por_import_name(
        db=db,
        import_name=import_name_normalizado,
        ignorar_library_id=ignorar_library_id,
    )

    if conflito_import is not None:
        estado = obter_estado_identidade_library(
            db,
            conflito_import,
        )

        raise _criar_erro_identidade(
            campo="import_name",
            valor=import_name_normalizado,
            library=conflito_import,
            estado=estado,
        )