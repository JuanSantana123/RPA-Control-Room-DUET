# ============================================================
# SERVICE - CATÁLOGO DE AGENTS
# ============================================================
#
# Regras de negócio relacionadas a:
#
# - listagem;
# - consulta;
# - criação;
# - exclusão lógica.
#
# Comunicação HTTP com o Agent não pertence a este módulo.
# ============================================================

import logging
import secrets

from sqlalchemy.orm import Session

from schemas.agents import AgentCreateRequest

from agents.repository import (
    atualizar_ambiente_agent,
    atualizar_display_agent,

    # Atualiza a identidade Windows configurada para
    # execução de automações Desktop.
    atualizar_usuario_execucao_agent,

    buscar_agent_por_id,
    criar_agent,
    desativar_agent,
    listar_agents_ativos,
)

from agents.serializers import (
    serializar_agent_consulta,
    serializar_agent_criado,
    serializar_agent_execucao,
    serializar_agent_lista,
)
# ============================================================
# SEGURANÇA DO TOKEN DO AGENT
# ============================================================
#
# O token é gerado em plaintext somente em memória.
# Antes da persistência, produzimos:
#
# - hash: utilizado para autenticação/lookup;
# - ciphertext: utilizado quando o Control Room precisa
#   recuperar o token original.
#
# O plaintext não será persistido em novos Agents.
# ============================================================

from agents.token_security import proteger_agent_token

logger = logging.getLogger("control_room")


def listar_agents_service(db: Session):
    """
    Lista todos os Agents ativos para gerenciamento.
    """

    agents = listar_agents_ativos(db)

    return {
        "status": "success",
        "total": len(agents),
        "agents": [
            serializar_agent_lista(agent)
            for agent in agents
        ],
    }


def listar_agents_disponiveis_execucao_service(
    db: Session,
):
    """
    Lista Agents ativos que podem aparecer na seleção
    de uma execução manual.
    """

    agents = listar_agents_ativos(db)

    return {
        "status": "success",
        "total": len(agents),
        "agents": [
            serializar_agent_execucao(agent)
            for agent in agents
        ],
    }


def consultar_agent_service(
    agent_id: str,
    db: Session,
):
    """
    Consulta um Agent específico.
    """

    agent = buscar_agent_por_id(
        db,
        agent_id,
    )

    if not agent:
        return {
            "status": "error",
            "message": "Agent não encontrado",
            "agent_id": agent_id,
        }

    return {
        "status": "success",
        "agent": serializar_agent_consulta(agent),
    }


