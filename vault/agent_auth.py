# ============================================================
# VAULT - AGENT AUTH
# ============================================================
#
# Autenticação técnica dos Agents que acessam recursos do Vault.
#
# IMPORTANTE:
#
# O Agent NÃO possui uma sessão de usuário do Control Room.
#
# Portanto este módulo:
#
# - NÃO utiliza get_usuario_atual;
# - NÃO utiliza cookie de sessão;
# - NÃO representa um usuário humano;
# - autentica exclusivamente através do agent_token.
#
# O token é recebido através de:
#
#     Authorization: Bearer <agent_token>
#
# Depois da autenticação, retornamos o registro Agent associado
# ao token. A autorização sobre uma execução/credencial será
# responsabilidade do service específico do Agent.
# ============================================================

from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from database import SessionLocal
from models import Agent
# Utilizado para autenticar o Agent sem consultar
# o token plaintext persistido.
from agents.token_security import calcular_hash_agent_token

# ============================================================
# HTTP BEARER
# ============================================================
#
# Define o mecanismo de autenticação utilizado pelo Agent.
#
# auto_error=False:
#     impede o HTTPBearer de gerar automaticamente a resposta
#     de erro.
#
# Isso é importante porque queremos preservar exatamente as
# mensagens HTTP existentes no backend atual.
# ============================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)


# ============================================================
# VALIDAR TOKEN DO AGENT
# ============================================================

def validar_agent_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    """
    Valida o agent_token enviado pelo Agent.

    Header esperado
    ---------------

        Authorization: Bearer <agent_token>

    Retorno
    -------

    Agent
        Registro do Agent associado ao token informado.

    Segurança
    ---------

    O token identifica tecnicamente a máquina/Agent.

    Ele NÃO representa o usuário que iniciou uma execução.

    O usuário responsável será posteriormente descoberto através
    da Execution associada ao execution_id.
    """

    # --------------------------------------------------------
    # AUTHORIZATION NÃO INFORMADO
    # --------------------------------------------------------
    #
    # Como HTTPBearer está configurado com auto_error=False,
    # credentials será None quando o header não for enviado.
    # --------------------------------------------------------

    if credentials is None:

        raise HTTPException(
            status_code=401,
            detail="Authorization não informado.",
        )


    # --------------------------------------------------------
    # VALIDA O SCHEME
    # --------------------------------------------------------
    #
    # Mantemos esta validação explicitamente para preservar
    # exatamente o comportamento do código original.
    # --------------------------------------------------------

    if credentials.scheme.lower() != "bearer":

        raise HTTPException(
            status_code=401,
            detail="Authorization deve utilizar Bearer.",
        )


    # --------------------------------------------------------
    # RECUPERA O TOKEN
    # --------------------------------------------------------

    token = credentials.credentials


    # --------------------------------------------------------
    # CONSULTA O AGENT
    # --------------------------------------------------------
    #
    # Esta função continua abrindo sua própria SessionLocal,
    # exatamente como acontece no código atual.
    #
    # Não estamos alterando esse comportamento durante a
    # modularização.
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        # Converte a credencial recebida em uma impressão
        # digital determinística antes da consulta.
        agent_token_hash = calcular_hash_agent_token(
            token
        )

        agent = (
            db.query(Agent)
            .filter(
                Agent.agent_token_hash == agent_token_hash,
                Agent.is_active == 1,
            )
            .first()
        )


        # ----------------------------------------------------
        # TOKEN NÃO RECONHECIDO
        # ----------------------------------------------------

        if not agent:

            raise HTTPException(
                status_code=401,
                detail="Agent token inválido.",
            )


        # ----------------------------------------------------
        # AGENT AUTENTICADO
        # ----------------------------------------------------
        #
        # Retornamos o objeto Agent para que o próximo service
        # consiga validar, entre outras coisas:
        #
        #     execucao.agent_id == agent.agent_id
        #
        # ----------------------------------------------------

        return agent


    finally:

        # ----------------------------------------------------
        # GARANTE O FECHAMENTO DA SESSÃO
        # ----------------------------------------------------

        db.close()