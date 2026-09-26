# ============================================================
# DUET CORE - SCHEMAS - SCHEDULES
# ============================================================
#
# Define os contratos de entrada utilizados pelos endpoints
# HTTP responsáveis pelos agendamentos do Control Room.
#
# Este módulo:
# - contém modelos Pydantic relacionados a Schedules;
# - define os campos aceitos na criação/edição;
# - mantém o contrato atualmente utilizado pela API.
#
# Este módulo NÃO:
# - acessa banco de dados;
# - executa regras do Scheduler;
# - cria threads;
# - registra endpoints FastAPI;
# - executa robôs.
#
# IMPORTANTE:
# Os campos e valores padrão abaixo foram extraídos do
# api/schedules.py sem alteração do contrato atual da API.
# ============================================================

from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# MODELO DE CRIAÇÃO / ATUALIZAÇÃO
# ============================================================

class ScheduleCreateRequest(BaseModel):
    """
    Payload utilizado atualmente tanto para criação quanto
    para atualização de um agendamento.
    """

    robot_id: int

    agent_id: str | None = None

    tipo: str

    data_inicio: str

    horario: str

    dias_semana: str | None = None

    intervalo_ativo: bool = False

    intervalo_valor: int | None = None

    intervalo_unidade: str | None = None

    horario_fim: str | None = None

    misfire_policy: Literal["run_once", "skip"] = "run_once"

    misfire_grace_seconds: int = Field(default=300, ge=30, le=86400)


class ScheduleListItem(BaseModel):
    id: int = Field(..., gt=0)
    robot_id: int = Field(..., gt=0)
    robot_name: str
    agent_id: str | None
    agent_name: str
    tipo: str
    data_inicio: str | None
    horario: str
    dias_semana: str | None
    ativo: bool
    proxima_execucao: str | None
    ultima_execucao: str | None
    intervalo_ativo: bool
    intervalo_valor: int | None
    intervalo_unidade: str | None
    horario_fim: str | None
    misfire_policy: Literal["run_once", "skip"]
    misfire_grace_seconds: int = Field(..., ge=30, le=86400)
    ultima_ocorrencia_perdida: str | None


class ScheduleListResponse(BaseModel):
    status: Literal["success"]
    total: int = Field(..., ge=0)
    schedules: list[ScheduleListItem]


class ScheduleRobotOption(BaseModel):
    id: int = Field(..., gt=0)
    name: str


class ScheduleAgentOption(BaseModel):
    agent_id: str
    name: str
    status: str


class ScheduleOptionsResponse(BaseModel):
    status: Literal["success"]
    robots: list[ScheduleRobotOption]
    agents: list[ScheduleAgentOption]
    timezone: str
