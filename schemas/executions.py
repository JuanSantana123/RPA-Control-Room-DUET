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

from pydantic import BaseModel


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
