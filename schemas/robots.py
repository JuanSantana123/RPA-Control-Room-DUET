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

from typing import Literal

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


class RobotVersionPublisher(BaseModel):
    id: int
    name: str
    username: str


class RobotVersionSourceProject(BaseModel):
    id: int
    name: str


class RobotVersionCatalogItem(BaseModel):
    id: int
    version: int
    filename: str
    file_hash: str
    published_at: str | None
    created_at: str
    is_current: bool
    publisher: RobotVersionPublisher | None
    source_project: RobotVersionSourceProject | None


class RobotVersionCatalogRobot(BaseModel):
    id: int
    name: str
    filename: str
    current_version: int


class RobotVersionsResponse(BaseModel):
    status: Literal["success"]
    robot: RobotVersionCatalogRobot
    total: int = Field(ge=0)
    versions: list[RobotVersionCatalogItem]
