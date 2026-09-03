# ============================================================
# ROUTER DE AGENTS
# ============================================================
# Centraliza consulta, heartbeat, cadastro, exclusão e monitoramento
# dos Agents. As URLs permanecem iguais às APIs existentes.
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel, Field
from database import SessionLocal
from models import Agent, Execution
from datetime import datetime, timedelta
import requests
import time
import logging


# ============================================================
# MODELO - CADASTRO MANUAL DO AGENT
# ============================================================
#
# Define os dados recebidos pelo endpoint:
#
# POST /agents/register
#
# O Control Room recebe o host e a porta do Agent
# para conseguir consultar o serviço.
# ============================================================

class AgentRegisterRequest(BaseModel):

    host: str = Field(
        ...,
        min_length=1
    )

    port: int = Field(
        ...,
        ge=1,
        le=65535
    )
    
router = APIRouter(tags=["Agents"])
logger = logging.getLogger("control_room")

# ============================================================
# LISTAR AGENTS
# ============================================================

@router.get("/agents")
def list_agents():
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        return {
            "status": "success",
            "total": len(agents),
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "host": agent.host,
                    "port": agent.port,
                    "rpa_directory": agent.rpa_directory,
                    "status": agent.status
                }
                for agent in agents
            ]
        }
    finally:
        db.close()

# ============================================================
# CONSULTAR AGENT
# ============================================================

@router.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(
            Agent.agent_id == agent_id
        ).first()

        if not agent:
            return {
                "status": "error",
                "message": "Agent não encontrado",
                "agent_id": agent_id
            }

        return {
            "status": "success",
            "agent": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "host": agent.host,
                "port": agent.port,
                "rpa_directory": agent.rpa_directory,
                "status": agent.status
            }
        }
    finally:
        db.close()

# ============================================================
# endpoint HEARTBEAT DO AGENT
# ============================================================
#
# O Agent envia periodicamente:
#
# - agent_id
# - name
# - host (IP atual)
# - port
# - rpa_directory
# - status
#
# Se o Agent já existir, atualizamos os dados.
# Se ainda não existir, criamos o cadastro.
#
# Isso permite que o IP seja alterado pelo DHCP sem
# necessidade de cadastro manual novamente.
# ============================================================

class AgentHeartbeatRequest(BaseModel):

    agent_id: str = Field(
        ...,
        min_length=1
    )

    name: str = Field(
        ...,
        min_length=1
    )

    host: str = Field(
        ...,
        min_length=1
    )

    port: int = Field(
        ...,
        ge=1,
        le=65535
    )

    rpa_directory: str = Field(
        ...,
        min_length=1
    )

    status: str = Field(
        default="online",
        min_length=1
    )


@router.post("/agents/heartbeat")
def agent_heartbeat(
    request: AgentHeartbeatRequest
):

    db = SessionLocal()

    try:

        agent = db.query(Agent).filter(
            Agent.agent_id == request.agent_id
        ).first()

        # ====================================================
        # AGENT NOVO
        # ====================================================

        if not agent:

            agent = Agent(
                agent_id=request.agent_id,
                name=request.name,
                host=request.host,
                port=request.port,
                rpa_directory=request.rpa_directory,
                status="online",
                last_heartbeat=datetime.now()
            )

            db.add(agent)

            db.commit()

            db.refresh(agent)
            logger.info(
                f"[AGENT] Agent registrado e online | "
                f"ID: {agent.agent_id} | "
                f"Nome: {agent.name} | "
                f"Host: {agent.host}:{agent.port}"
            )

            return {
                "status": "success",
                "message": "Agent registrado automaticamente",
                "created": True,
                "agent": {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "host": agent.host,
                    "port": agent.port,
                    "rpa_directory": agent.rpa_directory,
                    "status": agent.status
                }
            }


        # ====================================================
        # AGENT JÁ CADASTRADO
        # ====================================================
        #
        # Aqui está a parte importante:
        # se o IP mudou, o banco recebe o novo IP.
        #

        ip_mudou = agent.host != request.host

        # ============================================================
        # REGISTRA RETORNO DO AGENT AO ESTADO ONLINE
        # ============================================================

        if agent.status == "offline":

            logger.info(
                f"[AGENT] Agent voltou online | "
                f"ID: {agent.agent_id} | "
                f"Nome: {agent.name} | "
                f"Host: {agent.host}:{agent.port}"
            )

        agent.name = request.name
        agent.host = request.host
        agent.port = request.port
        agent.rpa_directory = request.rpa_directory
        agent.status = "online"
        agent.last_heartbeat = datetime.now()

        db.commit()

        db.refresh(agent)

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
                "status": agent.status
            }
        }


    

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível processar o heartbeat do Agent",
            "agent_id": request.agent_id,
            "error": str(error)
        }

    finally:

        db.close()

