# ============================================================
# SERVICE - ROLES DOS USUÁRIOS
# ============================================================
#
# Responsabilidade:
#     Consultar e atualizar as associações:
#
#         User -> UserRole -> Role
#
# Este módulo não registra endpoints e não decide RBAC.
# ============================================================

from sqlalchemy.orm import Session

from models import (
    User,
    UserRole,
    Role,
)

from schemas.auth import UserRolesUpdate

# ============================================================
# SEGURANÇA RBAC
# ============================================================
#
# A substituição completa das Roles também precisa respeitar
# a mesma regra de delegação utilizada pelo domínio User Roles.
# ============================================================

from auth.rbac_safety import (
    validar_delegacao_roles,
)
# ============================================================
# LISTAR ROLES DO USUÁRIO
# ============================================================

def listar_roles_usuario_service(
    user_id: int,
    db: Session,
):
    """
    Retorna todas as Roles associadas ao usuário informado.
    """

    usuario_alvo = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not usuario_alvo:
        return {
            "status": "error",
            "message": "Usuário não encontrado.",
        }

    user_roles = (
        db.query(UserRole)
        .filter(
            UserRole.user_id == user_id
        )
        .all()
    )

    roles = []

    for user_role in user_roles:

        role = (
            db.query(Role)
            .filter(
                Role.id == user_role.role_id
            )
            .first()
        )

        if role:
            roles.append(
                {
                    "id": role.id,
                    "name": role.name,
                }
            )

    return {
        "status": "success",
        "user": {
            "id": usuario_alvo.id,
            "username": usuario_alvo.username,
            "name": usuario_alvo.name,
        },
        "roles": roles,
    }


# ============================================================
