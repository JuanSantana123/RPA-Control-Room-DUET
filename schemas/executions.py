# ============================================================
# DUET CORE - SCHEMAS - EXECUTIONS
# ============================================================
#
# Contratos Pydantic utilizados pelos fluxos de execução.
#
# Este módulo NÃO executa robôs, não acessa banco de dados,
# não controla fila e não registra endpoints FastAPI.
#
# Os modelos abaixo foram extraídos literalmente do
# api/executions.py atual.
# ============================================================

from typing import Literal

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    # Origem da execução.
    #
    # robot:
    #     Robot publicado.
    #
    # development:
    #     AutomationProject da área de Desenvolvimento.
    source_type: str = "robot"

    # Preenchido somente para execução de Robot publicado.
    robot_id: int | None = None

    # Preenchido somente para execução de Desenvolvimento.
    project_id: int | None = None

    # ID da execução que já está na fila.
    #
    # Quando uma execução é solicitada normalmente,
    # esse campo fica vazio.
    #
    # Quando o Worker processa uma execução "queued",
    # ele informa este ID para reaproveitar o registro.
    execution_id: int | None = None

    # Usuário responsável pela execução.
    # Pode vir de uma execução manual ou do Scheduler.
    user_id: int | None = None


class DevelopmentExecutionRequest(BaseModel):
    # Agent escolhido para executar o snapshot temporário
    # do AutomationProject.
    agent_id: str


class ExecutionListItem(BaseModel):
    id: int = Field(..., gt=0)
    source_type: str
    robot_id: int | None
    robot_version: int | None
    project_id: int | None
    robot_name: str
    filename: str
    folder_name: str | None
    user_id: int | None
    username: str | None
    user_name: str | None
    agent_id: str
    agent_name: str
    schedule_id: int | None
    schedule_run_id: str | None
    pid: int | None
    status: str
    started_at: str | None
    finished_at: str | None
    error_message: str | None


class ExecutionListResponse(BaseModel):
    status: Literal["success"]
    total: int = Field(..., ge=0)
    executions: list[ExecutionListItem]
