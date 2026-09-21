# ============================================================
# ROUTER - AGENTS
# ============================================================
#
# Camada HTTP do domínio de Agents.
#
# RESPONSABILIDADES DESTE ARQUIVO:
# - declarar URLs;
# - declarar métodos HTTP;
# - aplicar autenticação e RBAC;
# - receber parâmetros HTTP;
# - fornecer sessão de banco aos services;
# - delegar regras de negócio.
#
# REGRAS DE NEGÓCIO:
# agents/
#
# CONTRATOS:
# schemas/agents.py
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_usuario_atual
from auth.permissions import require_permission
from database import SessionLocal
from schemas.agents import (
    AgentCreateRequest,
    AgentEnvironmentUpdateRequest,
    AgentRegisterRequest,
)

from agents.bootstrap_service import (
    download_agent_bootstrap_service,
    obter_installation_config_service,
)

from agents.catalog_service import (
    alterar_ambiente_agent_service,
    consultar_agent_service,
    criar_agent_service,
    excluir_agent_service,
    listar_agents_disponiveis_execucao_service,
    listar_agents_service,
)

from agents.installer_service import (
    gerar_instalador_agent_service,
)

from agents.monitoring_service import (
    monitorar_agents,
    verificar_agents_offline,
)

from agents.registration_service import (
    registrar_agent_service,
)


# ============================================================
# BANCO DE DADOS
# ============================================================

def get_db():
    """
    Cria uma sessão SQLAlchemy para a requisição HTTP.

    O FastAPI executa o bloco finally mesmo quando ocorre
    uma exceção durante o processamento da requisição.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["Agents"],
    dependencies=[
        Depends(get_usuario_atual),
    ],
)


# ============================================================
# LISTAR AGENTS
# ============================================================

@router.get(
    "/agents",
    summary="Listar Agents",
    description=(
        "Retorna todos os Agents cadastrados no Control Room. "
        "A resposta contém informações de identificação, conexão, "
        "diretório de RPAs e status atual de cada Agent. "
        "Requer autenticação do usuário e a permissão 'Agents:view'."
    ),
    dependencies=[
        Depends(
            require_permission("Agents", "view")
        ),
    ],
)
def list_agents(
    db: Session = Depends(get_db),
):
    """
    Lista os Agents ativos cadastrados no Control Room.

    Permissão:
        Agents:view
    """

    return listar_agents_service(db)


# ============================================================
# LISTAR AGENTS DISPONÍVEIS PARA EXECUÇÃO
# ============================================================

@router.get(
    "/agents/execution/available-agents",
    summary="Listar Agents disponíveis para execução",
    description=(
        "Retorna os Agents cadastrados no Control Room que podem "
        "ser selecionados para uma execução manual de um robô. "
        "O endpoint é utilizado pelo frontend para apresentar "
        "os Agents disponíveis ao usuário. "
        "Não retorna o agent_token. "
        "Requer autenticação do usuário e a permissão "
        "'Executions:execute'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Executions",
                "execute",
            )
        ),
    ],
)
def listar_agents_disponiveis_para_execucao(
    db: Session = Depends(get_db),
):
    """
    Lista Agents disponíveis para execução manual.

    Permissão:
        Executions:execute
    """

    return listar_agents_disponiveis_execucao_service(
        db
    )


# ============================================================
# CONSULTAR AGENT
# ============================================================

@router.get(
    "/agents/{agent_id}",
    summary="Consultar Agent",
    description=(
        "Retorna os dados de um Agent específico cadastrado no "
        "Control Room. O Agent é localizado pelo seu identificador "
        "único (agent_id). "
        "Requer autenticação do usuário e a permissão 'Agents:view'."
    ),
    dependencies=[
        Depends(
            require_permission("Agents", "view")
        ),
    ],
)
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """
    Consulta um Agent pelo identificador.

    Permissão:
        Agents:view
    """

    return consultar_agent_service(
        agent_id,
        db,
    )


# ============================================================
# REGISTRAR AGENT
# ============================================================

@router.post(
    "/agents/register",
    summary="Registrar Agent",
    description=(
        "Registra um Agent existente no Control Room. "
        "O endpoint valida a comunicação com o Agent informado, "
        "obtém suas informações de configuração e atualiza seu "
        "cadastro no Control Room. "
        "Requer autenticação do usuário e a permissão 'Agents:create'."
    ),
    dependencies=[
        Depends(
            require_permission("Agents", "create")
        ),
    ],
)
def register_agent(
    request: AgentRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Valida e registra um Agent previamente criado.

    Permissão:
        Agents:create
    """

    return registrar_agent_service(
        request,
        db,
    )


# ============================================================
# CRIAR AGENT
# ============================================================

