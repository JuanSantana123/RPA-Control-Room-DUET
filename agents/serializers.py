# ============================================================
# SERIALIZERS - AGENTS
# ============================================================
#
# Centraliza a transformação das entidades SQLAlchemy em
# estruturas que podem ser retornadas pela API.
#
# Nenhum serializer expõe agent_token.
# ============================================================


def serializar_agent_lista(agent):
    """
    Serializa um Agent para a tela administrativa.
    """

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "environment": agent.environment,
        "host": agent.host,
        "port": agent.port,
        "rpa_directory": agent.rpa_directory,
        "status": agent.status,
        "session_status": agent.session_status,
        "username": agent.username,
    }


def serializar_agent_execucao(agent):
    """
    Serializa um Agent para seleção durante execução manual.

    O agent_token deliberadamente não faz parte da resposta.
    """

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "environment": agent.environment,
        "host": agent.host,
        "port": agent.port,
        "status": agent.status,
        "session_status": agent.session_status,
        "username": agent.username,
    }


def serializar_agent_consulta(agent):
    """
    Serializa os dados retornados pela consulta individual.
    """

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "environment": agent.environment,
        "host": agent.host,
        "port": agent.port,
        "rpa_directory": agent.rpa_directory,
        "status": agent.status,
    }


def serializar_agent_criado(agent):
    """
    Serializa o retorno da criação inicial do Agent.
    """

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "environment": agent.environment,
        "port": agent.port,
        "rpa_directory": agent.rpa_directory,
        "status": agent.status,
    }