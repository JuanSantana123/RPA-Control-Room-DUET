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


    # ========================================================
    # USUÁRIO WINDOWS DE EXECUÇÃO
    # ========================================================
    #
    # Identifica a conta Windows que deverá executar
    # automações Desktop neste Agent.
    #
    # Estes campos não armazenam senha.
    # A senha será tratada separadamente pelo Vault.
    #
    # Mantemos ambos opcionais nesta etapa para preservar
    # compatibilidade com fluxos existentes de criação.
    # ========================================================

    execution_username: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Usuário Windows configurado para executar "
            "automações Desktop neste Agent."
        ),
    )

    execution_domain: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Domínio Windows ou nome da máquina associado "
            "ao usuário de execução."
        ),
    )


# ============================================================
# ============================================================
# ALTERAÇÃO DO USUÁRIO WINDOWS DE EXECUÇÃO
# ============================================================

class AgentExecutionUserUpdateRequest(BaseModel):
    """
    Configura a identidade Windows utilizada para executar
    automações Desktop em determinado Agent.

    A senha não faz parte deste contrato.
    A credencial será obtida posteriormente através do Vault.
    """

    execution_username: str = Field(
        ...,
        min_length=1,
        description=(
            "Usuário Windows que deverá executar "
            "automações Desktop."
        ),
    )

    execution_domain: str = Field(
        ...,
        min_length=1,
        description=(
            "Domínio Windows ou nome da máquina ao qual "
            "pertence o usuário de execução."
        ),
    )


# ============================================================
# ALTERAÇÃO DA CREDENCIAL WINDOWS DE EXECUÇÃO
# ============================================================

class AgentExecutionCredentialUpdateRequest(BaseModel):
    """
    Associa ao Agent uma Credencial de Dispositivo existente
    no Vault do DUET.

    O Agent não recebe nem armazena senha nesta configuração.

    Apenas o identificador da credencial é persistido:

        execution_credential_id

    A validação de que a credencial pertence ao escopo
    "device" e ao tipo "windows" é responsabilidade da
    camada de serviço, não deste schema.
    """

    credential_id: int = Field(
        ...,
        gt=0,
        description=(
            "ID da Credencial de Dispositivo Windows que será "
            "utilizada para autenticar a sessão de execução."
        ),
    )
    # ============================================================
    # ALTERAÇÃO DA CREDENCIAL WINDOWS DE EXECUÇÃO
    # ============================================================

    class AgentExecutionCredentialUpdateRequest(BaseModel):
        """
        Associa ao Agent uma Credencial de Dispositivo existente
        no Vault do DUET.

        O Agent não recebe nem armazena senha nesta configuração.

        Apenas o identificador da credencial é persistido:

            execution_credential_id

        A validação de que a credencial pertence ao escopo
        "device" e ao tipo "windows" é responsabilidade da
        camada de serviço, não deste schema.
        """

        credential_id: int = Field(
            ...,
            gt=0,
            description=(
                "ID da Credencial de Dispositivo Windows que será "
                "utilizada para autenticar a sessão de execução."
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


# ============================================================
# ALTERAÇÃO DE DISPLAY DO AGENT
# ============================================================

# ============================================================
# ALTERAÇÃO DE DISPLAY DO AGENT
# ============================================================

class AgentDisplayUpdateRequest(BaseModel):
    """
    Configuração de display desejada para um Agent.

    O Control Room persiste a resolução escolhida pelo usuário.

    IMPORTANTE:
    A validação definitiva de suporte da resolução pertence
    ao próprio Agent, pois somente ele conhece os modos de
    vídeo disponibilizados pelo Windows/driver da máquina.
    """

    width: int = Field(
        ...,
        gt=0,
        description="Largura desejada da área de trabalho em pixels.",
    )

    height: int = Field(
        ...,
        gt=0,
        description="Altura desejada da área de trabalho em pixels.",
    )

    scale: int = Field(
        default=100,
        gt=0,
        description="Escala de exibição desejada em percentual.",
    )