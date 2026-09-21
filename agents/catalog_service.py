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