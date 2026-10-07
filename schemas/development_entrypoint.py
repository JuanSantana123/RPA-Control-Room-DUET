# ============================================================
# DUET CORE - SCHEMAS - DEVELOPMENT ENTRYPOINT
# ============================================================

from pydantic import BaseModel, Field


class ProjectEntrypointUpdate(BaseModel):
    """Novo arquivo Python de entrada do AutomationProject."""

    entrypoint_path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )
