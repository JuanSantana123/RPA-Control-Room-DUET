# ============================================================
# ROUTER DE COMUNICAÇÃO DAS EXECUÇÕES DOS AGENTS
# ============================================================
#
# Camada HTTP responsável por receber resultados finais de
# execuções enviados pelos Agents ao Control Room.
#
# Responsabilidades deste arquivo:
#
# - registrar o endpoint FastAPI;
# - autenticar tecnicamente o Agent;
# - receber os parâmetros HTTP;
# - validar o payload através do schema Pydantic;
# - delegar a regra de negócio ao service.
#
# A regra de processamento do resultado está em:
#
#     agent_executions/service.py
#
# O contrato recebido do Agent está em:
#
#     schemas/agent_executions.py
#
# ============================================================

from fastapi import APIRouter, Depends

from auth.agent_dependencies import get_agent_atual

from schemas.agent_executions import (
    ExecutionResultRequest,
)

from agent_executions.service import (
    receber_resultado_execucao_service,
)


# ============================================================
# ROUTER
# ============================================================
#
# Diferentemente das APIs utilizadas pelo frontend, esta rota
# não utiliza get_usuario_atual.
#
# A autenticação é técnica e ocorre através do Agent:
#
#     get_agent_atual
#
# ============================================================

router = APIRouter(
    tags=["Agent Executions"]
)


# ============================================================
# RECEBER RESULTADO DA EXECUÇÃO DO AGENT
# ============================================================

@router.post(
    "/executions/{execution_id}/result",
    summary="Receber resultado da execução",
    description=(
        "Recebe o resultado final de uma execução enviado pelo Agent. "
        "O Control Room utiliza essas informações para atualizar o "
        "status, a data de término e a mensagem de erro da execução. "
        "Este endpoint é utilizado na comunicação entre Agent e "
        "Control Room e requer autenticação por agent_token."
    )
)
def receber_resultado_execucao(
    execution_id: int,
    request: ExecutionResultRequest,
    agent_autenticado=Depends(get_agent_atual)
):
    """
    Recebe o resultado final de uma execução enviado pelo Agent.

    Parâmetros
    ----------
    execution_id:
        Identificador da execução recebido através da URL.

    request:
        Payload validado pelo schema ExecutionResultRequest.

    agent_autenticado:
        Agent identificado através do agent_token pela dependency
        get_agent_atual.

    A camada HTTP não altera diretamente a Execution.

    Toda a regra de validação e persistência é delegada para:

        receber_resultado_execucao_service()
    """

    return receber_resultado_execucao_service(
        execution_id=execution_id,
        request=request,
        agent_autenticado=agent_autenticado,
    )