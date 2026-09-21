# ============================================================
# SCHEMAS - AGENT EXECUTIONS
# ============================================================
#
# Contratos utilizados na comunicação entre:
#
#     RPA Agent
#         │
#         ▼
#     Control Room
#
# Este arquivo contém somente modelos de dados.
#
# Não possui:
#
# - acesso ao banco;
# - autenticação;
# - regras de negócio;
# - endpoints FastAPI.
#
# ============================================================

from pydantic import BaseModel


# ============================================================
# RESULTADO DE EXECUÇÃO ENVIADO PELO AGENT
# ============================================================

class ExecutionResultRequest(BaseModel):
    """
    Representa o resultado final de uma execução enviado
    pelo Agent ao Control Room.

    Observação:
        started_at faz parte do contrato recebido atualmente,
        embora a implementação atual do Control Room não utilize
        esse valor durante a atualização da Execution.
    """

    # ID da execução informado também no payload.
    execution_id: int

    # Agent que afirma estar enviando o resultado.
    #
    # Posteriormente o backend compara esse valor com:
    #
    # - o Agent autenticado pelo agent_token;
    # - o Agent associado à Execution.
    agent_id: str

    # Resultado final informado pelo Agent.
    status: str

    # Mensagem associada ao resultado.
    #
    # Quando status == "error", atualmente essa mensagem
    # é armazenada em Execution.error_message.
    message: str

    # Datas enviadas pelo Agent.
    #
    # Mantemos str exatamente como no contrato original.
    started_at: str
    finished_at: str