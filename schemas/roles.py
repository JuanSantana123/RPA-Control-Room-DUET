# ============================================================
# SCHEMAS - ROLES
# ============================================================
#
# Contratos de entrada HTTP utilizados pelo domínio Roles.
#
# As regras de negócio não pertencem a este módulo.
# ============================================================

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    """
    Dados necessários para criar uma Role.
    """

    name: str = Field(
        ...,
        description="Nome da Role. Deve ser único no Control Room.",
    )

    description: str | None = Field(
        default=None,
        description="Descrição opcional da finalidade da Role.",
    )


class RolePermissionCreate(BaseModel):
    """
    Dados necessários para associar uma permissão a uma Role.
    """

    permission_id: int = Field(
        ...,
        description=(
            "ID da permissão existente no catálogo "
            "de permissões do Control Room."
        ),
    )


class RolePermissionsUpdate(BaseModel):
    """
    Representa a configuração final de permissões de uma Role.
    """

    permission_ids: list[int] = Field(
        ...,
        description=(
            "Lista completa dos IDs das permissões que a Role "
            "deverá possuir. As permissões atuais serão "
            "substituídas por esta lista."
        ),
    )