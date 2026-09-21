# ============================================================
# DUET CORE - SCHEMAS - ROBOTS
# ============================================================
#
# Contratos Pydantic utilizados pelos endpoints de Robots.
#
# Este módulo NÃO acessa banco, NÃO manipula artefatos físicos,
# NÃO publica versões e NÃO registra rotas FastAPI.
#
# Os contratos foram extraídos do api/robots.py atual sem
# alteração de campos, tipos ou validações.
# ============================================================

from pydantic import BaseModel, Field


class RobotFolderRequest(
    BaseModel
):
    name: str = Field(
        ...,
        description="Nome da pasta de robôs."
    )

    parent_id: int | None = Field(
        None,
        description="ID da pasta pai. Deixe vazio para criar uma pasta na raiz."
    )
