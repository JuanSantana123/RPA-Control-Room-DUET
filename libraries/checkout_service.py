# ============================================================
# DUET CORE - LIBRARY CHECKOUT SERVICE
# ============================================================
#
# Responsabilidade:
# - controlar o Checkout global de uma Library;
# - impedir que a mesma Library seja editada simultaneamente em
#   dois AutomationProjects diferentes;
# - validar o Checkout da Library nas operações de Workspace;
# - registrar histórico de Checkout/Check-in.
#
# REGRAS:
# - o Checkout da Library é independente do Checkout do projeto;
# - adquirir o Checkout da Library exige Checkout do projeto;
# - a propriedade do lock é composta por library_id + project_id
#   + user_id;
# - Check-in NÃO publica a Library e NÃO cria LibraryVersion;
# - caminhos fora de _libraries/ não são afetados.
# ============================================================

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    Library,
    LibraryCheckout,
    LibraryCheckoutHistory,
    ProjectLibraryDraft,
    User,
)

from development.checkout_service import (
    exigir_checkout_workspace,
)


# ============================================================
# RESOLUÇÃO DA LIBRARY NO CONTEXTO DO PROJETO
# ============================================================

def _obter_draft_biblioteca(
    *,
    db: Session,
    project_id: int,
    library_id: int,
) -> tuple[ProjectLibraryDraft, Library]:
    """
    Valida que a Library realmente pertence ao Workspace do projeto.

    Não filtra Library.is_active porque uma Library criada dentro do
    Development nasce com is_active=0 até sua primeira publicação, mas
    já possui ProjectLibraryDraft e precisa participar do Checkout.
    """

    registro = (
        db.query(ProjectLibraryDraft, Library)
        .join(
            Library,
            Library.id == ProjectLibraryDraft.library_id,
        )
        .filter(
            ProjectLibraryDraft.project_id == project_id,
            ProjectLibraryDraft.library_id == library_id,
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail=(
                "A biblioteca não está disponível como Working Copy "
                "neste projeto."
            ),
        )

    return registro


def _obter_library_por_namespace(
    *,
    db: Session,
    project_id: int,
    import_name: str,
) -> Optional[Library]:
    """
    Resolve o namespace _libraries/<import_name> para a Library real.

    O vínculo confiável é ProjectLibraryDraft(project_id, library_id).
    Isso cobre tanto Libraries publicadas quanto Libraries novas do projeto.
    """

    registro = (
        db.query(Library)
        .join(
            ProjectLibraryDraft,
            ProjectLibraryDraft.library_id == Library.id,
        )
        .filter(
            ProjectLibraryDraft.project_id == project_id,
            Library.import_name == import_name,
        )
        .first()
    )

    return registro


def _extrair_namespace_library(path: str) -> Optional[str]:
    """Retorna o namespace quando o path pertence a _libraries/."""

    normalizado = (
        str(path or "")
        .replace("\\", "/")
        .strip("/")
    )

    if not normalizado.startswith("_libraries/"):
        return None

    partes = normalizado.split("/")

    if len(partes) < 2 or not partes[1]:
        return None

    return partes[1]


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def _serializar_checkout(
    *,
    checkout: LibraryCheckout,
    user_name: Optional[str],
) -> dict:
    return {
        "id": checkout.id,
        "library_id": checkout.library_id,
        "project_id": checkout.project_id,
        "user_id": checkout.user_id,
        "user_name": user_name,
        "checked_out_at": (
            checkout.checked_out_at.isoformat()
            if checkout.checked_out_at
            else None
        ),
        "updated_at": (
            checkout.updated_at.isoformat()
            if checkout.updated_at
            else None
        ),
    }


def _serializar_estado(
    *,
    library: Library,
    checkout: Optional[LibraryCheckout],
    checkout_user_name: Optional[str],
    project_id: int,
    user_id: int,
) -> dict:
    owns_checkout = bool(
        checkout
        and checkout.project_id == project_id
        and checkout.user_id == user_id
    )

    return {
        "library_id": library.id,
        "library_name": library.name,
        "import_name": library.import_name,
        "checked_out": checkout is not None,
        "owns_checkout": owns_checkout,
        "checkout": (
            _serializar_checkout(
                checkout=checkout,
                user_name=checkout_user_name,
            )
            if checkout
            else None
        ),
    }


# ============================================================
# OVERVIEW DO PROJETO
# ============================================================

def consultar_checkout_bibliotecas_projeto_service(
    *,
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Retorna, em uma chamada, o lock global de todas as Libraries do projeto.

    Inclui também Libraries novas ainda não publicadas (is_active=0), pois
    elas já são Working Copies válidas quando possuem ProjectLibraryDraft.
    """

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id == project_id,
            AutomationProject.is_active == 1,
        )
        .first()
    )

    if not projeto:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    registros = (
        db.query(ProjectLibraryDraft, Library)
        .join(
            Library,
            Library.id == ProjectLibraryDraft.library_id,
        )
        .filter(
            ProjectLibraryDraft.project_id == project_id,
        )
        .order_by(Library.name.asc())
        .all()
    )

    library_ids = [library.id for _, library in registros]

    checkouts_por_library: dict[int, LibraryCheckout] = {}
    usuarios_por_id: dict[int, str] = {}

    if library_ids:
        checkouts = (
            db.query(LibraryCheckout)
            .filter(
                LibraryCheckout.library_id.in_(library_ids)
            )
            .all()
        )

        checkouts_por_library = {
            checkout.library_id: checkout
            for checkout in checkouts
        }

        user_ids = {
            checkout.user_id
            for checkout in checkouts
        }

        if user_ids:
            usuarios_por_id = {
                user.id: user.name
                for user in (
                    db.query(User)
                    .filter(User.id.in_(user_ids))
                    .all()
                )
            }

    return {
        "status": "success",
        "project_id": project_id,
        "libraries": [
            _serializar_estado(
                library=library,
                checkout=checkouts_por_library.get(library.id),
                checkout_user_name=(
                    usuarios_por_id.get(
                        checkouts_por_library[library.id].user_id
                    )
                    if library.id in checkouts_por_library
                    else None
                ),
                project_id=project_id,
                user_id=usuario.id,
            )
            for _, library in registros
        ],
    }


# ============================================================
# CHECKOUT
# ============================================================

def realizar_checkout_biblioteca_service(
    *,
    project_id: int,
    library_id: int,
    db: Session,
    usuario,
) -> dict:
    """Adquire lock global da Library para este projeto e usuário."""

    # Para editar uma Library dentro do Studio, o usuário também
    # precisa possuir o Checkout do AutomationProject aberto.
    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    _, library = _obter_draft_biblioteca(
        db=db,
        project_id=project_id,
        library_id=library_id,
    )

    # Serializa concorrência usando a própria linha estável da Library.
    # Mesmo quando ainda não existe LibraryCheckout, duas transações
    # concorrentes disputam este mesmo row lock antes de criar o lock.
    library_locked = (
        db.query(Library)
        .filter(
            Library.id == library_id,
        )
        .with_for_update()
        .first()
    )

    if not library_locked:
        raise HTTPException(
            status_code=404,
            detail="Biblioteca não encontrada.",
        )

    checkout_atual = (
        db.query(LibraryCheckout)
        .filter(
            LibraryCheckout.library_id == library_id
        )
        .first()
    )

    if checkout_atual:
        owner = (
            db.query(User)
            .filter(User.id == checkout_atual.user_id)
            .first()
        )

        if (
            checkout_atual.project_id == project_id
            and checkout_atual.user_id == usuario.id
        ):
            return {
                "status": "success",
                "already_owned": True,
                "state": _serializar_estado(
                    library=library,
                    checkout=checkout_atual,
                    checkout_user_name=(owner.name if owner else None),
                    project_id=project_id,
                    user_id=usuario.id,
                ),
            }

        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "Esta biblioteca já está em edição em outro "
                    "contexto de desenvolvimento."
                ),
                "library_id": library_id,
                "checkout_user_id": checkout_atual.user_id,
                "checkout_user_name": owner.name if owner else None,
                "checkout_project_id": checkout_atual.project_id,
            },
        )

    checkout = LibraryCheckout(
        library_id=library_id,
        project_id=project_id,
        user_id=usuario.id,
        checked_out_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    history = LibraryCheckoutHistory(
        library_id=library_id,
        project_id=project_id,
        user_id=usuario.id,
        action="checkout",
        created_at=datetime.utcnow(),
    )

    try:
        db.add(checkout)
        db.add(history)
        db.commit()
        db.refresh(checkout)
    except Exception:
        db.rollback()
        raise

    return {
        "status": "success",
        "already_owned": False,
        "state": _serializar_estado(
            library=library,
            checkout=checkout,
            checkout_user_name=usuario.name,
            project_id=project_id,
            user_id=usuario.id,
        ),
    }


# ============================================================
# CHECK-IN
# ============================================================

def realizar_checkin_biblioteca_service(
    *,
    project_id: int,
    library_id: int,
    db: Session,
    usuario,
) -> dict:
    """Libera somente o lock; não publica e não cria LibraryVersion."""

    _, library = _obter_draft_biblioteca(
        db=db,
        project_id=project_id,
        library_id=library_id,
    )

    # Mesmo lock de serialização usado no Checkout.
    (
        db.query(Library)
        .filter(Library.id == library_id)
        .with_for_update()
        .first()
    )

    checkout = (
        db.query(LibraryCheckout)
        .filter(
            LibraryCheckout.library_id == library_id
        )
        .first()
    )

    if not checkout:
        raise HTTPException(
            status_code=409,
            detail="A biblioteca não possui Checkout ativo.",
        )

    if (
        checkout.project_id != project_id
        or checkout.user_id != usuario.id
    ):
        owner = (
            db.query(User)
            .filter(User.id == checkout.user_id)
            .first()
        )

        raise HTTPException(
            status_code=423,
            detail={
                "message": "O Checkout da biblioteca pertence a outro contexto.",
                "checkout_user_id": checkout.user_id,
                "checkout_user_name": owner.name if owner else None,
                "checkout_project_id": checkout.project_id,
            },
        )

    history = LibraryCheckoutHistory(
        library_id=library_id,
        project_id=project_id,
        user_id=usuario.id,
        action="checkin",
        created_at=datetime.utcnow(),
    )

    try:
        db.add(history)
        db.delete(checkout)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "status": "success",
        "message": "Check-in da biblioteca realizado com sucesso.",
        "state": _serializar_estado(
            library=library,
            checkout=None,
            checkout_user_name=None,
            project_id=project_id,
            user_id=usuario.id,
        ),
    }


# ============================================================
# HISTÓRICO
# ============================================================

def consultar_historico_checkout_biblioteca_service(
    *,
    project_id: int,
    library_id: int,
    db: Session,
) -> dict:
    """Lista auditoria de Checkout/Check-in da Library."""

    _, library = _obter_draft_biblioteca(
        db=db,
        project_id=project_id,
        library_id=library_id,
    )

    eventos = (
        db.query(LibraryCheckoutHistory, User)
        .outerjoin(
            User,
            User.id == LibraryCheckoutHistory.user_id,
        )
        .filter(
            LibraryCheckoutHistory.library_id == library_id
        )
        .order_by(
            LibraryCheckoutHistory.created_at.desc(),
            LibraryCheckoutHistory.id.desc(),
        )
        .limit(200)
        .all()
    )

    return {
        "status": "success",
        "library_id": library.id,
        "library_name": library.name,
        "events": [
            {
                "id": event.id,
                "library_id": event.library_id,
                "project_id": event.project_id,
                "user_id": event.user_id,
                "user_name": user.name if user else None,
                "action": event.action,
                "created_at": (
                    event.created_at.isoformat()
                    if event.created_at
                    else None
                ),
            }
            for event, user in eventos
        ],
    }


# ============================================================
# GUARDA DE WORKSPACE
# ============================================================

def exigir_checkout_biblioteca(
    *,
    db: Session,
    project_id: int,
    library_id: int,
    user_id: int,
) -> LibraryCheckout:
    """Exige que o lock global pertença ao usuário NESTE projeto."""

    checkout = (
        db.query(LibraryCheckout)
        .filter(
            LibraryCheckout.library_id == library_id
        )
        .first()
    )

    if not checkout:
        raise HTTPException(
            status_code=423,
            detail=(
                "A biblioteca está em modo somente leitura. "
                "Faça Checkout da biblioteca antes de editar."
            ),
        )

    if (
        checkout.project_id != project_id
        or checkout.user_id != user_id
    ):
        owner = (
            db.query(User)
            .filter(User.id == checkout.user_id)
            .first()
        )

        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "A biblioteca está em edição por outro usuário "
                    "ou em outro projeto."
                ),
                "checkout_user_id": checkout.user_id,
                "checkout_user_name": owner.name if owner else None,
                "checkout_project_id": checkout.project_id,
            },
        )

    return checkout


def exigir_checkout_biblioteca_para_caminho(
    *,
    db: Session,
    project_id: int,
    user_id: int,
    path: str,
) -> Optional[LibraryCheckout]:
    """
    Aplica o segundo lock somente quando a operação toca uma Library.

    Arquivos normais do AutomationProject continuam protegidos apenas
    pelo Checkout do projeto, preservando o comportamento atual.
    """

    normalized = (
        str(path or "")
        .replace("\\", "/")
        .strip("/")
    )

    # _libraries é um container técnico controlado pelos services de
    # dependência. Ele não pode ser renomeado/excluído pelas APIs
    # genéricas do Workspace.
    if normalized == "_libraries":
        raise HTTPException(
            status_code=409,
            detail=(
                "A pasta _libraries é gerenciada pelo DUET e não "
                "pode ser alterada diretamente."
            ),
        )

    namespace = _extrair_namespace_library(path)

    if namespace is None:
        return None

    library = _obter_library_por_namespace(
        db=db,
        project_id=project_id,
        import_name=namespace,
    )

    if not library:
        raise HTTPException(
            status_code=409,
            detail=(
                "O namespace de biblioteca informado não pertence "
                "ao projeto atual."
            ),
        )

    return exigir_checkout_biblioteca(
        db=db,
        project_id=project_id,
        library_id=library.id,
        user_id=user_id,
    )


def possui_checkout_biblioteca_ativo_no_projeto(
    *,
    db: Session,
    project_id: int,
    user_id: int,
) -> bool:
    """Usado para impedir Check-in do projeto com Library ainda travada."""

    return (
        db.query(LibraryCheckout.id)
        .filter(
            LibraryCheckout.project_id == project_id,
            LibraryCheckout.user_id == user_id,
        )
        .first()
        is not None
    )

# ============================================================
# GUARDA PARA TERMINAL INTEGRADO
# ============================================================

def exigir_checkouts_bibliotecas_para_terminal(
    *,
    db: Session,
    project_id: int,
    user_id: int,
) -> None:
    """
    O terminal é um shell irrestrito sobre o Workspace oficial.

    Para não permitir que ele contorne os locks individuais, quando
    o projeto possui Libraries todas elas precisam estar em Checkout
    pelo mesmo usuário e neste mesmo projeto antes de abrir o shell.
    Projetos sem Libraries mantêm o comportamento anterior.
    """

    registros = (
        db.query(ProjectLibraryDraft, Library)
        .join(
            Library,
            Library.id == ProjectLibraryDraft.library_id,
        )
        .filter(
            ProjectLibraryDraft.project_id == project_id,
        )
        .order_by(Library.name.asc())
        .all()
    )

    if not registros:
        return

    library_ids = [
        library.id
        for _, library in registros
    ]

    checkouts = (
        db.query(LibraryCheckout)
        .filter(
            LibraryCheckout.library_id.in_(library_ids)
        )
        .all()
    )

    owned_ids = {
        checkout.library_id
        for checkout in checkouts
        if (
            checkout.project_id == project_id
            and checkout.user_id == user_id
        )
    }

    pendentes = [
        {
            "library_id": library.id,
            "library_name": library.name,
            "import_name": library.import_name,
        }
        for _, library in registros
        if library.id not in owned_ids
    ]

    if pendentes:
        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "O Terminal só pode ser aberto quando todas as "
                    "bibliotecas do projeto estiverem em Checkout por você."
                ),
                "libraries_without_checkout": pendentes,
            },
        )


# ============================================================
# GUARDA PARA TROCA/REMOÇÃO DE DEPENDÊNCIA
# ============================================================

def exigir_biblioteca_sem_checkout_neste_projeto(
    *,
    db: Session,
    project_id: int,
    library_id: int,
) -> None:
    """
    Impede remover/trocar a Working Copy que sustenta um lock ativo.

    Checkout da mesma Library em OUTRO projeto não impede este projeto
    de remover sua própria dependência, pois a outra Working Copy é
    independente.
    """

    checkout = (
        db.query(LibraryCheckout)
        .filter(
            LibraryCheckout.library_id == library_id,
            LibraryCheckout.project_id == project_id,
        )
        .first()
    )

    if not checkout:
        return

    owner = (
        db.query(User)
        .filter(User.id == checkout.user_id)
        .first()
    )

    raise HTTPException(
        status_code=409,
        detail={
            "message": (
                "Faça Check-in da biblioteca antes de alterar "
                "ou remover sua dependência deste projeto."
            ),
            "checkout_user_id": checkout.user_id,
            "checkout_user_name": owner.name if owner else None,
            "checkout_project_id": checkout.project_id,
        },
    )
