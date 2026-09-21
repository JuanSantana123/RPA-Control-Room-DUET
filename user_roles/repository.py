# ============================================================
# REPOSITORY - USER ROLES
# ============================================================
#
# Responsabilidade:
#
#     Centralizar as consultas e operações de persistência
#     utilizadas pelo domínio User Roles.
#
# Este módulo NÃO conhece:
#
#     - FastAPI;
#     - Depends;
#     - HTTPException;
#     - permissões HTTP;
#     - Request/Response.
#
# Regras de negócio permanecem em:
#
#     user_roles/service.py
#
# ============================================================

from sqlalchemy.orm import Session

from models import (
    Role,
    User,
    UserRole,
)


# ============================================================
# USUÁRIO
# ============================================================

def buscar_usuario_por_id(
    db: Session,
    user_id: int,
) -> User | None:
    """
    Busca um usuário pelo identificador interno.

    Parâmetros:

        db:
            Sessão SQLAlchemy utilizada pela operação.

        user_id:
            Identificador do usuário.

    Retorno:

        User:
            quando o usuário existe.

        None:
            quando nenhum usuário foi encontrado.
    """

    return (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
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


# ============================================================
# LISTAR ASSOCIAÇÕES DO USUÁRIO
# ============================================================

def listar_relacionamentos_usuario(
    db: Session,
    user_id: int,
) -> list[UserRole]:
    """
    Retorna todas as associações UserRole pertencentes
    ao usuário informado.
    """

    return (
        db.query(UserRole)
        .filter(
            UserRole.user_id == user_id
        )
        .all()
    )


# ============================================================
# BUSCAR ASSOCIAÇÃO
# ============================================================

def buscar_relacionamento(
    db: Session,
    user_id: int,
    role_id: int,
) -> UserRole | None:
    """
    Busca uma associação específica entre usuário e Role.
    """

    return (
        db.query(UserRole)
        .filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        .first()
    )


# ============================================================
# CRIAR ASSOCIAÇÃO
# ============================================================

def criar_relacionamento(
    db: Session,
    user_id: int,
    role_id: int,
) -> UserRole:
    """
    Cria em memória uma nova associação UserRole.

    IMPORTANTE:
        esta função adiciona o objeto à sessão, mas NÃO executa
        commit.

    O controle transacional pertence ao service.
    """

    relacionamento = UserRole(
        user_id=user_id,
        role_id=role_id,
    )

    db.add(
        relacionamento
    )

    return relacionamento


# ============================================================
# REMOVER ASSOCIAÇÃO
# ============================================================

def remover_relacionamento(
    db: Session,
    relacionamento: UserRole,
) -> None:
    """
    Marca uma associação UserRole para remoção.

    IMPORTANTE:
        não executa commit.

    O commit permanece sob responsabilidade do service para
    que a operação de negócio controle sua própria transação.
    """

    db.delete(
        relacionamento
    )

# ============================================================
# BUSCAR VÁRIAS ROLES
# ============================================================

def buscar_roles_por_ids(
    db: Session,
    role_ids: list[int],
) -> list[Role]:
    """
    Busca todas as Roles cujos IDs foram informados.

    Esta função somente consulta o banco.
    Validação de existência e regras de delegação pertencem
    ao service.
    """

    if not role_ids:
        return []

    return (
        db.query(Role)
        .filter(
            Role.id.in_(role_ids)
        )
        .all()
    )


# ============================================================
# REMOVER TODAS AS ROLES DE UM USUÁRIO
# ============================================================

def remover_relacionamentos_usuario(
    db: Session,
    user_id: int,
) -> None:
    """
    Remove da sessão todas as associações UserRole do usuário.

    IMPORTANTE:
        não executa commit.

    O controle transacional continua pertencendo ao service.
    """

    (
        db.query(UserRole)
        .filter(
            UserRole.user_id == user_id
        )
        .delete(
            synchronize_session=False
        )
    )