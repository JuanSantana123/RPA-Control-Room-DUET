# ============================================================
# DUET CORE - AGENT EXECUTION CREDENTIAL SERVICE
# ============================================================
#
# Serviço responsável por associar uma Credencial de
# Dispositivo Windows a um Agent.
#
# RESPONSABILIDADE:
#
# - validar se o Agent existe e está ativo;
# - localizar a VaultCredential informada;
# - validar se a credencial pertence ao escopo "device";
# - validar se a credencial é do tipo "windows";
# - persistir somente a referência execution_credential_id;
# - controlar commit / rollback;
# - registrar auditoria sem expor segredo.
#
# ESTE SERVICE NÃO:
#
# - descriptografa senha;
# - lê VaultField;
# - envia credencial ao Agent;
# - autentica sessão Windows;
# - chama Session Broker;
# - contém rota HTTP;
# - altera execution_username / execution_domain.
#
# A senha será resolvida somente no fluxo de execução,
# em memória, quando realmente houver necessidade de
# autenticar a sessão Windows.
# ============================================================

import logging

from sqlalchemy.orm import Session

from models import VaultCredential

from agents.repository import (
    atualizar_credencial_execucao_agent,
    buscar_agent_por_id,
)


# ============================================================
# CONSTANTES DO DOMÍNIO
# ============================================================

DEVICE_SCOPE = "device"
WINDOWS_CREDENTIAL_TYPE = "windows"


# ============================================================
# LOGGER
# ============================================================
#
# Nunca registrar:
#
# - password;
# - ciphertext;
# - VaultField.value;
# - material descriptografado.
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# ASSOCIAR CREDENCIAL DE EXECUÇÃO AO AGENT
# ============================================================

def associar_credencial_execucao_agent_service(
    *,
    agent_id: str,
    credential_id: int,
    db: Session,
):
    """
    Associa uma Credencial de Dispositivo Windows a um Agent.

    Parameters
    ----------
    agent_id:
        Identificador lógico do Agent.

    credential_id:
        ID da VaultCredential que deverá ser utilizada pelo
        Agent no fluxo de autenticação Windows.

    db:
        Sessão SQLAlchemy fornecida pela camada HTTP.

    Segurança
    ---------
    Este método trabalha somente com metadados da credencial.

    Nenhum VaultField é consultado e nenhum segredo é
    descriptografado nesta etapa.
    """

    try:

        # ====================================================
        # 1. LOCALIZA O AGENT
        # ====================================================

        agent = buscar_agent_por_id(
            db,
            agent_id,
        )


        if (
            not agent
            or
            agent.is_active != 1
        ):

            return {
                "status": "error",
                "message": "Agent não encontrado.",
                "agent_id": agent_id,
            }


        # ====================================================
        # 2. LOCALIZA A CREDENCIAL
        # ====================================================
        #
        # Consultamos somente VaultCredential.
        #
        # NÃO carregamos VaultField porque a associação não
        # precisa conhecer domínio, usuário ou senha.
        # ====================================================

        credential = (
            db.query(
                VaultCredential
            )
            .filter(
                VaultCredential.id == credential_id
            )
            .first()
        )


        if not credential:

            return {
                "status": "error",
                "message": (
                    "Credencial de dispositivo não encontrada."
                ),
                "agent_id": agent_id,
                "credential_id": credential_id,
            }


        # ====================================================
        # 3. VALIDA O ESCOPO
        # ====================================================
        #
        # Impede que credenciais genéricas de Automação sejam
        # associadas à autenticação Windows de um Device.
        # ====================================================

        if (
            credential.scope !=
            DEVICE_SCOPE
        ):

            return {
                "status": "error",
                "message": (
                    "A credencial informada não pertence ao "
                    "escopo de dispositivo."
                ),
                "agent_id": agent_id,
                "credential_id": credential_id,
            }


        # ====================================================
        # 4. VALIDA O TIPO
        # ====================================================

        if (
            credential.credential_type !=
            WINDOWS_CREDENTIAL_TYPE
        ):

            return {
                "status": "error",
                "message": (
                    "A credencial informada não é uma "
                    "credencial Windows."
                ),
                "agent_id": agent_id,
                "credential_id": credential_id,
            }


        # ====================================================
        # 5. PERSISTE SOMENTE A REFERÊNCIA
        # ====================================================
        #
        # O repository não conhece Vault nem executa commit.
        # Neste ponto a credencial já foi validada.
        # ====================================================

        atualizar_credencial_execucao_agent(
            agent,
            execution_credential_id=credential.id,
        )


        # ====================================================
        # 6. COMMIT
        # ====================================================

        db.commit()

        db.refresh(
            agent
        )


        # ====================================================
        # 7. AUDITORIA
        # ====================================================
        #
        # Registramos somente IDs e metadados seguros.
        # ====================================================

        logger.info(
            "Credencial Windows de execução associada ao Agent",
            extra={
                "event": (
                    "agent_execution_credential_updated"
                ),
                "agent_id": agent.agent_id,
                "execution_credential_id": (
                    agent.execution_credential_id
                ),
                "credential_name": credential.name,
            },
        )


        # ====================================================
        # 8. RETORNO
        # ====================================================
        #
        # Nenhum segredo é retornado.
        # ====================================================

        return {
            "status": "success",
            "message": (
                "Credencial Windows de execução associada "
                "ao Agent com sucesso."
            ),
            "agent_id": agent.agent_id,
            "execution_credential_id": (
                agent.execution_credential_id
            ),
            "credential": {
                "id": credential.id,
                "name": credential.name,
                "scope": credential.scope,
                "credential_type": (
                    credential.credential_type
                ),
            },
        }


    except Exception as error:

        # ====================================================
        # ROLLBACK
        # ====================================================

        db.rollback()


        # ====================================================
        # LOG CONTROLADO
        # ====================================================

        logger.exception(
            "Erro ao associar credencial Windows ao Agent",
            extra={
                "event": (
                    "agent_execution_credential_update_failed"
                ),
                "agent_id": agent_id,
                "credential_id": credential_id,
                "error_type": type(error).__name__,
            },
        )


        return {
            "status": "error",
            "message": (
                "Não foi possível associar a credencial "
                "Windows ao Agent."
            ),
            "agent_id": agent_id,
            "credential_id": credential_id,
        }
