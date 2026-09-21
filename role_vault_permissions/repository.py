# ============================================================
# ROLE VAULT PERMISSIONS - REPOSITORY
# ============================================================
#
# Responsável exclusivamente pelas consultas relacionadas às
# permissões do Vault e aos vínculos RolePermission.
#
# Este módulo:
#
# - busca uma Role;
# - busca uma Permission do recurso Vault;
# - busca um vínculo RolePermission existente.
#
# NÃO registra endpoints FastAPI.
# NÃO realiza commit.
# NÃO decide quais permissões devem ser adicionadas/removidas.
#
# Essas decisões pertencem ao service.
# ============================================================

from sqlalchemy.orm import Session

from models import (
    Role,
    RolePermission,
    Permission,
)


# ============================================================
# BUSCAR ROLE
# ============================================================

def buscar_role(
    db: Session,
    role_id: int,
):
    """
    Busca uma Role pelo identificador.

    Parâmetros
    ----------
    db:
        Sessão SQLAlchemy utilizada pela operação.

    role_id:
        Identificador da Role.

    Retorno
    -------
    Role | None
        Role encontrada ou None.
    """

    return (
        db.query(Role)
        .filter(
            Role.id == role_id
        )
        .first()
    )


# ============================================================
# BUSCAR PERMISSÃO DO VAULT
# ============================================================

def buscar_permissao_vault(
    db: Session,
    action: str,
):
    """
    Busca no catálogo RBAC uma permissão do recurso Vault.

    Exemplo:

        action="view"

    corresponde a:

        Permission(
            resource="Vault",
            action="view"
        )
    """

    return (
        db.query(Permission)
        .filter(
            Permission.resource == "Vault",
            Permission.action == action,
        )
        .first()
    )


# ============================================================
# BUSCAR VÍNCULO ROLE ↔ PERMISSION
# ============================================================

def buscar_role_permission(
    db: Session,
    role_id: int,
    permission_id: int,
):
    """
    Verifica se uma determinada Permission já está vinculada
    à Role informada.

    Retorna o objeto RolePermission quando o relacionamento
    existir; caso contrário, retorna None.
    """

    return (
        db.query(RolePermission)
        .filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        .first()
    )