@router.post(
    "/agents",
    summary="Criar Agent",
    description=(
        "Cria um novo Agent no Control Room. "
        "O Agent é criado inicialmente com status 'pending' "
        "e recebe um identificador e um token exclusivos. "
        "O token é utilizado posteriormente pelo Agent para "
        "autenticar suas comunicações com o Control Room. "
        "Requer autenticação do usuário e a permissão 'Agents:create'."
    ),
    dependencies=[
        Depends(
            require_permission("Agents", "create")
        ),
    ],
)
def create_agent(
    request: AgentCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Cria o cadastro inicial de um Agent.

    Permissão:
        Agents:create
    """

    return criar_agent_service(
        request,
        db,
    )


# ============================================================
# CONFIGURAÇÃO DE INSTALAÇÃO
# ============================================================

@router.get(
    "/agents/{agent_id}/installation-config",
    summary="Obter configuração de instalação do Agent",
    description=(
        "Retorna a configuração necessária para instalar e configurar "
        "um Agent específico. A resposta contém dados de bootstrap, "
        "incluindo o agent_token necessário para a comunicação do Agent "
        "com o Control Room. "
        "Este endpoint deve ser tratado como sensível e seu conteúdo "
        "não deve ser compartilhado. "
        "Requer autenticação do usuário e a permissão 'Agents:view'."
    ),
    dependencies=[
        Depends(
            # Este endpoint entrega configuração contendo material de
            # autenticação do Agent. Agents:view não é suficiente.
            require_permission("Agents", "bootstrap")
        ),
    ],
)
def get_installation_config(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """
    Retorna a configuração de instalação do Agent.

    ATENÇÃO:
        O retorno contém agent_token.

    Permissão atual:
        Agents:view

    A adequação dessa permissão será analisada posteriormente
    durante o hardening de segurança.
    """

    return obter_installation_config_service(
        agent_id,
        db,
    )


# ============================================================
# DOWNLOAD DO BOOTSTRAP
# ============================================================

@router.get(
    "/agents/{agent_id}/bootstrap",
    summary="Baixar bootstrap do Agent",
    description=(
        "Gera e retorna o arquivo de bootstrap necessário para "
        "configurar um Agent específico. O arquivo contém as "
        "informações necessárias para o Agent se conectar ao "
        "Control Room, incluindo o agent_token. "
        "Este arquivo deve ser tratado como uma credencial sensível. "
        "Requer autenticação do usuário e a permissão 'Agents:view'."
    ),
    dependencies=[
        Depends(
            # O arquivo de bootstrap contém agent_token e, portanto,
            # exige autorização específica para material de bootstrap.
            require_permission("Agents", "bootstrap")
        ),
    ],
)
def download_agent_bootstrap(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """
    Gera o bootstrap para download.

    ATENÇÃO:
        O arquivo contém agent_token.

    Permissão atual:
        Agents:view
    """

    return download_agent_bootstrap_service(
        agent_id,
        db,
    )


# ============================================================
# DOWNLOAD DO INSTALADOR
# ============================================================

@router.get(
    "/agents/{agent_id}/download",
    summary="Baixar instalador do Agent",
    description=(
        "Gera e disponibiliza o instalador personalizado de um Agent. "
        "O instalador é configurado com as informações necessárias "
        "para que o Agent se conecte ao Control Room. "
        "O agent_token é utilizado internamente na geração do instalador "
        "e não é retornado diretamente pela API. "
        "Requer autenticação do usuário e a permissão 'Agents:create'."
    ),
    dependencies=[
        Depends(
            # O instalador é personalizado com material de autenticação
            # do Agent, portanto sua obtenção exige Agents:bootstrap.
            require_permission("Agents", "bootstrap")
        ),
    ],
)
def download_agent(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """
    Gera o instalador personalizado do Agent.

    Permissão:
        Agents:create
    """

    return gerar_instalador_agent_service(
        agent_id,
        db,
    )

# ============================================================
# ALTERAR AMBIENTE DO AGENT
# ============================================================

@router.patch(
    "/agents/{agent_id}/environment",
    summary="Alterar ambiente do Agent",
    description=(
        "Altera administrativamente o ambiente operacional "
        "de um Agent entre Desenvolvimento/Homologação e Produção. "
        "Requer a permissão 'Agents:edit'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Agents",
                "edit",
            )
        ),
    ],
)
def update_agent_environment(
    agent_id: str,
    request: AgentEnvironmentUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Altera o ambiente operacional do Device.

    Permissão:
        Agents:edit
    """

    return alterar_ambiente_agent_service(
        agent_id,
        request.environment,
        db,
    )
# ============================================================
# EXCLUIR AGENT
# ============================================================

@router.delete(
    "/agents/{agent_id}",
    summary="Excluir Agent",
    description=(
        "Remove logicamente um Agent cadastrado no Control Room. "
        "O registro permanece no banco para preservar o histórico "
        "das execuções relacionadas. "
        "Requer autenticação do usuário e a permissão 'Agents:delete'."
    ),
    dependencies=[
        Depends(
            require_permission("Agents", "delete")
        ),
    ],
)
def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """
    Executa o soft delete do Agent.

    Permissão:
        Agents:delete
    """

    return excluir_agent_service(
        agent_id,
        db,
    )