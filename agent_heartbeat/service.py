# ============================================================
# AGENT HEARTBEAT SERVICE
# ============================================================
#
# Regra de negócio responsável pelo processamento do heartbeat
# enviado pelos Agents ao Control Room.
#
# Responsabilidades:
#
# - localizar o Agent;
# - criar automaticamente o Agent quando necessário;
# - atualizar dados de comunicação;
# - atualizar informações da sessão Windows;
# - marcar o Agent como online;
# - atualizar last_heartbeat;
# - detectar mudança de host;
# - persistir as alterações;
# - registrar logs técnicos.
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - executa Depends();
# - autentica agent_token;
# - define schemas Pydantic.
#
# ============================================================

# ============================================================
# DEPENDÊNCIAS PADRÃO
# ============================================================

from datetime import datetime
import logging

from database import SessionLocal
from models import Agent

from schemas.agent_heartbeat import (
    AgentHeartbeatRequest,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# PROCESSAR HEARTBEAT
# ============================================================

def processar_agent_heartbeat_service(
    request: AgentHeartbeatRequest,
):
    """
    Processa o heartbeat recebido de um Agent.

    Parâmetros
    ----------
    request:
        Payload validado pelo schema AgentHeartbeatRequest.

    Comportamento
    -------------
    O Agent deve ter sido previamente provisionado pelo
    Control Room e autenticado através do agent_token.

    O heartbeat atualiza seus dados de comunicação, informações
    da sessão Windows, last_heartbeat e força seu status para
    "online".

    O heartbeat não é responsável pelo cadastro ou pela geração
    de credenciais de novos Agents.

    Observação
    ----------
    A autenticação e a comparação entre o Agent autenticado
    e request.agent_id continuam sendo responsabilidade da
    camada HTTP, exatamente antes da chamada deste service.
    """

    # ========================================================
    # SESSÃO DO BANCO
    # ========================================================

    db = SessionLocal()

    try:

        # ====================================================
        # LOCALIZA O AGENT
        # ====================================================

        agent = (
            db.query(Agent)
            .filter(
                Agent.agent_id == request.agent_id
            )
            .first()
        )

        # ====================================================
        # PROTEÇÃO DEFENSIVA - AGENT NÃO ENCONTRADO
        # ====================================================
        #
        # No fluxo normal este cenário não deve ocorrer.
        #
        # Antes de chegar ao service, o router executa:
        #
        #     get_agent_atual
        #
        # Essa dependency autentica o agent_token consultando
        # previamente o próprio Agent no banco.
        #
        # Além disso, o router confirma:
        #
        #     agent_autenticado.agent_id == request.agent_id
        #
        # Portanto, quando chegamos aqui, o Agent já deveria
        # existir.
        #
        # Mantemos esta verificação como proteção contra uma
        # eventual inconsistência entre autenticação e banco,
        # mas o heartbeat NÃO cria novos Agents.
        #
        # O provisionamento é responsabilidade de POST /agents,
        # que gera previamente o agent_id e o agent_token.
        # ====================================================

        if not agent:

            logger.warning(
                "Agent autenticado não encontrado durante processamento do heartbeat",
                extra={
                    "event": "agent_heartbeat_agent_not_found",
                    "agent_id": request.agent_id,
                },
            )

            return {
                "status": "error",
                "message": "Agent não encontrado.",
                "agent_id": request.agent_id,
            }


        # ====================================================
        # AGENT JÁ CADASTRADO
        # ====================================================


        # ====================================================
        # AGENT NOVO
        # ====================================================
        
        # ====================================================
        # AGENT JÁ CADASTRADO
        # ====================================================

        # Verifica se o host/IP informado mudou desde o
        # heartbeat anterior.
        ip_mudou = (
            agent.host != request.host
        )


        # ====================================================
        # AGENT VOLTOU A FICAR ONLINE
        # ====================================================

        if agent.status == "offline":

            logger.info(
                "Agent voltou a ficar online",
                extra={
                    "event": "agent_back_online",
                    "agent_id": agent.agent_id,
                    "agent_name": request.name,
                    "agent_host": request.host,
                    "agent_port": request.port,
                },
            )


        # ====================================================
        # ATUALIZA DADOS DO AGENT
        # ====================================================

        agent.name = request.name

        agent.host = request.host

        agent.port = request.port

        agent.rpa_directory = request.rpa_directory


        # ====================================================
        # ATUALIZA SESSÃO WINDOWS
        # ====================================================

        agent.session_status = request.session_status

        agent.username = request.username


        # ====================================================
        # STATUS DE COMUNICAÇÃO
        # ====================================================
        #
        # O recebimento do heartbeat significa que o Agent
        # está online.
        #
        # Preservamos o comportamento original e NÃO utilizamos
        # request.status nesta atribuição.
        # ====================================================

        agent.status = "online"


        # ====================================================
        # ÚLTIMO HEARTBEAT
        # ====================================================

        agent.last_heartbeat = datetime.now()


        # ====================================================
        # PERSISTÊNCIA
        # ====================================================

        db.commit()

        db.refresh(
            agent
        )


        # ====================================================
        # RETORNO
        # ====================================================

        return {
            "status": "success",
            "message": (
                "Agent atualizado automaticamente"
                if ip_mudou
                else "Heartbeat recebido"
            ),
            "created": False,
            "ip_changed": ip_mudou,
            "agent": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "host": agent.host,
                "port": agent.port,
                "rpa_directory": agent.rpa_directory,
                "status": agent.status,
            },
        }


    # ========================================================
    # ERRO
    # ========================================================

    except Exception as error:

        # Desfaz alterações pendentes da transação.
        db.rollback()


        logger.exception(
            "Erro ao processar heartbeat do Agent",
            extra={
                "event": "agent_heartbeat_processing_failed",
                "agent_id": request.agent_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )


        # Preservamos o contrato original: falhas internas
        # retornam um payload status="error" em vez de levantar
        # uma HTTPException.
        return {
            "status": "error",
            "message": (
                "Não foi possível processar o heartbeat do Agent"
            ),
            "agent_id": request.agent_id,
            "error": str(error),
        }


    # ========================================================
    # FECHA BANCO
    # ========================================================

    finally:

        db.close()