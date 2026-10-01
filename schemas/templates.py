# ============================================================
# SCHEMAS - AUTOMATION TEMPLATES
# ============================================================
#
# Contratos HTTP utilizados pelo módulo de Templates.
#
# Templates são somente a origem inicial de um projeto:
# depois da criação, o código pertence ao AutomationProject.
# ============================================================

from pydantic import BaseModel, Field


# ============================================================
# ATUALIZAÇÃO DE METADADOS
# ============================================================

class AutomationTemplateUpdate(BaseModel):
    """
    Atualiza somente metadados do Template.

    Código-fonte nunca é alterado por este contrato.
    Para alterar o código deve ser publicada uma nova versão.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=180,
    )

    description: str | None = Field(
        default=None,
        max_length=4000,
    )

    is_active: bool | None = None


# ============================================================
# CRIAÇÃO DE PROJETO A PARTIR DE TEMPLATE
# ============================================================

class TemplateProjectCreate(BaseModel):
    """
    Dados necessários para criar um AutomationProject usando
    uma versão exata de Template como origem.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    folder_id: int | None = Field(
        default=None,
        ge=1,
    )

    template_version_id: int = Field(
        ...,
        ge=1,
    )
