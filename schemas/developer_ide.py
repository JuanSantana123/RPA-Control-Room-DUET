# ============================================================
# DUET CORE - SCHEMAS - EXTERNAL IDE
# ============================================================
#
# Contratos HTTP específicos da integração com IDEs externas.
# ============================================================

from pydantic import BaseModel, Field


class DeveloperIdeRedeemRequest(BaseModel):
    """Código temporário recebido pelo DUET Developer Bridge."""

    launch_code: str = Field(
        ...,
        min_length=20,
        max_length=512,
    )
