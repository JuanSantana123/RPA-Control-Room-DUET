# ============================================================
# DUET CORE - PROJECT ENTRYPOINT SCHEMAS
# ============================================================
#
# Contratos HTTP relacionados ao EntryPoint de um
# AutomationProject.
#
# A validação estrutural e de existência física continua
# pertencendo a development/entrypoint_service.py.
# ============================================================

from pydantic import BaseModel, Field


class ProjectEntrypointUpdate(BaseModel):
    """Solicitação de alteração do EntryPoint do projeto."""

    entrypoint_path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )