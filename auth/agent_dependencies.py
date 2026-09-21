from fastapi import Header, HTTPException

from database import SessionLocal
from models import Agent
# Calcula a impressão digital do token recebido.
# O token plaintext não é utilizado para consulta no banco.
from agents.token_security import calcular_hash_agent_token

def get_agent_atual(
    authorization: str | None = Header(default=None)
):
    """
    Valida o token enviado pelo Agent.

    O Agent deve enviar:
        Authorization: Bearer <agent_token>
    """

    # Verifica se o header Authorization foi enviado.
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token do Agent não informado."
        )

    # Verifica o formato esperado:
    # Authorization: Bearer <token>
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Formato do token do Agent inválido."
        )

    # Remove o prefixo "Bearer ".
    agent_token = authorization[7:].strip()

    if not agent_token:
        raise HTTPException(
            status_code=401,
            detail="Token do Agent não informado."
        )

    db = SessionLocal()

    try:

        # Procura um Agent que possua esse token.
        # --------------------------------------------------------
        # LOCALIZA SOMENTE AGENT ATIVO
        # --------------------------------------------------------
        #
        # O agent_token autentica a identidade técnica do Agent.
        #
        # A validação de is_active faz parte da mesma decisão de
        # autenticação: um Agent removido logicamente não pode
        # continuar acessando endpoints machine-to-machine.
        #
        # Dessa forma, o soft delete também funciona como
        # revogação operacional imediata da autenticação.
        # --------------------------------------------------------

        # O token recebido existe somente em memória.
        # A consulta ao banco utiliza exclusivamente seu hash.
        agent_token_hash = calcular_hash_agent_token(
            agent_token
        )

        agent = (
            db.query(Agent)
            .filter(
                Agent.agent_token_hash == agent_token_hash,
                Agent.is_active == 1,
            )
            .first()
        )

        # Token inexistente OU pertencente a Agent desativado.
        #
        # Mantemos a mesma resposta nos dois casos para não
        # revelar ao cliente se determinada credencial existe.
        if not agent:
            raise HTTPException(
                status_code=401,
                detail="Token do Agent inválido."
            )

        # Token não pertence a nenhum Agent.
        if not agent:
            raise HTTPException(
                status_code=401,
                detail="Token do Agent inválido."
            )

        # Retorna o Agent autenticado.
        return agent

    finally:

        db.close()