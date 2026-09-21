# ============================================================
# SCHEMAS - AGENT HEARTBEAT
# ============================================================
#
# Contratos utilizados no heartbeat enviado pelos Agents
# ao Control Room.
#
# Este módulo contém somente modelos de dados.
#
# Não possui:
#
# - acesso ao banco;
# - autenticação;
# - endpoints FastAPI;
# - regras de negócio.
#
# ============================================================

from pydantic import BaseModel, Field


# ============================================================
# HEARTBEAT ENVIADO PELO AGENT
# ============================================================

class AgentHeartbeatRequest(BaseModel):
    """
    Representa o heartbeat periódico enviado por um Agent.

    O payload informa os dados atuais da VM, da instância do
    Agent e da sessão Windows.
    """

    # Identificador único do Agent.
    agent_id: str = Field(
        ...,
        min_length=1,
    )

    # Nome atualmente informado pelo Agent.
    name: str = Field(
        ...,
        min_length=1,
    )

    # IP ou hostname atual da máquina.
    host: str = Field(
        ...,
        min_length=1,
    )

    # Porta onde a API do Agent está executando.
    port: int = Field(
        ...,
        ge=1,
        le=65535,
    )

    # Diretório onde os RPAs ficam armazenados
    # na máquina do Agent.
    rpa_directory: str = Field(
        ...,
        min_length=1,
    )

    # Status enviado no payload.
    #
    # Mantemos este campo exatamente como no contrato original.
    #
    # Atualmente o processamento do heartbeat não utiliza esse
    # valor para definir o status persistido: o recebimento do
    # heartbeat força o Agent para "online".
    status: str = Field(
        default="online",
        min_length=1,
    )

    # Estado atual da sessão Windows.
    #
    # Exemplos atualmente documentados:
    #
    # - unknown
    # - ready
    # - error
    session_status: str = Field(
        default="unknown",
        min_length=1,
    )

    # Usuário atualmente associado à sessão Windows.
    username: str | None = None