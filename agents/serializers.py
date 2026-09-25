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
        # Identidade Windows configurada para execução Desktop.
        #
        # Estes campos não contêm senha.
        "execution_username": agent.execution_username,
        "execution_domain": agent.execution_domain,
        "session_status": agent.session_status,

        # Usuário atualmente detectado na sessão Windows.
        # Este campo é telemetria enviada pelo Agent.
        "username": agent.username,

        # Identidade Windows configurada administrativamente
        # para executar automações Desktop neste Agent.
        "execution_username": agent.execution_username,
        "execution_domain": agent.execution_domain,
        # Configuração desejada de display.
        "display_width": agent.display_width,
        "display_height": agent.display_height,
        "display_scale": agent.display_scale,
        # Último estado real informado pelo RPA-Agent.
        "display_current": (
            {
                "width": agent.display_current_width,
                "height": agent.display_current_height,
            }
            if (
                agent.display_current_width is not None
                and agent.display_current_height is not None
            )
            else None
        ),

        # Resoluções que a própria máquina informou suportar.
        "display_supported": agent.display_supported or [],
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

        # Usuário atualmente detectado na sessão Windows.
        "username": agent.username,

        # Usuário que DEVE executar as automações Desktop.
        "execution_username": agent.execution_username,
        "execution_domain": agent.execution_domain,
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

        # Identidade Windows configurada administrativamente
        # para executar automações Desktop neste Agent.
        #
        # Estes campos representam a conta que DEVE executar
        # os Robots, e não o usuário atualmente detectado
        # pela telemetria da sessão Windows.
        "execution_username": agent.execution_username,
        "execution_domain": agent.execution_domain,

        # Configuração desejada de display.
        # Configuração desejada de display.
        "display_width": agent.display_width,
        "display_height": agent.display_height,
        "display_scale": agent.display_scale,
        # Último estado real informado pelo RPA-Agent.
        "display_current": (
            {
                "width": agent.display_current_width,
                "height": agent.display_current_height,
            }
            if (
                agent.display_current_width is not None
                and agent.display_current_height is not None
            )
            else None
        ),

        # Resoluções suportadas reportadas pela própria máquina.
        "display_supported": agent.display_supported or [],
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

        # Identidade Windows configurada para execução Desktop.
        "execution_username": agent.execution_username,
        "execution_domain": agent.execution_domain,

        "status": agent.status,
    }