def criar_agent_service(
    request: AgentCreateRequest,
    db: Session,
):
    """
    Cria o cadastro inicial de um Agent.

    Gera:
    - agent_id;
    - agent_token.

    O token permanece armazenado no Control Room e não é
    devolvido neste endpoint.
    """

    try:
        agent_id = (
            f"AGENT-{secrets.token_hex(4).upper()}"
        )

        # ====================================================
        # CREDENCIAL DO AGENT
        # ====================================================
        #
        # O token original nasce somente em memória.
        #
        # proteger_agent_token() devolve:
        #
        # 1. hash determinístico para autenticação;
        # 2. ciphertext Fernet recuperável pelo Control Room.
        #
        # O plaintext NÃO será enviado ao repository.
        # ====================================================

        agent_token = secrets.token_urlsafe(32)

        (
            agent_token_hash,
            agent_token_encrypted,
        ) = proteger_agent_token(
            agent_token
        )

        agent = criar_agent(
            db,
            agent_id=agent_id,
            agent_token_hash=agent_token_hash,
            agent_token_encrypted=agent_token_encrypted,

            # Ambiente escolhido administrativamente durante
            # a criação do Agent no Control Room.
            environment=request.environment,

            port=request.port,
            rpa_directory=request.rpa_directory,

            # Identidade Windows configurada para execução
            # de automações Desktop neste Agent.
            #
            # Pode permanecer None para preservar Agents
            # criados antes desta funcionalidade.
            execution_username=request.execution_username,
            execution_domain=request.execution_domain,
        )

        db.commit()
        db.refresh(agent)

        logger.info(
            "Agent criado no Control Room",
            extra={
                "event": "agent_created",
                "agent_id": agent.agent_id,
                "agent_port": agent.port,
            },
        )

        return {
            "status": "success",
            "message": "Agent criado com sucesso.",
            "agent": serializar_agent_criado(agent),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro ao criar Agent no Control Room",
            extra={
                "event": "agent_creation_failed",
                "agent_port": request.port,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        # O detalhe técnico já foi registrado pelo logger acima.
        # A API retorna somente uma mensagem controlada para não
        # expor informações internas do Control Room.
        return {
            "status": "error",
            "message": "Não foi possível criar o Agent.",
        }


def excluir_agent_service(
    agent_id: str,
    db: Session,
):
    """
    Executa exclusão lógica de um Agent.

    O registro permanece no banco para preservar histórico
    de execuções relacionadas ao Agent.
    """

    try:
        agent = buscar_agent_por_id(
            db,
            agent_id,
        )

        if not agent:

            logger.warning(
                "Tentativa de excluir Agent inexistente",
                extra={
                    "event": "agent_delete_not_found",
                    "agent_id": agent_id,
                },
            )

            return {
                "status": "error",
                "message": "Agent não encontrado",
                "agent_id": agent_id,
            }

        agent_name = agent.name
        agent_host = agent.host
        agent_port = agent.port

        desativar_agent(agent)

        db.commit()

        logger.info(
            "Agent removido do Control Room",
            extra={
                "event": "agent_deleted",
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_host": agent_host,
                "agent_port": agent_port,
            },
        )

        return {
            "status": "success",
            "message": "Agent removido do Control Room",
            "agent_id": agent_id,
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro ao excluir Agent do Control Room",
            extra={
                "event": "agent_delete_failed",
                "agent_id": agent_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        # O erro técnico permanece disponível somente nos logs.
        return {
            "status": "error",
            "message": "Não foi possível remover o Agent",
            "agent_id": agent_id,
        }


# ============================================================
# ALTERAR AMBIENTE DO AGENT
# ============================================================

def alterar_ambiente_agent_service(
    agent_id: str,
    environment: str,
    db: Session,
):
    """
    Altera administrativamente o ambiente operacional
    de um Agent existente.

    Nesta etapa a alteração é apenas classificatória.

    Ainda NÃO:
    - bloqueia execuções;
    - altera Scheduler;
    - altera Robots;
    - altera configuração instalada no Agent.
    """

    try:

        agent = buscar_agent_por_id(
            db,
            agent_id,
        )

        if not agent or agent.is_active != 1:

            return {
                "status": "error",
                "message": "Agent não encontrado.",
                "agent_id": agent_id,
            }

        atualizar_ambiente_agent(
            agent,
            environment=environment,
        )

        db.commit()
        db.refresh(agent)

        logger.info(
            "Ambiente do Agent alterado",
            extra={
                "event": "agent_environment_updated",
                "agent_id": agent.agent_id,
                "agent_environment": agent.environment,
            },
        )

        return {
            "status": "success",
            "message": "Ambiente do Agent alterado com sucesso.",
            "agent": serializar_agent_consulta(agent),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro ao alterar ambiente do Agent",
            extra={
                "event": "agent_environment_update_failed",
                "agent_id": agent_id,
                "error_type": type(error).__name__,
            },
        )

        return {
            "status": "error",
            "message": (
                "Não foi possível alterar o ambiente do Agent."
            ),
            "agent_id": agent_id,
        }


# ============================================================
# ALTERAR DISPLAY DO AGENT
# ============================================================

def alterar_display_agent_service(
    agent_id: str,
    width: int,
    height: int,
    scale: int,
    db: Session,
):
    """
    Persiste a configuração de display desejada para o Agent.

    Nesta camada não alteramos fisicamente a resolução do Windows.
    Essa responsabilidade pertence ao RPA-Agent.
    """

    try:

        agent = buscar_agent_por_id(
            db,
            agent_id,
        )

        if not agent or agent.is_active != 1:

            return {
                "status": "error",
                "message": "Agent não encontrado.",
                "agent_id": agent_id,
            }

        atualizar_display_agent(
            agent,
            width=width,
            height=height,
            scale=scale,
        )

        db.commit()
        db.refresh(agent)

        logger.info(
            "Configuração de display do Agent alterada",
            extra={
                "event": "agent_display_updated",
                "agent_id": agent.agent_id,
                "display_width": agent.display_width,
                "display_height": agent.display_height,
                "display_scale": agent.display_scale,
            },
        )

        return {
            "status": "success",
            "message": (
                "Configuração de display do Agent "
                "alterada com sucesso."
            ),
            "agent": serializar_agent_consulta(agent),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro ao alterar configuração de display do Agent",
            extra={
                "event": "agent_display_update_failed",
                "agent_id": agent_id,
                "error_type": type(error).__name__,
            },
        )

        return {
            "status": "error",
            "message": (
                "Não foi possível alterar a configuração "
                "de display do Agent."
            ),
            "agent_id": agent_id,
        }


# ============================================================
# ALTERAR USUÁRIO WINDOWS DE EXECUÇÃO
# ============================================================

def alterar_usuario_execucao_agent_service(
    agent_id: str,
    execution_username: str,
    execution_domain: str,
    db: Session,
):
    """
    Configura a identidade Windows utilizada para executar
    automações Desktop em determinado Agent.

    Parameters
    ----------
    agent_id:
        Identificador do Agent que será configurado.

    execution_username:
        Nome da conta Windows utilizada para execução.

    execution_domain:
        Domínio Windows ou nome da máquina associado à conta.

    db:
        Sessão SQLAlchemy fornecida pela camada HTTP.

    IMPORTANTE
    ----------
    A senha NÃO pertence a esta configuração.

    Usuário e domínio identificam a conta.
    A credencial de autenticação será tratada posteriormente
    através do Vault.
    """

    try:

        agent = buscar_agent_por_id(
            db,
            agent_id,
        )

        # ----------------------------------------------------
        # VALIDA AGENT
        # ----------------------------------------------------

        if not agent or agent.is_active != 1:

            return {
                "status": "error",
                "message": "Agent não encontrado.",
                "agent_id": agent_id,
            }

        # ----------------------------------------------------
        # NORMALIZA A IDENTIDADE WINDOWS
        # ----------------------------------------------------
        #
        # Remove espaços acidentais nas extremidades.
        #
        # Não alteramos maiúsculas/minúsculas porque queremos
        # preservar a forma administrativa informada pelo
        # usuário no Control Room.
        # ----------------------------------------------------

        username_normalizado = execution_username.strip()
        domain_normalizado = execution_domain.strip()

        if not username_normalizado:

            return {
                "status": "error",
                "message": (
                    "Usuário Windows de execução não pode "
                    "ser vazio."
                ),
                "agent_id": agent_id,
            }

        if not domain_normalizado:

            return {
                "status": "error",
                "message": (
                    "Domínio Windows de execução não pode "
                    "ser vazio."
                ),
                "agent_id": agent_id,
            }

        # ----------------------------------------------------
        # PERSISTE CONFIGURAÇÃO
        # ----------------------------------------------------

        atualizar_usuario_execucao_agent(
            agent,
            execution_username=username_normalizado,
            execution_domain=domain_normalizado,
        )

        db.commit()
        db.refresh(agent)

        logger.info(
            "Usuário Windows de execução do Agent alterado",
            extra={
                "event": "agent_execution_user_updated",
                "agent_id": agent.agent_id,
                "execution_username": agent.execution_username,
                "execution_domain": agent.execution_domain,
            },
        )

        return {
            "status": "success",
            "message": (
                "Usuário Windows de execução configurado "
                "com sucesso."
            ),
            "agent": serializar_agent_consulta(agent),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro ao alterar usuário Windows de execução do Agent",
            extra={
                "event": "agent_execution_user_update_failed",
                "agent_id": agent_id,
                "error_type": type(error).__name__,
            },
        )

        return {
            "status": "error",
            "message": (
                "Não foi possível alterar o usuário Windows "
                "de execução do Agent."
            ),
            "agent_id": agent_id,
        }