# ============================================================
# USUÁRIO ↔ ROLE API
# ============================================================
#
# Responsabilidade:
#
#     Expor a camada HTTP do domínio User Roles.
#
# As regras de negócio permanecem em:
#
#     user_roles/service.py
#
# As consultas e operações de persistência permanecem em:
#
#     user_roles/repository.py
#
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from database import SessionLocal

from auth.permissions import require_permission

from user_roles.service import (
    associar_role_usuario_service,
    listar_roles_usuario_service,
    remover_role_usuario_service,
)


# ============================================================
# DEPENDÊNCIA DO BANCO
# ============================================================

def get_db():
    """
    Abre uma sessão SQLAlchemy para a requisição e garante
    seu fechamento ao término do processamento.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"],
)


# ============================================================
# LISTAR ROLES DE UM USUÁRIO
# ============================================================

@router.get(
    "/users/{user_id}",
    summary="Listar Roles do Usuário",
    description=(
        "Retorna todas as Roles associadas a um usuário. "
        "É necessário informar o ID do usuário. "
        "Requer autenticação do usuário e a permissão "
        "'Users:view'."
    ),
)
def listar_roles_usuario(
    user_id: int,
    db: Session = Depends(get_db),

    # A consulta de Roles de usuários exige Users:view.
    usuario=Depends(
        require_permission(
            "Users",
            "view",
        )
    ),
):
    """
    Lista todas as Roles associadas a um usuário.

    Permissão necessária:

        Users:view
    """

    return listar_roles_usuario_service(
        user_id=user_id,
        db=db,
    )


# ============================================================
# ASSOCIAR ROLE AO USUÁRIO
# ============================================================

@router.post(
    "/users/{user_id}/roles/{role_id}",
    summary="Associar Role ao Usuário",
    description=(
        "Associa uma Role a um usuário. "
        "É necessário informar o ID do usuário e o ID da Role "
        "que será associada. "
        "Requer autenticação do usuário e a permissão "
        "'Users:edit'."
    ),
)
def associar_role_usuario(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),

    # Alterar as Roles de um usuário é uma operação
    # administrativa e exige Users:edit.
    usuario=Depends(
        require_permission(
            "Users",
            "edit",
        )
    ),
):
    """
    Associa uma Role a um usuário.

    Permissão necessária:

        Users:edit
    """

    return associar_role_usuario_service(
        user_id=user_id,
        role_id=role_id,
        db=db,

        # Usuário autenticado responsável pela concessão.
        # O service utiliza essa identidade para impedir
        # escalada de privilégios.
        usuario_executor=usuario,
    )


# ============================================================
# REMOVER ROLE DO USUÁRIO
# ============================================================

@router.delete(
    "/users/{user_id}/roles/{role_id}",
    summary="Remover Role do Usuário",
    description=(
        "Remove uma Role de um usuário. "
        "É necessário informar o ID do usuário e o ID da Role "
        "que será removida. "
        "Requer autenticação do usuário e a permissão "
        "'Users:edit'."
    ),
)
def remover_role_usuario(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),

    # Remover uma Role também altera a autorização efetiva
    # do usuário e exige Users:edit.
    usuario=Depends(
        require_permission(
            "Users",
            "edit",
        )
    ),
):
    """
    Remove uma Role de um usuário.

    Permissão necessária:

        Users:edit
    """

    return remover_role_usuario_service(
        user_id=user_id,
        role_id=role_id,
        db=db,
    )