# ============================================================
# MONITORAMENTO DE AGENTS
# ============================================================
def verificar_agents_offline():

    db = SessionLocal()

    try:

        agora = datetime.now()
        limite = agora - timedelta(seconds=60)

        agents = db.query(Agent).all()

        for agent in agents:

            if (
                agent.last_heartbeat is not None
                and agent.last_heartbeat < limite
            ):

                if agent.status != "offline":

                    logger.warning(
                    f"[AGENT] Agent ficou offline | "
                    f"ID: {agent.agent_id} | "
                    f"Nome: {agent.name} | "
                    f"Host: {agent.host}:{agent.port} | "
                    f"Último heartbeat: {agent.last_heartbeat}"
                )

                    agent.status = "offline"

                    # ====================================================
                    # MARCA EXECUÇÕES PENDENTES COMO ERRO
                    # ====================================================

                    execucoes = db.query(Execution).filter(
                        Execution.agent_id == agent.agent_id,
                        Execution.status == "running"
                    ).all()

                    for execucao in execucoes:

                        execucao.status = "error"
                        execucao.finished_at = agora
                        execucao.error_message = (
                            "Agent ficou offline durante a execução"
                        )

                        print(
                            f"[EXECUÇÃO INTERROMPIDA] "
                            f"Execution #{execucao.id} | "
                            f"Agent: {agent.name}"
                        )

        db.commit()

    except Exception as error:

        db.rollback()

        print(
            f"[ERRO] Monitoramento de Agents: {error}"
        )

    finally:

        db.close()

def monitorar_agents():

    while True:

        verificar_agents_offline()

        time.sleep(10)

# ============================================================
# REGISTRAR AGENT MANUALMENTE
# ============================================================

