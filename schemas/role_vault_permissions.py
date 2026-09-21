# ============================================================
# SCHEMAS - ROLE VAULT PERMISSIONS
# ============================================================
#
# Contratos de entrada utilizados pela API de configuração
# das permissões do Vault associadas às Roles.
#
# IMPORTANTE:
#
# Os nomes can_* são mantidos por compatibilidade com a API
# existente.
#
# Internamente, essas propriedades representam permissões do
# RBAC genérico:
#
#     can_view   -> Vault:view
#     can_create -> Vault:create
#     can_edit   -> Vault:edit
#     can_delete -> Vault:delete
#     can_use    -> Vault:use
#
# Este módulo NÃO acessa banco de dados e NÃO contém regras
# de autorização.
# ============================================================

from pydantic import BaseModel, Field


# ============================================================
# CONFIGURAÇÃO DAS PERMISSÕES DO VAULT
# ============================================================

class RoleVaultPermissionRequest(BaseModel):
    """
    Mantém o formato existente da API.

    Cada propriedade informa se determinada permissão do
    Vault deve estar vinculada à Role.
    """

    can_view: bool = Field(
        False,
        description="Permite visualizar recursos do Vault.",
    )

    can_create: bool = Field(
        False,
        description="Permite criar recursos no Vault.",
    )

    can_edit: bool = Field(
        False,
        description="Permite alterar recursos do Vault.",
    )

    can_delete: bool = Field(
        False,
        description="Permite excluir recursos do Vault.",
    )

    can_use: bool = Field(
        False,
        description="Permite utilizar credenciais do Vault.",
    )