# ============================================================
# SCHEMAS - DEVELOPMENT PROJECT IMPORT
# ============================================================
#
# Contratos exclusivos do fluxo de importação de um projeto
# Python para a área de Desenvolvimento.
#
# Este módulo não acessa banco, filesystem ou FastAPI.
# ============================================================

from pydantic import BaseModel, Field


class DevelopmentProjectImportConfirmRequest(BaseModel):
    """Confirma uma análise pendente e cria o AutomationProject."""

    import_token: str = Field(
        ...,
        min_length=32,
        max_length=128,
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    folder_id: int | None = None

    entrypoint_path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )
