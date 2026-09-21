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

from pydantic import BaseModel


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