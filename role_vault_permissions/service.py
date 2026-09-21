# ============================================================
# ROLE VAULT PERMISSIONS - SERVICE
# ============================================================
#
# Responsável pelas regras de negócio utilizadas para
# consultar e configurar as permissões do Vault de uma Role.
#
# A persistência real utiliza o RBAC genérico:
#
#     Role
#       ↓
#     RolePermission
#       ↓
#     Permission
#
# Os nomes can_* são mantidos apenas por compatibilidade com
# o contrato HTTP existente.
#
# IMPORTANTE:
#
# Nesta etapa de modularização estamos preservando o
# comportamento atual.
#
# A revisão de autorização de quem pode ALTERAR permissões
# será realizada separadamente, depois da comprovação de
# equivalência com o router original.
# ============================================================

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import RolePermission

from schemas.role_vault_permissions import (
    RoleVaultPermissionRequest,
)

from role_vault_permissions.repository import (
    buscar_role,
    buscar_permissao_vault,
    buscar_role_permission,
)


# ============================================================
# MAPA DE COMPATIBILIDADE
# ============================================================
#
# Traduz o contrato antigo can_* para as actions utilizadas
# pelo RBAC genérico.
# ============================================================

VAULT_PERMISSION_MAP = {
    "can_view": "view",
    "can_create": "create",
    "can_edit": "edit",
    "can_delete": "delete",
    "can_use": "use",
}


# ============================================================
# CONFIGURAR PERMISSÕES DA ROLE
# ============================================================

def configurar_permissoes_role_service(
    role_id: int,
    dados: RoleVaultPermissionRequest,
    db: Session,
):
    """
    Configura as permissões do Vault associadas a uma Role.

    Esta função preserva o comportamento do endpoint POST
    original.

    Para cada propriedade can_*:

    - True:
        garante que o vínculo RolePermission exista;

    - False:
        garante que o vínculo RolePermission não exista.

    Ao final, todas as alterações são persistidas em uma
    única chamada db.commit().
    """

    # ========================================================
    # ROLE
    # ========================================================

    role = buscar_role(
        db=db,
        role_id=role_id,
    )

    if not role:

        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    # ========================================================
    # CONFIGURAÇÃO
    # ========================================================

    permissoes_configuradas = {}

    for campo, action in VAULT_PERMISSION_MAP.items():

        # Obtém o estado solicitado no contrato can_*.
        habilitada = getattr(
            dados,
            campo,
        )

        # Preserva exatamente o formato retornado pela API.
        permissoes_configuradas[campo] = habilitada

        # ----------------------------------------------------
        # CATÁLOGO RBAC
        # ----------------------------------------------------

        permissao = buscar_permissao_vault(
            db=db,
            action=action,
        )

        # No POST original, uma permissão ausente no catálogo
        # é tratada como erro interno.
        if not permissao:

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Permissão 'Vault:{action}' "
                    f"não encontrada no catálogo."
                ),
            )

        # ----------------------------------------------------
        # VÍNCULO ATUAL
        # ----------------------------------------------------

        role_permission = buscar_role_permission(
            db=db,
            role_id=role_id,
            permission_id=permissao.id,
        )

        # ----------------------------------------------------
        # ADICIONAR
        # ----------------------------------------------------

        if habilitada and not role_permission:

            db.add(
                RolePermission(
                    role_id=role_id,
                    permission_id=permissao.id,
                )
            )

        # ----------------------------------------------------
        # REMOVER
        # ----------------------------------------------------

        elif (
            not habilitada
            and role_permission
        ):

            db.delete(
                role_permission
            )

    # ========================================================
    # TRANSAÇÃO
    # ========================================================

    db.commit()

    # ========================================================
    # RETORNO
    # ========================================================

    return {
        "message": (
            "Permissões da Role configuradas com sucesso."
        ),
        "role": {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        },
        "permissions": permissoes_configuradas,
    }


# ============================================================
# CONSULTAR PERMISSÕES DA ROLE
# ============================================================

