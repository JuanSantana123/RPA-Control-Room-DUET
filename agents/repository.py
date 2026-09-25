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

    # Usuário Windows configurado para execução Desktop.
    # Mantemos opcional para preservar compatibilidade com
    # Agents criados antes desta funcionalidade.
    execution_username: str | None = None,
    execution_domain: str | None = None,
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

        # Identidade Windows que deverá ser utilizada para
        # executar automações Desktop neste Agent.
        execution_username=execution_username,
        execution_domain=execution_domain,

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


# ============================================================
# ALTERAR DISPLAY DO AGENT
# ============================================================

def atualizar_display_agent(
    agent,
    *,
    width: int,
    height: int,
    scale: int,
):
    """
    Atualiza a configuração de display desejada do Agent.

    O repository somente altera a entidade SQLAlchemy.
    Commit/rollback continuam sendo responsabilidade do service.
    """

    agent.display_width = width
    agent.display_height = height
    agent.display_scale = scale

    return agent


# ============================================================
# ALTERAR USUÁRIO WINDOWS DE EXECUÇÃO
# ============================================================

def atualizar_usuario_execucao_agent(
    agent,
    *,
    execution_username: str,
    execution_domain: str,
):
    """
    Atualiza a identidade Windows configurada para execução
    de automações Desktop neste Agent.

    Parameters
    ----------
    agent:
        Entidade SQLAlchemy do Agent que será alterada.

    execution_username:
        Nome da conta Windows utilizada para execução.

    execution_domain:
        Domínio Windows ou nome da máquina associado à conta.

    IMPORTANTE
    ----------
    Esta função NÃO recebe nem persiste senha.

    A credencial de autenticação será tratada separadamente
    pela camada de Vault.

    O repository também NÃO executa commit.
    A transação permanece responsabilidade do service.
    """

    agent.execution_username = execution_username
    agent.execution_domain = execution_domain

    return agent


# ============================================================
# ALTERAR CREDENCIAL WINDOWS DE EXECUÇÃO
# ============================================================

def atualizar_credencial_execucao_agent(
    agent,
    *,
    execution_credential_id: int,
):
    """
    Atualiza somente a referência da Credencial de Dispositivo
    utilizada pelo Agent para autenticação Windows.

    Parameters
    ----------
    agent:
        Entidade SQLAlchemy do Agent que será alterada.

    execution_credential_id:
        ID da VaultCredential associada ao Agent.

    IMPORTANTE
    ----------
    Este repository NÃO:

    - consulta o Vault;
    - valida scope;
    - valida credential_type;
    - descriptografa senha;
    - executa commit;
    - executa rollback.

    Todas essas responsabilidades pertencem às camadas
    apropriadas acima do repository.

    Aqui apenas persistimos a referência já validada.
    """

    agent.execution_credential_id = execution_credential_id

    return agent