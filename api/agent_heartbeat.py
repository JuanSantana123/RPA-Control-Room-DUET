# ============================================================
# ROUTER DE HEARTBEAT DOS AGENTS
# ============================================================
#
# Camada HTTP responsável pela comunicação de heartbeat
# entre os Agents das VMs e o Control Room.
#
# Responsabilidades deste arquivo:
#
# - registrar o endpoint FastAPI;
# - autenticar tecnicamente o Agent através do agent_token;
# - validar se o token pertence ao Agent informado;
# - validar o payload através do schema Pydantic;
# - delegar o processamento do heartbeat ao service.
#
# A regra de negócio está em:
#
#     agent_heartbeat/service.py
#
# O contrato recebido do Agent está em:
#
#     schemas/agent_heartbeat.py
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from auth.agent_dependencies import (
    get_agent_atual,
)

from schemas.agent_heartbeat import (
    AgentHeartbeatRequest,
)

from agent_heartbeat.service import (
    processar_agent_heartbeat_service,
)


# ============================================================
# ROUTER
# ============================================================
#
# Este router não utiliza a sessão de usuário do Control Room.
#
# A autenticação é feita especificamente pelo Agent através de:
#
#     get_agent_atual
#
# ============================================================

router = APIRouter(
    tags=["Agent Heartbeat"]
)


# ============================================================
# HEARTBEAT
# ============================================================

@router.post(
    "/agents/heartbeat",
    summary="Atualizar heartbeat do Agent",
    description=(
        "Recebe o heartbeat enviado por um Agent para informar ao "
        "Control Room que o Agent está ativo e disponível. "
        "O heartbeat também é utilizado para atualizar as informações "
        "e o status de comunicação do Agent. "
        "Este endpoint é utilizado internamente pelo Agent e requer "
        "autenticação por agent_token."
    )
)
def agent_heartbeat(
    request: AgentHeartbeatRequest,
    agent_autenticado=Depends(get_agent_atual),
):
    """
    Recebe o heartbeat enviado pelo Agent.

    Parâmetros
    ----------
    request:
        Payload validado pelo schema AgentHeartbeatRequest.

    agent_autenticado:
        Agent identificado através do agent_token pela dependency
        get_agent_atual.

    Segurança
    ---------
    O Agent autenticado pelo token deve possuir o mesmo agent_id
    informado no payload do heartbeat.

    Somente após essa validação a regra de negócio é executada.
    """

    # ========================================================
    # VALIDA AGENT AUTENTICADO
    # ========================================================
    #
    # Preservamos esta validação na camada HTTP exatamente
    # como no código original.
    #
    # Dessa forma, um Agent autenticado não pode enviar um
    # heartbeat utilizando o agent_id de outro Agent.
    # ========================================================

    if agent_autenticado.agent_id != request.agent_id:

        raise HTTPException(
            status_code=403,
            detail="O token não pertence ao Agent informado.",
        )


    # ========================================================
    # DELEGA PROCESSAMENTO
    # ========================================================
    #
    # Depois da autenticação e validação de identidade,
    # o processamento do heartbeat é responsabilidade
    # do service.
    # ========================================================

    return processar_agent_heartbeat_service(
        request=request,
    )