def consultar_permissoes_role_service(
    role_id: int,
    db: Session,
):
    """
    Consulta as permissões do Vault atualmente associadas
    a uma Role.

    Preserva o comportamento do endpoint GET original.

    Caso determinada Permission do Vault não exista no
    catálogo RBAC, o valor correspondente é retornado como
    False.
    """

    # ========================================================
    # ROLE
    # ========================================================

    role = buscar_role(
        db=db,
        role_id=role_id,
    )

    if not role:

        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    # ========================================================
    # PERMISSÕES
    # ========================================================

    permissoes = {}

    for campo, action in VAULT_PERMISSION_MAP.items():

        permissao = buscar_permissao_vault(
            db=db,
            action=action,
        )

        # O GET original considera uma Permission ausente
        # como uma permissão desabilitada.
        if not permissao:

            permissoes[campo] = False
            continue

        role_permission = buscar_role_permission(
            db=db,
            role_id=role_id,
            permission_id=permissao.id,
        )

        permissoes[campo] = (
            role_permission is not None
        )

    # ========================================================
    # RETORNO
    # ========================================================

    return {
        "role": {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        },
        "permissions": permissoes,
    }


# ============================================================
# ALTERAR PERMISSÕES DA ROLE
# ============================================================

def alterar_permissoes_role_service(
    role_id: int,
    dados: RoleVaultPermissionRequest,
    db: Session,
):
    """
    Altera as permissões do Vault associadas a uma Role.

    Esta função preserva especificamente o comportamento do
    endpoint PUT original.

    Apesar de POST e PUT possuírem lógica semelhante, eles
    permanecem como operações separadas nesta primeira etapa
    para facilitar a comparação com a implementação anterior.
    """

    # ========================================================
    # ROLE
    # ========================================================

    role = buscar_role(
        db=db,
        role_id=role_id,
    )

    if not role:

        raise HTTPException(
            status_code=404,
            detail="Role não encontrada.",
        )

    # ========================================================
    # ATUALIZAÇÃO
    # ========================================================

    for campo, action in VAULT_PERMISSION_MAP.items():

        habilitada = getattr(
            dados,
            campo,
        )

        permissao = buscar_permissao_vault(
            db=db,
            action=action,
        )

        # Assim como no PUT original, a ausência de uma
        # Permission esperada no catálogo é erro interno.
        if not permissao:

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Permissão 'Vault:{action}' "
                    f"não encontrada no catálogo."
                ),
            )

        role_permission = buscar_role_permission(
            db=db,
            role_id=role_id,
            permission_id=permissao.id,
        )

        # ----------------------------------------------------
        # ADICIONAR
        # ----------------------------------------------------

        if habilitada and not role_permission:

            db.add(
                RolePermission(
                    role_id=role_id,
                    permission_id=permissao.id,
                )
            )

        # ----------------------------------------------------
        # REMOVER
        # ----------------------------------------------------

        elif (
            not habilitada
            and role_permission
        ):

            db.delete(
                role_permission
            )

    # ========================================================
    # TRANSAÇÃO
    # ========================================================

    db.commit()

    # ========================================================
    # CONSULTA DO ESTADO PERSISTIDO
    # ========================================================
    #
    # Preservamos o comportamento do PUT original, que depois
    # do commit consulta novamente cada relacionamento antes
    # de construir a resposta.
    # ========================================================

    permissoes_atualizadas = {}

    for campo, action in VAULT_PERMISSION_MAP.items():

        permissao = buscar_permissao_vault(
            db=db,
            action=action,
        )

        if not permissao:

            permissoes_atualizadas[campo] = False
            continue

        role_permission = buscar_role_permission(
            db=db,
            role_id=role_id,
            permission_id=permissao.id,
        )

        permissoes_atualizadas[campo] = (
            role_permission is not None
        )

    # ========================================================
    # RETORNO
    # ========================================================

    return {
        "message": (
            "Permissões da Role atualizadas com sucesso."
        ),
        "role": {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        },
        "permissions": permissoes_atualizadas,
    }