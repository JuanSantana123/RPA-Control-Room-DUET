# ============================================================
# SERIALIZERS - ROLES
# ============================================================
#
# Responsabilidade:
#
#     Transformar modelos SQLAlchemy do domínio Roles em
#     estruturas simples utilizadas pelos contratos HTTP.
#
# Nenhuma consulta ao banco ou regra de negócio deve existir
# neste módulo.
# ============================================================


def serializar_role(
    role,
) -> dict:
    """
    Serializa os campos públicos completos de uma Role.
    """

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "created_at": role.created_at,
    }


def serializar_role_resumida(
    role,
) -> dict:
    """
    Serializa uma Role sem created_at.

    Utilizado em contratos históricos que retornam somente
    identificação, nome e descrição.
    """

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
    }


def serializar_permissao(
    permissao,
) -> dict:
    """
    Serializa uma Permission do catálogo.
    """

    return {
        "id": permissao.id,
        "resource": permissao.resource,
        "action": permissao.action,
    }