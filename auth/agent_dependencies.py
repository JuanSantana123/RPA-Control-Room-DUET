from fastapi import Header, HTTPException

from database import SessionLocal
from models import Agent

# Calcula a impressão digital do token recebido.
# O token plaintext não é utilizado para consulta no banco.
from agents.token_security import calcular_hash_agent_token

from agents.observability import (
    registrar_falha_autenticacao_agent,
)


def get_agent_atual(
    authorization: str | None = Header(default=None)
):
    """
    Valida o token enviado pelo Agent.

    O Agent deve enviar:
        Authorization: Bearer <agent_token>
    """

    # ========================================================
    # HEADER AUSENTE
    # ========================================================

    if not authorization:
        registrar_falha_autenticacao_agent(
            reason="authorization_header_missing",
        )

        raise HTTPException(
            status_code=401,
            detail="Token do Agent não informado."
        )

    # ========================================================
    # FORMATO DO HEADER INVÁLIDO
    # ========================================================
    #
    # Esperado:
    #
    #     Authorization: Bearer <token>
    #
    # ========================================================

    if not authorization.startswith("Bearer "):
        registrar_falha_autenticacao_agent(
            reason="invalid_authorization_scheme",
        )

        raise HTTPException(
            status_code=401,
            detail="Formato do token do Agent inválido."
        )

    # ========================================================
    # EXTRAI TOKEN
    # ========================================================

    agent_token = authorization[7:].strip()

    # Bearer foi informado, porém sem conteúdo depois dele.
    if not agent_token:
        registrar_falha_autenticacao_agent(
            reason="agent_token_missing",
        )

        raise HTTPException(
            status_code=401,
            detail="Token do Agent não informado."
        )

    # ========================================================
    # CONSULTA AGENT
    # ========================================================

    db = SessionLocal()

    try:

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

        # ====================================================
        # TOKEN INVÁLIDO OU AGENT INATIVO
        # ====================================================
        #
        # Mantemos a mesma resposta nos dois casos para não
        # revelar ao cliente se determinada credencial existe.
        # ====================================================

        if not agent:
            registrar_falha_autenticacao_agent(
                reason="invalid_or_inactive_agent_token",
            )

            raise HTTPException(
                status_code=401,
                detail="Token do Agent inválido."
            )

        # ====================================================
        # AUTENTICAÇÃO OK
        # ====================================================
        #
        # Não geramos evento de sucesso para não poluir os logs.
        # ====================================================

        return agent

    finally:
        db.close()