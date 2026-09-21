# ============================================================
# SCHEMAS - AGENTS
# ============================================================
#
# Contratos HTTP utilizados pelas APIs de Agents.
#
# Este módulo contém somente validação/estrutura dos dados
# recebidos pela API. Não acessa banco nem executa regras
# de negócio.
# ============================================================

from typing import Literal

from pydantic import BaseModel, Field


class AgentRegisterRequest(BaseModel):
    """
    Dados necessários para registrar/conectar um Agent
    previamente criado no Control Room.
    """

    agent_id: str = Field(
        ...,
        min_length=1,
        description="Identificador do Agent criado no Control Room.",
    )

    host: str = Field(
        ...,
        min_length=1,
        description="IP ou hostname utilizado para acessar o Agent.",
    )

    port: int = Field(
        ...,
        ge=1,
        le=65535,
        description="Porta HTTP utilizada pelo Agent.",
    )


class AgentCreateRequest(BaseModel):
    """
    Dados necessários para criar o cadastro inicial de um Agent.
    """
    # Ambiente operacional atribuído ao Agent.
    #
    # Literal impede que a API aceite valores arbitrários.
    # Somente os dois ambientes oficiais do DUET são válidos.
    environment: Literal[
        "development",
        "production",
    ] = Field(
        default="development",
        description=(
            "Ambiente operacional do Agent: "
            "'development' ou 'production'."
        ),
    )
    port: int = Field(
        ...,
        ge=1,
        le=65535,
        description="Porta HTTP utilizada pelo Agent na máquina.",
    )

    rpa_directory: str = Field(
        ...,
        min_length=1,
        description=(
            "Diretório onde os pacotes dos RPAs serão "
            "armazenados na máquina do Agent."
        ),
    )


# ============================================================
# ALTERAÇÃO DE AMBIENTE DO AGENT
# ============================================================

class AgentEnvironmentUpdateRequest(BaseModel):
    """
    Dados permitidos para alteração administrativa do ambiente
    operacional de um Agent existente.
    """

    environment: Literal[
        "development",
        "production",
    ] = Field(
        ...,
        description=(
            "Novo ambiente operacional do Agent: "
            "'development' ou 'production'."
        ),
    )