@router.post("/agents/register")
def register_agent(
    request: AgentRegisterRequest
):

    host = request.host
    port = request.port

    base_url = f"http://{host}:{port}"


    # ========================================================
    # 1. CONSULTA HEALTH DO AGENT
    # ========================================================

    health_url = f"{base_url}/health"

    try:

        response = requests.get(
            health_url,
            timeout=5
        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Não foi possível conectar ao Agent",
            "host": host,
            "port": port,
            "error": str(error)
        }


    # ========================================================
    # 2. VALIDA HTTP
    # ========================================================

    if response.status_code != 200:

        return {
            "status": "error",
            "message": "Agent respondeu com erro no /health",
            "host": host,
            "port": port,
            "http_status": response.status_code
        }


    # ========================================================
    # 3. LÊ HEALTH
    # ========================================================

    try:

        health = response.json()

    except ValueError:

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no /health"
        }


    # ========================================================
    # 4. VALIDA STATUS DO AGENT
    # ========================================================

    if health.get("status") != "online":

        return {
            "status": "error",
            "message": "Agent não está online",
            "health": health
        }


    # ========================================================
    # 5. O AGENT PRECISA INFORMAR O ID
    # ========================================================

    agent_id = health.get("agent_id")

    if not agent_id:

        return {
            "status": "error",
            "message": "Agent não informou agent_id",
            "health": health
        }


    # ========================================================
    # 6. VERIFICA SE JÁ ESTÁ CADASTRADO
    # ========================================================


    db = SessionLocal()

    try:

        agent_existente = db.query(Agent).filter(
            Agent.agent_id == agent_id
        ).first()

    finally:

        db.close()


    if agent_existente:

        return {

            "status": "error",

            "message": "Agent já cadastrado",

            "agent": {

                "agent_id": agent_existente.agent_id,

                "name": agent_existente.name,

                "host": agent_existente.host,

                "port": agent_existente.port,

                "rpa_directory": agent_existente.rpa_directory,

                "status": agent_existente.status

            }

        }


    # ========================================================
    # 7. CONSULTA CONFIG DO AGENT
    # ========================================================

    config_url = f"{base_url}/config"

    try:

        response = requests.get(
            config_url,
            timeout=5
        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Não foi possível consultar /config do Agent",
            "agent_id": agent_id,
            "error": str(error)
        }


    # ========================================================
    # 8. VALIDA HTTP DO CONFIG
    # ========================================================

    if response.status_code != 200:

        return {
            "status": "error",
            "message": "Agent respondeu com erro no /config",
            "agent_id": agent_id,
            "http_status": response.status_code
        }


    # ========================================================
    # 9. LÊ CONFIG
    # ========================================================

    try:

        config_response = response.json()

    except ValueError:

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no /config",
            "agent_id": agent_id
        }


    # ========================================================
    # 10. VALIDA RESPOSTA DO CONFIG
    # ========================================================

    if config_response.get("status") != "success":

        return {
            "status": "error",
            "message": "Resposta inválida do /config",
            "agent_id": agent_id,
            "response": config_response
        }


    config = config_response.get("config")


    if not isinstance(config, dict):

        return {
            "status": "error",
            "message": "Configuração do Agent inválida",
            "agent_id": agent_id
        }


    # ========================================================
    # 11. CAMPOS OBRIGATÓRIOS
    # ========================================================

    campos_obrigatorios = [
        "agent_id",
        "name",
        "host",
        "port",
        "status",
        "rpa_directory"
    ]


    campos_faltantes = [
        campo
        for campo in campos_obrigatorios
        if not config.get(campo)
    ]


    if campos_faltantes:

        return {
            "status": "error",
            "message": "Configuração do Agent incompleta",
            "agent_id": agent_id,
            "campos_faltantes": campos_faltantes
        }


    # ========================================================
    # 12. VALIDA IDENTIDADE
    # ========================================================

    if config["agent_id"] != agent_id:

        return {
            "status": "error",
            "message": "agent_id do /health não corresponde ao /config",
            "health": health,
            "config": config
        }


    # ========================================================
    # 13. VALIDA HOST
    # ========================================================

    if config["host"] != host:

        return {
            "status": "error",
            "message": "Host informado não corresponde ao Agent",
            "host_informado": host,
            "host_agent": config["host"]
        }


    # ========================================================
    # 14. VALIDA PORTA
    # ========================================================

    if int(config["port"]) != int(port):

        return {
            "status": "error",
            "message": "Porta informada não corresponde ao Agent",
            "port_informada": port,
            "port_agent": config["port"]
        }


    # ========================================================
    # 15. VALIDA DIRETÓRIO DOS RPAs
    # ========================================================

    if not config["rpa_directory"]:

        return {
            "status": "error",
            "message": "rpa_directory não informado",
            "agent_id": agent_id
        }


    # ========================================================
    # 16. ATIVA O AGENT
    #
    # Aqui está a parte que estava faltando.
    #
    # O Control Room chama o Agent e manda:
    #
    # {
    #     "status": "online"
    # }
    #
    # O próprio Agent grava isso no config.json.
    # ========================================================

    status_url = f"{base_url}/config/status"

    try:

        response = requests.put(
            status_url,
            json={
                "status": "online"
            },
            timeout=5
        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Agent validado, mas não foi possível ativá-lo",
            "agent_id": agent_id,
            "error": str(error)
        }


    # ========================================================
    # 17. VALIDA ATIVAÇÃO
    # ========================================================

    if response.status_code != 200:

        return {
            "status": "error",
            "message": "Não foi possível alterar o status do Agent para online",
            "agent_id": agent_id,
            "http_status": response.status_code,
            "response": response.text
        }


    try:

        status_response = response.json()

    except ValueError:

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido ao atualizar status",
            "agent_id": agent_id
        }


    if status_response.get("status") != "success":

        return {
            "status": "error",
            "message": "Agent não confirmou ativação",
            "agent_id": agent_id,
            "response": status_response
        }


    # ========================================================
    # 18. MONTA AGENT CADASTRADO
    # ========================================================

    agent = {

        "agent_id": config["agent_id"],

        "name": config["name"],

        "host": config["host"],

        "port": int(config["port"]),

        "rpa_directory": config["rpa_directory"],

        "status": "online"
    }


    # ========================================================
    # 19. CADASTRA NO CONTROL ROOM
    # ========================================================
    db = SessionLocal()

    try:
        db_agent = Agent(
            agent_id=agent["agent_id"],
            name=agent["name"],
            host=agent["host"],
            port=agent["port"],
            rpa_directory=agent["rpa_directory"],
            status=agent["status"]
        )

        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)

    finally:
        db.close()


    # ========================================================
    # 20. RETORNO
    # ========================================================

    return {

        "status": "success",

        "message": "Agent validado, ativado e cadastrado",

        "agent": agent
    }

# ============================================================
# Endpoint deletar agente do Contro Room
# ============================================================

@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str):

    db = SessionLocal()

    try:

        agent = db.query(Agent).filter(
            Agent.agent_id == agent_id
        ).first()

        if not agent:

            return {
                "status": "error",
                "message": "Agent não encontrado",
                "agent_id": agent_id
            }

        db.delete(agent)
        db.commit()

        return {
            "status": "success",
            "message": "Agent removido do Control Room",
            "agent_id": agent_id
        }

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível remover o Agent",
            "agent_id": agent_id,
            "error": str(error)
        }

    finally:

        db.close()
