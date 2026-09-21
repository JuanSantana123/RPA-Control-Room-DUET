# ============================================================
# REPOSITORY - AGENTS
# ============================================================
#
# Centraliza operações de persistência relacionadas aos Agents.
#
# IMPORTANTE:
# - repository NÃO executa commit;
# - repository NÃO executa rollback;
# - repository NÃO contém regras HTTP;
# - transações pertencem aos services.
# ============================================================

from sqlalchemy.orm import Session

from models import Agent, Execution


def listar_agents_ativos(db: Session):
    """
    Retorna todos os Agents que não foram removidos logicamente.
    """

    return (
        db.query(Agent)
        .filter(Agent.is_active == 1)
        .all()
    )


def buscar_agent_por_id(
    db: Session,
    agent_id: str,
):
    """
    Localiza um Agent pelo identificador único.

    Não filtra is_active porque alguns fluxos administrativos
    precisam consultar o registro mesmo após soft delete.
    """

    return (
        db.query(Agent)
        .filter(Agent.agent_id == agent_id)
        .first()
    )

def criar_agent(
    db: Session,
    *,
    agent_id: str,
    agent_token_hash: str,
    agent_token_encrypted: str,
    environment: str,
    port: int,
    rpa_directory: str,
):
    """
    Cria a entidade Agent na sessão atual.

    Segurança:
    - agent_token_hash é utilizado para autenticação;
    - agent_token_encrypted permite recuperação controlada;
    - o token plaintext não é persistido.

    O commit será responsabilidade do service.
    """

    agent = Agent(
        agent_id=agent_id,
        agent_token_hash=agent_token_hash,
        agent_token_encrypted=agent_token_encrypted,
        name="",
        host=None,
         # Ambiente administrativo definido no Control Room.
        environment=environment,
        port=port,
        rpa_directory=rpa_directory,
        status="pending",
    )

    db.add(agent)

    return agent
def listar_execucoes_running_agent(
    db: Session,
    agent_id: str,
):
    """
    Retorna execuções atualmente marcadas como running
    para determinado Agent.
    """

    return (
        db.query(Execution)
        .filter(
            Execution.agent_id == agent_id,
            Execution.status == "running",
        )
        .all()
    )


def desativar_agent(agent):
    """
    Executa o soft delete do Agent.

    Não realiza commit.
    """

    agent.is_active = 0


def atualizar_agent_registrado(
    agent,
    *,
    name: str,
    host: str,
    port: int,
    rpa_directory: str,
):
    """
    Atualiza os dados descobertos durante o registro do Agent.

    Não realiza commit.
    """

    agent.name = name
    agent.host = host
    agent.port = port
    agent.rpa_directory = rpa_directory
    agent.status = "online"

    return agent


# ============================================================
# ALTERAR AMBIENTE DO AGENT
# ============================================================

def atualizar_ambiente_agent(
    agent,
    *,
    environment: str,
):
    """
    Atualiza somente o ambiente operacional do Agent.

    O repository não realiza commit.
    A transação continua sendo responsabilidade do service.
    """

    agent.environment = environment

    return agent