# ============================================================
# ROLES API
# ============================================================
#
# Responsabilidade:
#
#     Expor os endpoints HTTP do domínio Roles e aplicar
#     autenticação/autorização RBAC.
#
# Regras de negócio:
#
#     roles/service.py
#
# Persistência:
#
#     roles/repository.py
#
# Contratos:
#
#     schemas/roles.py
#
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from database import SessionLocal

from auth.permissions import require_permission

from schemas.roles import (
    RoleCreate,
    RolePermissionCreate,
    RolePermissionsUpdate,
)

from roles.service import (
    adicionar_permissao_role_service,
    atualizar_permissoes_role_service,
    criar_role_service,
    excluir_role_service,
    listar_permissoes_role_service,
    listar_permissoes_service,
    listar_roles_service,
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
    prefix="/roles",
    tags=["Roles"],
)


# ============================================================
# LISTAR PERMISSÕES
# ============================================================

@router.get(
    "/permissions",
    summary="Listar Permissões",
    description=(
        "Retorna o catálogo de permissões disponíveis no "
        "Control Room. "
        "As permissões são identificadas por ID e possuem "
        "um recurso e uma ação. "
        "Os IDs retornados podem ser utilizados para configurar "
        "as permissões de uma Role. "
        "Não é necessário informar parâmetros. "
        "Requer a permissão 'Roles:view'."
    ),
)
def listar_permissoes(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Roles",
            "view",
        )
    ),
):
    """
    Lista o catálogo de permissões.

    Permissão necessária:

        Roles:view
    """

    return listar_permissoes_service(
        db=db
    )


# ============================================================
# LISTAR ROLES
# ============================================================

@router.get(
    "",
    summary="Listar Roles",
    description=(
        "Retorna todas as Roles cadastradas no Control Room, "
        "incluindo nome, descrição e data de criação. "
        "Não é necessário informar parâmetros. "
        "Requer a permissão 'Roles:view'."
    ),
)
def listar_roles(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Roles",
            "view",
        )
    ),
):
    """
    Lista todas as Roles cadastradas.

    Permissão necessária:

        Roles:view
    """

    return listar_roles_service(
        db=db
    )


# ============================================================
# CRIAR ROLE
# ============================================================

@router.post(
    "",
    summary="Criar Role",
    description=(
        "Cria uma nova Role no Control Room. "
        "O nome da Role é obrigatório e deve ser único. "
        "A descrição é opcional. "
        "Requer a permissão 'Roles:create'."
    ),
)
def criar_role(
    dados: RoleCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Roles",
            "create",
        )
    ),
):
    """
    Cria uma nova Role.

    Permissão necessária:

        Roles:create
    """

    return criar_role_service(
        dados=dados,
        db=db,
    )


# ============================================================
# LISTAR PERMISSÕES DA ROLE
# ============================================================

@router.get(
    "/{role_id}/permissions",
    summary="Listar Permissões da Role",
    description=(
        "Retorna todas as permissões atualmente associadas "
        "a uma Role específica. "
        "É necessário informar o ID da Role. "
        "Requer a permissão 'Roles:view'."
    ),
)
def listar_permissoes_role(
    role_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Roles",
            "view",
        )
    ),
):
    """
    Lista as permissões associadas à Role.

    Permissão necessária:

        Roles:view
    """

    return listar_permissoes_role_service(
        role_id=role_id,
        db=db,
    )


# ============================================================
# ADICIONAR PERMISSÃO À ROLE
# ============================================================

@router.post(
    "/{role_id}/permissions",
    summary="Adicionar Permissão à Role",
    description=(
        "Associa uma permissão existente a uma Role. "
        "A Role e a permissão informada precisam existir. "
        "A mesma permissão não pode ser associada duas vezes "
        "à mesma Role. "
        "Requer a permissão 'Roles:edit'."
    ),
)
def adicionar_permissao_role(
    role_id: int,
    dados: RolePermissionCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Roles",
            "edit",
        )
    ),
):
    """
    Adiciona uma Permission à Role.

    Permissão necessária:

        Roles:edit
    """

    return adicionar_permissao_role_service(
        role_id=role_id,
        dados=dados,
        db=db,

        # Usuário autenticado responsável pela concessão.
        usuario_executor=usuario,
    )


# ============================================================
# ATUALIZAR PERMISSÕES DA ROLE
# ============================================================

@router.put(
    "/{role_id}/permissions",
    summary="Atualizar Permissões da Role",
    description=(
        "Substitui as permissões atuais de uma Role pela lista "
        "de permissões informada. "
        "As permissões atuais que não estiverem na nova lista "
        "serão removidas. "
        "IDs duplicados são tratados automaticamente. "
        "É necessário informar o ID da Role e a lista completa "
        "de permissões desejadas. "
        "Requer a permissão 'Roles:edit'."
    ),
)
def atualizar_permissoes_role(
    role_id: int,
    dados: RolePermissionsUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Roles",
            "edit",
        )
    ),
):
    """
    Substitui a configuração de permissões da Role.

    Permissão necessária:

        Roles:edit
    """

    return atualizar_permissoes_role_service(
        role_id=role_id,
        dados=dados,
        db=db,

        # Usuário autenticado responsável pela alteração.
        usuario_executor=usuario,
    )


# ============================================================
# EXCLUIR ROLE
# ============================================================

@router.delete(
    "/{role_id}",
    summary="Excluir Role",
    description=(
        "Exclui uma Role do Control Room. "
        "Antes da exclusão, são removidas as associações "
        "da Role com permissões e usuários. "
        "As permissões e os usuários continuam cadastrados "
        "normalmente no sistema. "
        "É necessário informar o ID da Role. "
        "Requer a permissão 'Roles:delete'."
    ),
)
def excluir_role(
    role_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Roles",
            "delete",
        )
    ),
):
    """
    Exclui uma Role.

    Permissão necessária:

        Roles:delete
    """

    return excluir_role_service(
        role_id=role_id,
        db=db,
    )