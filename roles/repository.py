# ============================================================
# REPOSITORY - ROLES
# ============================================================
#
# Responsabilidade:
#
#     Centralizar acesso aos modelos Role, Permission,
#     RolePermission e UserRole.
#
# Este módulo NÃO executa commit.
#
# O limite transacional pertence ao service.
# ============================================================

from sqlalchemy.orm import Session

from models import (
    Permission,
    Role,
    RolePermission,
    UserRole,
)


# ============================================================
# ROLE
# ============================================================

def buscar_role_por_id(
    db: Session,
    role_id: int,
) -> Role | None:
    """
    Busca uma Role pelo identificador interno.
    """

    return (
        db.query(Role)
        .filter(
            Role.id == role_id
        )
        .first()
    )


def buscar_role_por_nome(
    db: Session,
    nome: str,
) -> Role | None:
    """
    Busca uma Role pelo nome exato.
    """

    return (
        db.query(Role)
        .filter(
            Role.name == nome
        )
        .first()
    )


def listar_roles(
    db: Session,
) -> list[Role]:
    """
    Lista todas as Roles ordenadas pelo nome.
    """

    return (
        db.query(Role)
        .order_by(
            Role.name
        )
        .all()
    )


def criar_role(
    db: Session,
    nome: str,
    descricao: str | None,
) -> Role:
    """
    Cria uma Role em memória e adiciona à sessão SQLAlchemy.

    Não executa commit.
    """

    role = Role(
        name=nome,
        description=descricao,
    )

    db.add(role)

    return role


def excluir_role(
    db: Session,
    role: Role,
) -> None:
    """
    Marca a Role para exclusão.

    Não executa commit.
    """

    db.delete(role)


# ============================================================
# PERMISSIONS
# ============================================================

def buscar_permissao_por_id(
    db: Session,
    permission_id: int,
) -> Permission | None:
    """
    Busca uma Permission pelo identificador.
    """

    return (
        db.query(Permission)
        .filter(
            Permission.id == permission_id
        )
        .first()
    )


def listar_permissoes(
    db: Session,
) -> list[Permission]:
    """
    Lista o catálogo completo de permissões.
    """

    return (
        db.query(Permission)
        .order_by(
            Permission.resource,
            Permission.id,
        )
        .all()
    )


def listar_permissoes_por_ids(
    db: Session,
    permission_ids: list[int],
) -> list[Permission]:
    """
    Busca todas as Permissions pertencentes aos IDs informados.
    """

    if not permission_ids:
        return []

    return (
        db.query(Permission)
        .filter(
            Permission.id.in_(permission_ids)
        )
        .all()
    )


def listar_permissoes_role(
    db: Session,
    role_id: int,
) -> list[Permission]:
    """
    Lista as Permissions atualmente associadas à Role.
    """

    return (
        db.query(Permission)
        .join(
            RolePermission,
            RolePermission.permission_id
            == Permission.id,
        )
        .filter(
            RolePermission.role_id == role_id
        )
        .order_by(
            Permission.resource,
            Permission.id,
        )
        .all()
    )


# ============================================================
# ROLE PERMISSION
# ============================================================

def buscar_role_permission(
    db: Session,
    role_id: int,
    permission_id: int,
) -> RolePermission | None:
    """
    Busca uma associação específica Role ↔ Permission.
    """

    return (
        db.query(RolePermission)
        .filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        .first()
    )


def criar_role_permission(
    db: Session,
    role_id: int,
    permission_id: int,
) -> RolePermission:
    """
    Cria uma associação RolePermission sem executar commit.
    """

    associacao = RolePermission(
        role_id=role_id,
        permission_id=permission_id,
    )

    db.add(associacao)

    return associacao


def remover_permissoes_role(
    db: Session,
    role_id: int,
) -> None:
    """
    Remove todas as associações Permission de uma Role.

    Não executa commit.
    """

    (
        db.query(RolePermission)
        .filter(
            RolePermission.role_id == role_id
        )
        .delete(
            synchronize_session=False
        )
    )


# ============================================================
# USER ROLE
# ============================================================

def remover_usuarios_role(
    db: Session,
    role_id: int,
) -> None:
    """
    Remove todas as associações UserRole pertencentes à Role.

    Os usuários permanecem cadastrados.
    """

    (
        db.query(UserRole)
        .filter(
            UserRole.role_id == role_id
        )
        .delete(
            synchronize_session=False
        )
    )