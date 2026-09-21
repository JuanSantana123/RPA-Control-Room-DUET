# ============================================================
# SEGURANÇA DE DELEGAÇÃO RBAC
# ============================================================
#
# Responsabilidade:
#
#     Impedir escalada de privilégios durante alterações RBAC.
#
# Regra central:
#
#     Um usuário só pode CONCEDER privilégios que ele próprio
#     já possui.
#
# Aplicações:
#
#     User -> Role
#         Uma Role só pode ser atribuída se todas as permissões
#         dessa Role também pertencerem ao usuário executor.
#
#     Role -> Permission
#         Uma Permission só pode ser adicionada a uma Role se
#         o usuário executor também possuir essa Permission.
#
# IMPORTANTE:
#
#     Este módulo NÃO implementa regras como:
#
#         - "último administrador";
#         - Role chamada "Administrador";
#         - lista fixa de permissões críticas;
#         - hierarquia manual de Roles.
#
#     A decisão é baseada exclusivamente no RBAC efetivamente
#     armazenado no banco.
# ============================================================

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)


# ============================================================
# PERMISSÕES EFETIVAS DO USUÁRIO
# ============================================================

def obter_permission_ids_usuario(
    usuario: User,
    db: Session,
) -> set[int]:
    """
    Retorna os IDs de todas as Permissions efetivamente
    concedidas ao usuário através de suas Roles.

    Fluxo:

        User
          ↓
        UserRole
          ↓
        RolePermission
          ↓
        Permission
    """

    resultados = (
        db.query(
            Permission.id
        )
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        )
        .join(
            UserRole,
            UserRole.role_id == RolePermission.role_id,
        )
        .filter(
            UserRole.user_id == usuario.id
        )
        .distinct()
        .all()
    )

    return {
        permission_id
        for (permission_id,) in resultados
    }


# ============================================================
# PERMISSÕES DE UMA ROLE
# ============================================================

def obter_permission_ids_role(
    role_id: int,
    db: Session,
) -> set[int]:
    """
    Retorna os IDs das Permissions atualmente associadas
    à Role informada.
    """

    resultados = (
        db.query(
            RolePermission.permission_id
        )
        .filter(
            RolePermission.role_id == role_id
        )
        .all()
    )

    return {
        permission_id
        for (permission_id,) in resultados
    }


# ============================================================
# VALIDAR DELEGAÇÃO DE ROLE
# ============================================================

def validar_delegacao_role(
    usuario_executor: User,
    role: Role,
    db: Session,
) -> None:
    """
    Verifica se o usuário executor pode atribuir a Role.

    Para conceder a Role, o executor precisa possuir todas
    as Permissions atualmente presentes nela.

    Uma Role sem Permissions não concede privilégio e,
    portanto, pode ser atribuída normalmente.
    """

    permissoes_role = obter_permission_ids_role(
        role_id=role.id,
        db=db,
    )

    if not permissoes_role:
        return

    permissoes_executor = obter_permission_ids_usuario(
        usuario=usuario_executor,
        db=db,
    )

    permissoes_nao_delegaveis = (
        permissoes_role
        - permissoes_executor
    )

    if permissoes_nao_delegaveis:
        raise HTTPException(
            status_code=403,
            detail=(
                "Você não pode atribuir esta Role porque ela "
                "concede uma ou mais permissões que você não possui."
            ),
        )


# ============================================================
# VALIDAR DELEGAÇÃO DE VÁRIAS ROLES
# ============================================================

def validar_delegacao_roles(
    usuario_executor: User,
    roles: list[Role],
    db: Session,
) -> None:
    """
    Valida todas as Roles que serão concedidas ao usuário.

    A operação inteira é bloqueada se pelo menos uma Role
    conceder privilégio que o executor não possui.
    """

    for role in roles:

        validar_delegacao_role(
            usuario_executor=usuario_executor,
            role=role,
            db=db,
        )


# ============================================================
# VALIDAR DELEGAÇÃO DE PERMISSION
# ============================================================

def validar_delegacao_permissao(
    usuario_executor: User,
    permissao: Permission,
    db: Session,
) -> None:
    """
    Verifica se o usuário executor pode conceder a Permission.

    Para adicionar uma Permission a uma Role, o executor
    precisa possuir essa mesma Permission.
    """

    permissoes_executor = obter_permission_ids_usuario(
        usuario=usuario_executor,
        db=db,
    )

    if permissao.id not in permissoes_executor:
        raise HTTPException(
            status_code=403,
            detail=(
                "Você não pode conceder esta permissão porque "
                "ela não faz parte das suas permissões atuais."
            ),
        )


# ============================================================
# VALIDAR DELEGAÇÃO DE VÁRIAS PERMISSIONS
# ============================================================

def validar_delegacao_permissoes(
    usuario_executor: User,
    permissoes: list[Permission],
    db: Session,
) -> None:
    """
    Valida um conjunto de Permissions que será concedido.

    Utilizado principalmente na substituição completa das
    permissões de uma Role.
    """

    if not permissoes:
        return

    permissoes_executor = obter_permission_ids_usuario(
        usuario=usuario_executor,
        db=db,
    )

    permission_ids_solicitados = {
        permissao.id
        for permissao in permissoes
    }

    permissoes_nao_delegaveis = (
        permission_ids_solicitados
        - permissoes_executor
    )

    if permissoes_nao_delegaveis:
        raise HTTPException(
            status_code=403,
            detail=(
                "Você não pode conceder uma ou mais permissões "
                "porque elas não fazem parte das suas permissões atuais."
            ),
        )