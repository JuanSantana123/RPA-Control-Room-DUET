# ============================================================
# AUTORIZAÇÃO POR PERMISSÕES
# ============================================================

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import (
    User,
    UserRole,
    RolePermission,
    Permission
)

# Autenticação utilizada pelo frontend, aceitando sessão/cookie.
from auth.dependencies import get_usuario_atual

# Autenticação exclusiva por Bearer para a API/Swagger.
from auth.dependencies import get_usuario_bearer


# ============================================================
# CONEXÃO COM O BANCO
# ============================================================

def get_db():
    """
    Abre uma sessão com o banco de dados.

    A sessão é encerrada automaticamente depois que
    a requisição termina.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# VERIFICAR PERMISSÃO DO USUÁRIO
# ============================================================

def usuario_tem_permissao(
    usuario: User,
    db: Session,
    resource: str,
    action: str
) -> bool:
    """
    Verifica se o usuário possui uma determinada permissão.

    Fluxo:

        User
          ↓
        UserRole
          ↓
        Role
          ↓
        RolePermission
          ↓
        Permission
          ↓
        resource + action
    """

    permissao = (
        db.query(Permission)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id
        )
        .join(
            UserRole,
            UserRole.role_id == RolePermission.role_id
        )
        .filter(
            UserRole.user_id == usuario.id,
            Permission.resource == resource,
            Permission.action == action
        )
        .first()
    )

    return permissao is not None


# ============================================================
# DEPENDÊNCIA DE AUTORIZAÇÃO
# ============================================================

def require_permission(
    resource: str,
    action: str
):
    """
    Cria uma dependência FastAPI que exige uma permissão.

    Exemplo:

        usuario=Depends(
            require_permission("Agents", "view")
        )

    Se o usuário não possuir a permissão,
    a API retorna HTTP 403.
    """

    def verificar_permissao(
        usuario: User = Depends(get_usuario_atual),
        db: Session = Depends(get_db)
    ):
        # ====================================================
        # Verifica se o usuário possui a permissão solicitada.
        # ====================================================

        permitido = usuario_tem_permissao(
            usuario=usuario,
            db=db,
            resource=resource,
            action=action
        )

        # ====================================================
        # Usuário autenticado, mas sem autorização.
        # ====================================================

        if not permitido:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Usuário não possui permissão "
                    f"'{resource}:{action}'."
                )
            )

        # ====================================================
        # Permissão concedida.
        #
        # Retornamos o usuário para que o endpoint possa
        # utilizá-lo normalmente, caso precise.
        # ====================================================

        return usuario

    return verificar_permissao



# ============================================================
# DEPENDÊNCIA DE AUTORIZAÇÃO PARA API / SWAGGER
# ============================================================

def require_permission_bearer(
    resource: str,
    action: str
):
    """
    Cria uma dependência FastAPI que exige:

        1. Access Token Bearer válido.
        2. Permissão RBAC solicitada.

    Esta versão é destinada às rotas da API utilizadas
    pelo Swagger e por clientes externos.

    Diferentemente de require_permission(), ela NÃO aceita
    session_id por cookie.

    Exemplo:

        usuario=Depends(
            require_permission_bearer("Agents", "view")
        )

    Se não houver Bearer válido:
        HTTP 401

    Se o usuário estiver autenticado, mas não possuir
    a permissão:
        HTTP 403
    """

    def verificar_permissao_bearer(
        usuario: User = Depends(get_usuario_bearer),
        db: Session = Depends(get_db)
    ):
        # ====================================================
        # Verifica se o usuário autenticado possui a
        # permissão RBAC solicitada.
        # ====================================================

        permitido = usuario_tem_permissao(
            usuario=usuario,
            db=db,
            resource=resource,
            action=action
        )

        # ====================================================
        # Usuário autenticado, mas sem autorização.
        # ====================================================

        if not permitido:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Usuário não possui permissão "
                    f"'{resource}:{action}'."
                )
            )

        # ====================================================
        # Permissão concedida.
        #
        # Retornamos o usuário para que o endpoint possa
        # utilizá-lo normalmente.
        # ====================================================

        return usuario

    return verificar_permissao_bearer