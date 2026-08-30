from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import requests
import uvicorn
from database import criar_banco, SessionLocal
import hashlib
from models import Agent, Robot, RobotFolder, Execution, Schedule
import os
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time

#FRONT END
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse


# ============================================================
# CONTROL ROOM
# ============================================================

app = FastAPI(
    title="RPA Control Room",
    version="1.0.0"
)
# ============================================================
# REPOSITÓRIO DE ROBÔS
# ============================================================

BASE_DIRECTORY = Path(
    os.path.abspath(__file__)
).parent

ROBOT_REPOSITORY = (
    BASE_DIRECTORY / "repository"
)

ROBOT_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# BANCO DE DADOS
# ============================================================

criar_banco()

# ============================================================
# FRONT-END
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)

# ============================================================
# DASHBOARD
# ============================================================

@app.get("/")
def dashboard(request: Request):

    db = SessionLocal()

    try:

        agents = db.query(Agent).all()

        total_agents = len(agents)

        agents_online = sum(
            1
            for agent in agents
            if agent.status == "online"
        )

        total_robots = db.query(Robot).count()

    finally:

        db.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
        "agents": agents,
        "total_agents": total_agents,
        "agents_online": agents_online,
        "total_robots": total_robots
        }
)

    


# ============================================================
# FUNÇÃO PARA CALCULAR HASH DO ARQUIVO
# ============================================================

def calcular_hash_arquivo(
    arquivo: bytes
):

    return hashlib.sha256(
        arquivo
    ).hexdigest()

# ============================================================
# MODELO PARA CADASTRO
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




# ============================================================
# HEALTH DO CONTROL ROOM
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "service": "RPA Control Room"
    }


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


@app.post("/agents/heartbeat")
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

                    print(
                        f"[AGENT OFFLINE] "
                        f"{agent.name} | "
                        f"último heartbeat: "
                        f"{agent.last_heartbeat}"
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

@app.post("/agents/register")
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
    #agents[agent_id] = agent


    # ========================================================
    # 20. RETORNO
    # ========================================================

    return {

        "status": "success",

        "message": "Agent validado, ativado e cadastrado",

        "agent": agent
    }


# ============================================================
# ENDPOINT AGENTS
# ============================================================

@app.get("/agents")
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
# endppoint PÁGINA CADASTRAR NOVO AGENT
# ============================================================

@app.get("/agents/new")
def new_agent(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="agent_form.html"
    )
# ============================================================
# ENDPOINT PÁGINA HISTÓRICO DE EXECUÇÕES
# ============================================================

@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="history.html"
    )

# ============================================================
# Endpoint CONSULTAR AGENT
# ============================================================

@app.get("/agents/{agent_id}")
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
# ENDPOINT EXECUTAR ROBOT NO AGENT
# ============================================================

class ExecutionRequest(BaseModel):

    robot_id: int


# ============================================================
# EXECUTAR ROBÔ
#
# Fluxo:
#
# 1. Busca Agent
# 2. Busca Robot
# 3. Verifica se Agent está idle
# 4. Faz deploy do Robot no Agent
# 5. Manda executar o Robot
# 6. Retorna resultado
# ============================================================

@app.post("/agents/{agent_id}/execution/run")
def run_agent_robot(
    agent_id: str,
    request: ExecutionRequest
):

    # ========================================================
    # 1. ABRE BANCO
    # ========================================================

    db = SessionLocal()

    try:

        # ====================================================
        # 2. BUSCA AGENT
        # ====================================================

        agent = db.query(Agent).filter(
            Agent.agent_id == agent_id
        ).first()

        if not agent:

            return {
                "status": "error",
                "message": "Agent não encontrado",
                "agent_id": agent_id
            }


        # ====================================================
        # 3. BUSCA ROBÔ
        # ====================================================

        robot = db.query(Robot).filter(
            Robot.id == request.robot_id
        ).first()

        if not robot:

            return {
                "status": "error",
                "message": "Robot não encontrado",
                "robot_id": request.robot_id
            }


        # Guarda os dados necessários antes de fechar o banco

        robot_id = robot.id
        robot_name = robot.name
        robot_filename = robot.filename
        robot_version = robot.version
        robot_file_path = robot.file_path

    finally:

        db.close()


    # ========================================================
    # 4. VALIDA ARQUIVO DO ROBÔ
    # ========================================================

    if not robot_file_path:

        return {
            "status": "error",
            "message": "Robot não possui file_path cadastrado",
            "robot_id": robot_id
        }


    robot_path = Path(robot_file_path)

    if not robot_path.exists():

        return {
            "status": "error",
            "message": "Arquivo do Robot não encontrado no Control Room",
            "robot_id": robot_id,
            "file_path": str(robot_path)
        }

    # ========================================================
    # 4.1 VALIDA FORMATO PARA EXECUÇÃO
    # ========================================================

    extensao_robot = robot_path.suffix.lower()

    if extensao_robot != ".zip":

        return {
            "status": "error",
            "message": "Formato de Robot não suportado para execução",
            "robot_id": robot_id,
            "robot_name": robot_name,
            "filename": robot_filename,
            "extensao": extensao_robot,
            "formato_permitido": ".zip"
        }

    # ========================================================
    # 5. VALIDA CONEXÃO REAL COM O AGENT
    # ========================================================

    health_url = (
        f"http://{agent.host}:{agent.port}"
        "/health"
    )

    try:

        health_response = requests.get(
            health_url,
            timeout=5
        )

    except requests.RequestException as error:

        # ====================================================
        # AGENT NÃO ESTÁ ACESSÍVEL
        # ====================================================

        db = SessionLocal()

        try:

            agent_db = db.query(Agent).filter(
                Agent.agent_id == agent_id
            ).first()

            if agent_db:
                agent_db.status = "offline"
                db.commit()

        finally:

            db.close()

        return {
            "status": "error",
            "message": "Agent está offline ou indisponível",
            "agent_id": agent_id,
            "error": str(error)
        }


    # ========================================================
    # 5.1 VALIDA RESPOSTA DO HEALTH
    # ========================================================

    if health_response.status_code != 200:

        db = SessionLocal()

        try:

            agent_db = db.query(Agent).filter(
                Agent.agent_id == agent_id
            ).first()

            if agent_db:
                agent_db.status = "offline"
                db.commit()

        finally:

            db.close()

        return {
            "status": "error",
            "message": "Agent respondeu com erro no /health",
            "agent_id": agent_id,
            "http_status": health_response.status_code
        }


    # ========================================================
    # 5.2 LÊ RESPOSTA DO HEALTH
    # ========================================================

    try:

        health = health_response.json()

    except ValueError:

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no /health",
            "agent_id": agent_id
        }


    # ========================================================
    # 5.3 CONFIRMA QUE O AGENT ESTÁ ONLINE
    # ========================================================

    if health.get("status") != "online":

        db = SessionLocal()

        try:

            agent_db = db.query(Agent).filter(
                Agent.agent_id == agent_id
            ).first()

            if agent_db:
                agent_db.status = "offline"
                db.commit()

        finally:

            db.close()

        return {
            "status": "error",
            "message": "Agent não está online",
            "agent_id": agent_id,
            "health": health
        }


    # ========================================================
    # 5.4 AGENT ESTÁ ACESSÍVEL
    # ========================================================

    print(
        f"[AGENT DISPONÍVEL] "
        f"{agent.name} | "
        f"{agent.host}:{agent.port}"
    )


    # ========================================================
    # 5.5 AGORA CONSULTA STATUS DE EXECUÇÃO
    # ========================================================

    status_url = (
        f"http://{agent.host}:{agent.port}"
        "/execution/status"
    )

    try:

        response = requests.get(
            status_url,
            timeout=5
        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Não foi possível consultar o status de execução do Agent",
            "agent_id": agent_id,
            "error": str(error)
        }
    # ========================================================
    # 6. VALIDA STATUS HTTP
    # ========================================================

    if response.status_code != 200:

        return {
            "status": "error",
            "message": "Agent respondeu com erro ao consultar status",
            "agent_id": agent_id,
            "http_status": response.status_code,
            "response": response.text
        }


    # ========================================================
    # 7. LÊ STATUS
    # ========================================================

    try:

        status_response = response.json()

    except ValueError:

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido",
            "agent_id": agent_id
        }


    execution_status = status_response.get(
        "execution_status"
    )


    # ========================================================
    # 8. VERIFICA SE AGENT ESTÁ LIVRE
    # ========================================================

    if execution_status != "idle":

        return {
            "status": "error",
            "message": "Agent não está disponível para execução",
            "agent_id": agent_id,
            "execution_status": execution_status
        }


    # ========================================================
    # 9. DEPLOY DO ROBÔ NO AGENT
    # ========================================================
    #
    # O arquivo está no:
    #
    # Control Room:
    # repository/TESTE/teste.zip
    #
    # Agora enviamos esse arquivo para o Agent.
    #

    deploy_url = (
    f"http://{agent.host}:{agent.port}"
    "/robots/upload"
)

    try:

        with open(
            robot_path,
            "rb"
        ) as arquivo:

            deploy_response_http = requests.post(

                deploy_url,

                files={
                    "file": (
                        robot_filename,
                        arquivo,
                        "application/zip"
                    )
                },

                timeout=60
            )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Não foi possível fazer upload do Robot para o Agent",
            "agent_id": agent_id,
            "robot_id": robot_id,
            "error": str(error)
        }


    # ========================================================
    # 10. VALIDA DEPLOY
    # ========================================================

    if deploy_response_http.status_code != 200:

        return {
            "status": "error",
            "message": "Agent recusou o deploy do Robot",
            "agent_id": agent_id,
            "robot_id": robot_id,
            "http_status": deploy_response_http.status_code,
            "response": deploy_response_http.text
        }


    try:

        deploy_response = deploy_response_http.json()

    except ValueError:

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no deploy",
            "agent_id": agent_id,
            "robot_id": robot_id
        }


    # ========================================================
    # 11. EXECUÇÃO DO ROBÔ
    # ========================================================
    # 11.1 CRIA REGISTRO DA EXECUÇÃO
    # ========================================================

    db = SessionLocal()

    try:

        execucao = Execution(
            robot_id=robot_id,
            robot_name=robot.name,
            robot_filename=robot.filename,
            agent_id=agent_id,
            status="running",
            started_at=datetime.now()
        )

        db.add(execucao)

        db.commit()

        db.refresh(execucao)

        execution_id = execucao.id

    finally:

        db.close()
        # ========================================================
        #
        # IMPORTANTE:
        #
        # O Agent recebe robot_name.
        #
        # Não enviamos robot_id para ele.
        #

    execution_url = (
        f"http://{agent.host}:{agent.port}"
        "/execution/run"
    )

    try:

        response = requests.post(

            execution_url,

            json={
                "robot_name": robot_filename,
                "execution_id": execution_id
            },

            timeout=10

        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Não foi possível enviar comando de execução para o Agent",
            "agent_id": agent_id,
            "robot_id": robot_id,
            "error": str(error)
        }


    # ========================================================
    # 12. VALIDA EXECUÇÃO
    # ========================================================

    if response.status_code != 200:

        return {

            "status": "error",

            "message": "Agent recusou o comando de execução",

            "agent_id": agent_id,

            "robot_id": robot_id,

            "http_status": response.status_code,

            "response": response.text

        }


    try:

        execution_response = response.json()

    except ValueError:



        return {

            "status": "error",

            "message": "Agent retornou JSON inválido na execução",

            "agent_id": agent_id,

            "robot_id": robot_id

        }

    # ========================================================
    # 12.1 VALIDA STATUS DA EXECUÇÃO
    # ========================================================

    if execution_response.get("status") != "success":

        return {

            "status": "error",

            "message": "Agent recusou a execução do Robot",

            "agent_id": agent_id,

            "robot_id": robot_id,

            "robot_name": robot_name,

            "filename": robot_filename,

            "deploy": deploy_response,

            "execution": execution_response

        }


    # ========================================================
    # 13. RETORNO FINAL
    # ========================================================

    return {

        "status": "success",

        "message": "Robot enviado para o Agent e execução iniciada",

        "agent_id": agent_id,

        "robot_id": robot_id,

        "robot_name": robot_name,

        "filename": robot_filename,

        "version": robot_version,

        "deploy": deploy_response,

        "execution": execution_response

    }
# ============================================================
# ENDPOINT CONSULTAR STATUS DE EXECUÇÃO DO AGENT
# ============================================================

@app.get("/agents/{agent_id}/execution/status")
def get_execution_status(agent_id: str):

    # ========================================================
    # 1. BUSCA AGENT NO BANCO
    # ========================================================

    db = SessionLocal()

    try:

        agent = db.query(Agent).filter(
            Agent.agent_id == agent_id
        ).first()

    finally:

        db.close()


    if not agent:

        return {

            "status": "error",

            "message": "Agent não encontrado",

            "agent_id": agent_id

        }


    # ========================================================
    # 2. MONTA URL DO AGENT
    # ========================================================

    agent_url = (
        f"http://{agent.host}:{agent.port}"
        "/execution/status"
    )


    # ========================================================
    # 3. CONSULTA O AGENT
    # ========================================================

    try:

        response = requests.get(

            agent_url,

            timeout=5

        )

    except requests.RequestException as error:

        return {

            "status": "error",

            "message": "Não foi possível consultar o status de execução do Agent",

            "agent_id": agent_id,

            "error": str(error)

        }


    # ========================================================
    # 4. VALIDA RESPOSTA
    # ========================================================

    if response.status_code != 200:

        return {

            "status": "error",

            "message": "Agent respondeu com erro",

            "agent_id": agent_id,

            "http_status": response.status_code,

            "response": response.text

        }


    # ========================================================
    # 5. LÊ JSON
    # ========================================================

    try:

        resultado = response.json()

    except ValueError:

        return {

            "status": "error",

            "message": "Agent retornou JSON inválido",

            "agent_id": agent_id

        }

    # ========================================================
    # 6. ATUALIZA EXECUÇÃO NO BANCO
    
    # ========================================================
    # 6. RETORNO
    # ========================================================

    return {

        "status": "success",

        "agent_id": agent_id,

        "execution_status": resultado.get(
            "execution_status"
        ),
        "last_execution": resultado.get(
            "last_execution"
        )

    }
# ============================================================
# ENDPOINT PARAR EXECUÇÃO DO AGENT
# ============================================================

@app.post("/agents/{agent_id}/execution/stop")
def stop_agent_execution(agent_id: str):

    # ========================================================
    # 1. BUSCA AGENT NO BANCO
    # ========================================================

    db = SessionLocal()

    try:

        agent = db.query(Agent).filter(
            Agent.agent_id == agent_id
        ).first()

    finally:

        db.close()


    if not agent:

        return {
            "status": "error",
            "message": "Agent não encontrado",
            "agent_id": agent_id
        }


    # ========================================================
    # 2. MONTA URL DO AGENT
    # ========================================================

    stop_url = (
        f"http://{agent.host}:{agent.port}"
        "/execution/stop"
    )


    # ========================================================
    # 3. ENVIA COMANDO DE STOP
    # ========================================================

    try:

        response = requests.post(
            stop_url,
            timeout=10
        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Não foi possível enviar comando de stop para o Agent",
            "agent_id": agent_id,
            "error": str(error)
        }


    # ========================================================
    # 4. VALIDA RESPOSTA HTTP
    # ========================================================

    if response.status_code != 200:

        return {
            "status": "error",
            "message": "Agent respondeu com erro ao parar o Robot",
            "agent_id": agent_id,
            "http_status": response.status_code,
            "response": response.text
        }


    # ========================================================
    # 5. LÊ RESPOSTA DO AGENT
    # ========================================================

    try:

        resultado = response.json()

    except ValueError:

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido ao parar o Robot",
            "agent_id": agent_id
        }


    # ========================================================
    # 6. VALIDA RESULTADO
    # ========================================================

    if resultado.get("status") != "success":

        return {
            "status": "error",
            "message": resultado.get(
                "message",
                "Agent recusou o comando de stop"
            ),
            "agent_id": agent_id,
            "agent_response": resultado
        }


    # ========================================================
    # 7. RETORNO
    # ========================================================

    return {
        "status": "success",
        "message": "Comando de stop enviado para o Agent",
        "agent_id": agent_id,
        "agent_response": resultado
    }
# ============================================================
# ENDPOINT LISTAR EXECUÇÕES
# ============================================================
# ============================================================
# ENDPOINT LISTAR EXECUÇÕES EM ANDAMENTO
# ============================================================

@app.get("/executions")
def list_executions():

    db = SessionLocal()

    try:

        executions = (
            db.query(
                Execution,
                Robot,
                Agent
            )
            .outerjoin(
                Robot,
                Execution.robot_id == Robot.id
            )
            .outerjoin(
                Agent,
                Execution.agent_id == Agent.agent_id
            )
            .filter(
                Execution.status == "running"
            )
            .order_by(
                Execution.id.desc()
            )
            .all()
        )

        resultado = []

        for execution, robot, agent in executions:

            resultado.append({

                "id": execution.id,

                "robot_id": execution.robot_id,

                "robot_name": (
                    execution.robot_name
                    if execution.robot_name
                    else (
                        robot.name
                        if robot
                        else "Desconhecido"
                    )
                ),

                "filename": (
                    execution.robot_filename
                    if execution.robot_filename
                    else (
                        robot.filename
                        if robot
                        else "Desconhecido"
                    )
                ),

                "agent_id": execution.agent_id,

                "agent_name": (
                    agent.name
                    if agent
                    else "Agent excluído"
                ),

                "status": execution.status,

                "started_at": (
                    execution.started_at.isoformat()
                    if execution.started_at
                    else None
                ),

                "finished_at": (
                    execution.finished_at.isoformat()
                    if execution.finished_at
                    else None
                ),

                "error_message": execution.error_message

            })

        return {

            "status": "success",

            "total": len(resultado),

            "executions": resultado

        }

    finally:

        db.close()


# ============================================================
# ENDPOINT HISTÓRICO DE EXECUÇÕES
# ============================================================

@app.get("/executions/history")
def list_execution_history():

    db = SessionLocal()

    try:

        executions = (
            db.query(
                Execution,
                Robot,
                Agent
            )
            .outerjoin(
                Robot,
                Execution.robot_id == Robot.id
            )
            .outerjoin(
                Agent,
                Execution.agent_id == Agent.agent_id
            )
            .filter(
                Execution.status != "running"
            )
            .order_by(
                Execution.id.desc()
            )
            .all()
        )

        resultado = []

        for execution, robot, agent in executions:

            resultado.append({

                "id": execution.id,

                "robot_id": execution.robot_id,

                "robot_name": (
                    execution.robot_name
                    if execution.robot_name
                    else (
                        robot.name
                        if robot
                        else "Desconhecido"
                    )
                ),

                "filename": (
                    execution.robot_filename
                    if execution.robot_filename
                    else (
                        robot.filename
                        if robot
                        else "Desconhecido"
                    )
                ),

                "agent_id": execution.agent_id,

                "agent_name": (
                    agent.name
                    if agent
                    else "Agent excluído"
                ),

                "status": execution.status,

                "started_at": (
                    execution.started_at.isoformat()
                    if execution.started_at
                    else None
                ),

                "finished_at": (
                    execution.finished_at.isoformat()
                    if execution.finished_at
                    else None
                ),

                "error_message": execution.error_message

            })

        return {

            "status": "success",

            "total": len(resultado),

            "executions": resultado

        }

    finally:

        db.close()
# ============================================================
# Endpoint deletar agente do Contro Room
# ============================================================

@app.delete("/agents/{agent_id}")
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

# ============================================================
# ENDPOINT UPLOAD ROBOT PARA O CONTROL ROOM
# ============================================================

@app.post("/robots/upload")
async def upload_robot(
    file: UploadFile = File(...),
    folder_id: int | None = Form(None)
):

    # ========================================================
    # 1. BUSCA AGENT NO BANCO
    # ========================================================




    # ========================================================
    # 2. VALIDA EXTENSÃO
    # ========================================================

    nome_arquivo = file.filename

    if not nome_arquivo:

        return {

            "status": "error",

            "message": "Nome do arquivo não informado"

        }


    extensao = os.path.splitext(
        nome_arquivo
    )[1].lower()


    extensoes_permitidas = [
        ".zip",
        ".rar"
    ]


    if extensao not in extensoes_permitidas:

        return {

            "status": "error",

            "message": "Formato de robô não permitido",

            "extensao": extensao,

            "formatos_permitidos": extensoes_permitidas

        }


    # ========================================================
    # 3. LÊ O ARQUIVO
    # ========================================================

    try:

        conteudo = await file.read()

    except Exception as error:

        return {

            "status": "error",

            "message": "Não foi possível ler o arquivo",

            #"agent_id": agent_id,

            "error": str(error)

        }


    # ========================================================
    # 4. CALCULA SHA-256
    # ========================================================

    file_hash = calcular_hash_arquivo(
        conteudo
    )
        # ============================================================
    # LOCALIZA PASTA DO ROBÔ
    # ============================================================

    db = SessionLocal()

    try:

        pasta = None

        if folder_id is not None:

            pasta = db.query(
                RobotFolder
            ).filter(
                RobotFolder.id == folder_id
            ).first()

            if not pasta:

                return {
                    "status": "error",
                    "message": "Pasta não encontrada",
                    "folder_id": folder_id
                }

    finally:

        db.close()


    if pasta:

        pasta_path = ROBOT_REPOSITORY / pasta.name

    else:

        pasta_path = ROBOT_REPOSITORY / "Sem pasta"


    pasta_path.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho_arquivo = pasta_path / nome_arquivo

    with open(
        caminho_arquivo,
        "wb"
    ) as arquivo_destino:

        arquivo_destino.write(
            conteudo
        )

    # ========================================================
    # 5. CONSULTA / ATUALIZA ROBOT NO BANCO
    # ========================================================

    db = SessionLocal()

    try:

        robot = db.query(Robot).filter(
            Robot.name == nome_arquivo,
            
        ).first()


        # ====================================================
        # DEBUG VERSIONAMENTO
        # ====================================================

        print()
        print("=" * 60)
        print("DEBUG VERSIONAMENTO")
        print(f"Arquivo recebido : {nome_arquivo}")
        print(f"Hash recebido    : {file_hash}")
        #print(f"Agent ID         : {agent_id}")
        print(f"Robot encontrado : {robot}")

        if robot:

            print(f"Hash banco       : {robot.file_hash}")
            print(f"Versão banco     : {robot.version}")
            print(f"Hash é igual?    : {robot.file_hash == file_hash}")

        print("=" * 60)
        print()


        # ====================================================
        # 6. VERIFICA SE O ARQUIVO É IGUAL
        # ====================================================

        if robot:

            if robot.file_hash == file_hash:

                return {

                    "status": "success",

                    "message": "Robot já está atualizado",

                    "upload": False,

                    #"agent_id": agent_id,

                    "robot": {

                        "name": robot.name,

                        "filename": robot.filename,

                        "version": robot.version,

                        "file_hash": robot.file_hash

                    }

                }


            # =================================================
            # ARQUIVO FOI ALTERADO
            # =================================================

            nova_versao = robot.version + 1

        else:

            # =================================================
            # PRIMEIRO UPLOAD
            # =================================================

            nova_versao = 1



        # ====================================================
        # 10. SALVA / ATUALIZA ROBOT NO BANCO
        # ====================================================

        if robot:

            robot.filename = nome_arquivo

            robot.version = nova_versao

            robot.file_hash = file_hash
            robot.file_path = str(caminho_arquivo)
            robot.folder_id = folder_id

        else:

            robot = Robot(

                name=nome_arquivo,

                filename=nome_arquivo,

                version=nova_versao,

                file_hash=file_hash,
                file_path=str(caminho_arquivo),
                folder_id=folder_id


            )

            db.add(robot)


        db.commit()

        db.refresh(robot)


    finally:

        db.close()
    # ========================================================
    # 11. RETORNO
    # ========================================================

    return {

        "status": "success",

        "message": "Robot enviado para o Agent",

        "upload": True,

        #"agent_id": agent_id,

        "robot": {

            "name": robot.name,

            "filename": robot.filename,

            "version": robot.version,

            "file_hash": robot.file_hash

        },

        #"agent_response": resultado.get(
        #    "robot"
        #)

    }

# ============================================================
# ENDPOINT EXCLUIR ROBÔ
# ============================================================

@app.delete("/robots/{robot_id}")
def delete_robot(robot_id: int):

    db = SessionLocal()

    try:

        robot = db.query(Robot).filter(
            Robot.id == robot_id
        ).first()

        if not robot:

            return {
                "status": "error",
                "message": "Robô não encontrado",
                "robot_id": robot_id
            }

        nome = robot.name
        file_path = robot.file_path

        # --------------------------------------------
        # Exclui arquivo físico
        # --------------------------------------------

        if file_path:

            caminho = Path(file_path)

            if caminho.exists():
                caminho.unlink()

        # --------------------------------------------
        # Exclui registro do banco
        # --------------------------------------------

        db.delete(robot)
        db.commit()

        return {
            "status": "success",
            "message": "Robô excluído com sucesso",
            "robot_id": robot_id,
            "name": nome
        }

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível excluir o robô",
            "robot_id": robot_id,
            "error": str(error)
        }

    finally:

        db.close()


# ============================================================
# EXCLUIR PASTA
# ============================================================

@app.delete("/robot-folders/{folder_id}")
def delete_robot_folder(folder_id: int):

    db = SessionLocal()

    try:

        folder = db.query(RobotFolder).filter(
            RobotFolder.id == folder_id
        ).first()

        if not folder:

            return {
                "status": "error",
                "message": "Pasta não encontrada",
                "folder_id": folder_id
            }

        # --------------------------------------------
        # Verifica se existem robôs na pasta
        # --------------------------------------------

        robots = db.query(Robot).filter(
            Robot.folder_id == folder_id
        ).all()

        if robots:

            return {
                "status": "error",
                "message": (
                    "Não é possível excluir a pasta "
                    "porque existem robôs dentro dela."
                ),
                "folder_id": folder_id,
                "robots_count": len(robots)
            }

        # --------------------------------------------
        # Caminho físico da pasta
        # --------------------------------------------

        pasta_path = ROBOT_REPOSITORY / folder.name

        # --------------------------------------------
        # Remove pasta física
        # --------------------------------------------

        if pasta_path.exists():
            pasta_path.rmdir()

        # --------------------------------------------
        # Remove registro do banco
        # --------------------------------------------

        db.delete(folder)
        db.commit()

        return {
            "status": "success",
            "message": "Pasta excluída com sucesso",
            "folder_id": folder_id,
            "name": folder.name
        }

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível excluir a pasta",
            "folder_id": folder_id,
            "error": str(error)
        }

    finally:

        db.close()

# ============================================================
# ENDPOINT EXCLUIR PASTA DE ROBÔS
# ============================================================

@app.delete("/robot-folders/{folder_id}")
def delete_robot_folder(folder_id: int):

    db = SessionLocal()

    try:

        # --------------------------------------------
        # Busca pasta
        # --------------------------------------------

        folder = db.query(RobotFolder).filter(
            RobotFolder.id == folder_id
        ).first()

        if not folder:

            return {
                "status": "error",
                "message": "Pasta não encontrada",
                "folder_id": folder_id
            }

        # --------------------------------------------
        # Verifica robôs dentro da pasta
        # --------------------------------------------

        robots = db.query(Robot).filter(
            Robot.folder_id == folder_id
        ).all()

        if robots:

            return {

                "status": "error",

                "message": (
                    "Não é possível excluir a pasta "
                    "porque existem robôs dentro dela"
                ),

                "folder_id": folder_id,

                "robots_count": len(robots)

            }

        # --------------------------------------------
        # Caminho físico
        # --------------------------------------------

        pasta_path = ROBOT_REPOSITORY / folder.name

        # --------------------------------------------
        # Remove pasta física se estiver vazia
        # --------------------------------------------

        if pasta_path.exists():

            pasta_path.rmdir()

        # --------------------------------------------
        # Remove banco
        # --------------------------------------------

        db.delete(folder)

        db.commit()

        return {

            "status": "success",

            "message": "Pasta excluída com sucesso",

            "folder_id": folder_id,

            "name": folder.name

        }

    except Exception as error:

        db.rollback()

        return {

            "status": "error",

            "message": "Não foi possível excluir a pasta",

            "folder_id": folder_id,

            "error": str(error)

        }

    finally:

        db.close()
# ============================================================
# ENDPOINT EXCLUIR ROBÔ
# ============================================================

@app.delete("/robots/{robot_id}")
def delete_robot(robot_id: int):

    db = SessionLocal()

    try:

        robot = db.query(Robot).filter(
            Robot.id == robot_id
        ).first()

        if not robot:

            return {
                "status": "error",
                "message": "Robô não encontrado",
                "robot_id": robot_id
            }

        # --------------------------------------------
        # Guarda informações antes de excluir
        # --------------------------------------------

        nome = robot.name
        file_path = robot.file_path

        # --------------------------------------------
        # Exclui arquivo físico
        # --------------------------------------------

        if file_path:

            caminho = Path(file_path)

            if caminho.exists():

                caminho.unlink()

        # --------------------------------------------
        # Exclui registro do banco
        # --------------------------------------------

        db.delete(robot)

        db.commit()

        return {

            "status": "success",

            "message": "Robô excluído com sucesso",

            "robot_id": robot_id,

            "name": nome

        }

    except Exception as error:

        db.rollback()

        return {

            "status": "error",

            "message": "Não foi possível excluir o robô",

            "robot_id": robot_id,

            "error": str(error)

        }

    finally:

        db.close()
# ============================================================
# endpoint CRIAR PASTA DE ROBÔS
# ============================================================

class RobotFolderRequest(BaseModel):

    name: str

    parent_id: int | None = None


@app.post("/robot-folders")
def create_robot_folder(
    request: RobotFolderRequest
):

    db = SessionLocal()

    try:

        # ====================================================
        # 1. VALIDA NOME
        # ====================================================

        nome = request.name.strip()

        if not nome:

            return {
                "status": "error",
                "message": "Nome da pasta não informado"
            }


        # ====================================================
        # 2. VALIDA PASTA PAI
        # ====================================================

        if request.parent_id is not None:

            parent = db.query(
                RobotFolder
            ).filter(
                RobotFolder.id == request.parent_id
            ).first()

            if not parent:

                return {
                    "status": "error",
                    "message": "Pasta pai não encontrada",
                    "parent_id": request.parent_id
                }


        # ====================================================
        # 3. VERIFICA DUPLICIDADE
        # ====================================================

        pasta_existente = db.query(
            RobotFolder
        ).filter(
            RobotFolder.name == nome,
            RobotFolder.parent_id == request.parent_id
        ).first()


        if pasta_existente:

            return {
                "status": "error",
                "message": "Pasta já existe",
                "folder_id": pasta_existente.id
            }


        # ====================================================
        # 4. CRIA PASTA
        # ====================================================

        pasta = RobotFolder(

            name=nome,

            parent_id=request.parent_id

        )


        db.add(pasta)

        db.commit()

        db.refresh(pasta)


        # ====================================================
        # 5. RETORNO
        # ====================================================

        return {

            "status": "success",

            "message": "Pasta criada com sucesso",

            "folder": {

                "id": pasta.id,

                "name": pasta.name,

                "parent_id": pasta.parent_id

            }

        }

    except Exception as error:

        db.rollback()

        return {

            "status": "error",

            "message": "Não foi possível criar a pasta",

            "error": str(error)

        }

    finally:

        db.close()


# ============================================================
# endpointLISTAR PASTAS DE ROBÔS
# ============================================================

@app.get("/robot-folders")
def list_robot_folders():

    db = SessionLocal()

    try:

        folders = db.query(
            RobotFolder
        ).order_by(
            RobotFolder.name
        ).all()

        return {

            "status": "success",

            "total": len(folders),

            "folders": [

                {
                    "id": folder.id,
                    "name": folder.name,
                    "parent_id": folder.parent_id
                }

                for folder in folders

            ]

        }

    except Exception as error:

        return {

            "status": "error",

            "message": "Não foi possível listar as pastas",

            "error": str(error)

        }

    finally:

        db.close()

# ============================================================
# Endpoint LISTAR ROBÔS DE UMA PASTA
# ============================================================

@app.get("/robot-folders/{folder_id}/robots")
def list_robots_in_folder(folder_id: int):

    db = SessionLocal()

    try:

        # ====================================================
        # 1. BUSCA A PASTA
        # ====================================================

        folder = db.query(
            RobotFolder
        ).filter(
            RobotFolder.id == folder_id
        ).first()

        if not folder:

            return {
                "status": "error",
                "message": "Pasta não encontrada",
                "folder_id": folder_id
            }


        # ====================================================
        # 2. BUSCA OS ROBÔS DA PASTA
        # ====================================================

        robots = db.query(
            Robot
        ).filter(
            Robot.folder_id == folder_id
        ).order_by(
            Robot.name
        ).all()


        # ====================================================
        # 3. RETORNO
        # ====================================================

        return {

            "status": "success",

            "folder": {
                "id": folder.id,
                "name": folder.name
            },

            "total": len(robots),

            "robots": [

                {
                    "id": robot.id,
                    "name": robot.name,
                    "filename": robot.filename,
                    "version": robot.version,
                    "file_hash": robot.file_hash,
                    "file_path": robot.file_path
                }

                for robot in robots

            ]

        }

    except Exception as error:

        return {

            "status": "error",

            "message": "Não foi possível listar os robôs da pasta",

            "error": str(error)

        }

    finally:

        db.close()

# ============================================================
# PÁGINA DE ROBÔS
# ============================================================

@app.get("/robots")
def robots_page(request: Request):

    db = SessionLocal()

    try:

        folders = db.query(
            RobotFolder
        ).filter(
            RobotFolder.parent_id == None
        ).order_by(
            RobotFolder.name
        ).all()

        return templates.TemplateResponse(
            request=request,
            name="robots.html",
            context={
                "folders": folders
            }
        )

    finally:

        db.close()

# ============================================================
# RECEBE RESULTADO DA EXECUÇÃO DO AGENT
# ============================================================

class ExecutionResultRequest(BaseModel):

    execution_id: int
    agent_id: str
    status: str
    message: str
    started_at: str
    finished_at: str


@app.post("/executions/{execution_id}/result")
def receber_resultado_execucao(
    execution_id: int,
    request: ExecutionResultRequest
):

    db = SessionLocal()

    try:

        # ====================================================
        # LOCALIZA A EXECUÇÃO
        # ====================================================

        execucao = db.query(
            Execution
        ).filter(
            Execution.id == execution_id
        ).first()


        if not execucao:

            return {
                "status": "error",
                "message": "Execução não encontrada",
                "execution_id": execution_id
            }


        # ====================================================
        # VALIDA AGENT
        # ====================================================

        if execucao.agent_id != request.agent_id:

            return {
                "status": "error",
                "message": "Agent não corresponde à execução",
                "execution_id": execution_id
            }


        # ====================================================
        # ATUALIZA EXECUÇÃO
        # ====================================================

        execucao.status = request.status

        execucao.finished_at = datetime.fromisoformat(
            request.finished_at
        )


        if request.status == "error":

            execucao.error_message = request.message

        else:

            execucao.error_message = None


        db.commit()


        # ====================================================
        # RETORNO
        # ====================================================

        return {

            "status": "success",

            "message": "Resultado da execução atualizado",

            "execution_id": execution_id,

            "execution_status": execucao.status

        }

    except Exception as error:

        db.rollback()

        return {

            "status": "error",

            "message": "Erro ao atualizar execução",

            "error": str(error),

            "execution_id": execution_id

        }

    finally:

        db.close()


# ============================================================
# PÁGINA DE EXECUÇÕES
# ============================================================

@app.get(
    "/executions/page",
    response_class=HTMLResponse
)
def pagina_execucoes(
    request: Request
):

    return templates.TemplateResponse(
    request=request,
    name="executions.html"
)

# ============================================================
## ============================================================
# PÁGINA DE AGENTS
# ============================================================

@app.get(
    "/agents-page",
    response_class=HTMLResponse
)
def pagina_agents(
    request: Request
):

    db = SessionLocal()

    try:

        agents = db.query(
            Agent
        ).all()

        return templates.TemplateResponse(
            request=request,
            name="agents.html",
            context={
                "agents": agents
            }
        )

    finally:

        db.close()



# ============================================================
# endpoint PÁGINA DE AGENDAMENTOS
# ============================================================

@app.get(
    "/schedules",
    response_class=HTMLResponse
)
def pagina_agendamentos(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="schedules.html"
    )



# ============================================================
# ENDPOINT LISTAR AGENDAMENTOS
# ============================================================

@app.get("/api/schedules")
def listar_agendamentos():

    db = SessionLocal()

    try:

        schedules = db.query(
            Schedule
        ).order_by(
            Schedule.id.desc()
        ).all()

        resultado = []

        for schedule in schedules:

            robot = db.query(
                Robot
            ).filter(
                Robot.id == schedule.robot_id
            ).first()

            agent = None

            if schedule.agent_id:

                agent = db.query(
                    Agent
                ).filter(
                    Agent.agent_id == schedule.agent_id
                ).first()

            resultado.append({

                "id": schedule.id,

                "robot_id": schedule.robot_id,

                "robot_name":
                    robot.name
                    if robot
                    else "Robô não encontrado",

                "agent_id":
                    schedule.agent_id,

                "agent_name":
                    agent.name
                    if agent
                    else "Automático",

                "tipo":
                    schedule.tipo,

                "data_inicio":
                    schedule.data_inicio.isoformat()
                    if schedule.data_inicio
                    else None,

                "horario":
                    schedule.horario,

                "dias_semana":
                    schedule.dias_semana,

                "ativo":
                    bool(schedule.ativo),

                "proxima_execucao":
                    schedule.proxima_execucao.isoformat()
                    if schedule.proxima_execucao
                    else None,

                "ultima_execucao":
                    schedule.ultima_execucao.isoformat()
                    if schedule.ultima_execucao
                    else None,

                "intervalo_ativo":
                    bool(schedule.intervalo_ativo),

                "intervalo_valor":
                    schedule.intervalo_valor,

                "intervalo_unidade":
                    schedule.intervalo_unidade,

                "horario_fim":
                    schedule.horario_fim

            })

        return {

            "status": "success",

            "total": len(resultado),

            "schedules": resultado

        }

    finally:

        db.close()




# ============================================================
# SCHEDULER DE AGENDAMENTOS
# ============================================================

scheduler_lock = threading.Lock()
scheduler_thread = None


def _horario_para_datetime(data_base, horario):

    try:
        hora, minuto = horario.split(":")[:2]
        return data_base.replace(
            hour=int(hora),
            minute=int(minuto),
            second=0,
            microsecond=0
        )
    except (ValueError, AttributeError):
        return None


def calcular_proxima_execucao(schedule, agora=None):

    if agora is None:
        agora = datetime.now()

    inicio = schedule.data_inicio

    if not inicio:
        return None

    horario_inicial = _horario_para_datetime(
        inicio,
        schedule.horario
    )

    if horario_inicial is None:
        return None

    # ========================================================
    # UMA VEZ
    # ========================================================

    if schedule.tipo == "once":
        return horario_inicial


    # ========================================================
    # INTERVALO
    # ========================================================

    intervalo_ativo = getattr(
        schedule,
        "intervalo_ativo",
        0
    )

    intervalo_valor = getattr(
        schedule,
        "intervalo_valor",
        None
    )

    intervalo_unidade = getattr(
        schedule,
        "intervalo_unidade",
        None
    )

    horario_fim = getattr(
        schedule,
        "horario_fim",
        None
    )


    if (
        intervalo_ativo
        and intervalo_valor
        and intervalo_valor > 0
        and intervalo_unidade
        and horario_fim
    ):

        if intervalo_unidade == "minutes":

            incremento = timedelta(
                minutes=intervalo_valor
            )

        elif intervalo_unidade == "hours":

            incremento = timedelta(
                hours=intervalo_valor
            )

        else:
            incremento = None


        if incremento:

            # ------------------------------------------------
            # DIÁRIO COM INTERVALO
            # ------------------------------------------------

            if schedule.tipo == "daily":

            # Se a data de início ainda está no futuro,
            # a primeira execução deve acontecer exatamente
            # na data de início.

                if inicio > agora:
                    return horario_inicial

                candidato = _horario_para_datetime(
                    agora,
                    schedule.horario
                )

                if candidato is None:
                    return None

                if candidato <= agora:
                    candidato += timedelta(days=1)

                return candidato


            # ------------------------------------------------
            # SEMANAL COM INTERVALO
            # ------------------------------------------------

            if schedule.tipo == "weekly":

                dias = {
                    "mon": 0,
                    "tue": 1,
                    "wed": 2,
                    "thu": 3,
                    "fri": 4,
                    "sat": 5,
                    "sun": 6
                }

                selecionados = set(
                    dia.strip().lower()
                    for dia in (
                        schedule.dias_semana or ""
                    ).split(",")
                    if dia.strip()
                )

                numeros = sorted(
                    dias[dia]
                    for dia in selecionados
                    if dia in dias
                )

                if not numeros:
                    return None

                for deslocamento in range(0, 8):

                    data = (
                        agora +
                        timedelta(days=deslocamento)
                    ).replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    )

                    if data.weekday() not in numeros:
                        continue

                    inicio_dia = _horario_para_datetime(
                        data,
                        schedule.horario
                    )

                    fim_dia = _horario_para_datetime(
                        data,
                        horario_fim
                    )

                    if (
                        inicio_dia is None
                        or fim_dia is None
                    ):
                        continue

                    if inicio_dia < inicio:
                        continue

                    if agora < inicio_dia:
                        return inicio_dia

                    candidato = inicio_dia

                    while candidato <= agora:
                        candidato += incremento

                    if candidato <= fim_dia:
                        return candidato

                return None


            # ------------------------------------------------
            # MENSAL COM INTERVALO
            # ------------------------------------------------

            if schedule.tipo == "monthly":

                dia_mes = inicio.day

                ano = agora.year
                mes = agora.month

                for _ in range(24):

                    try:

                        data = datetime(
                            ano,
                            mes,
                            dia_mes
                        )

                    except ValueError:

                        data = None


                    if data is not None:

                        inicio_dia = _horario_para_datetime(
                            data,
                            schedule.horario
                        )

                        fim_dia = _horario_para_datetime(
                            data,
                            horario_fim
                        )

                        if (
                            inicio_dia is not None
                            and fim_dia is not None
                            and inicio_dia >= inicio
                        ):

                            if agora < inicio_dia:
                                return inicio_dia

                            candidato = inicio_dia

                            while candidato <= agora:
                                candidato += incremento

                            if candidato <= fim_dia:
                                return candidato

                    mes += 1

                    if mes > 12:
                        mes = 1
                        ano += 1

                return None


    # ========================================================
    # DIÁRIO SEM INTERVALO
    # ========================================================

    if schedule.tipo == "daily":

        candidato = _horario_para_datetime(
            agora,
            schedule.horario
        )

        if candidato is None:
            return None

        if candidato < inicio:
            candidato = horario_inicial

        if candidato <= agora:
            candidato += timedelta(days=1)

        return candidato


    # ========================================================
    # SEMANAL SEM INTERVALO
    # ========================================================

    if schedule.tipo == "weekly":

        dias = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6
        }

        selecionados = set(
            dia.strip().lower()
            for dia in (
                schedule.dias_semana or ""
            ).split(",")
            if dia.strip()
        )

        numeros = sorted(
            dias[dia]
            for dia in selecionados
            if dia in dias
        )

        if not numeros:
            return None

        for deslocamento in range(0, 8):

            data = agora + timedelta(
                days=deslocamento
            )

            candidato = _horario_para_datetime(
                data,
                schedule.horario
            )

            if (
                data.weekday() in numeros
                and candidato is not None
                and candidato >= inicio
                and candidato > agora
            ):
                return candidato

        return None


    # ========================================================
    # MENSAL SEM INTERVALO
    # ========================================================

    if schedule.tipo == "monthly":

        dia_mes = inicio.day

        ano = agora.year
        mes = agora.month

        for _ in range(24):

            try:

                candidato_base = datetime(
                    ano,
                    mes,
                    dia_mes
                )

            except ValueError:

                candidato_base = None


            if candidato_base is not None:

                candidato = _horario_para_datetime(
                    candidato_base,
                    schedule.horario
                )

                if (
                    candidato is not None
                    and candidato >= inicio
                    and candidato > agora
                ):
                    return candidato

            mes += 1

            if mes > 12:
                mes = 1
                ano += 1

        return None


    return None

def proxima_execucao_apos_execucao(schedule, agora=None):

    if agora is None:
        agora = datetime.now()

    # ========================================================
    # UMA VEZ
    # ========================================================

    if schedule.tipo == "once":
        return None


    # ========================================================
    # COM INTERVALO
    # ========================================================

    intervalo_ativo = getattr(
        schedule,
        "intervalo_ativo",
        0
    )

    intervalo_valor = getattr(
        schedule,
        "intervalo_valor",
        None
    )

    intervalo_unidade = getattr(
        schedule,
        "intervalo_unidade",
        None
    )

    horario_fim = getattr(
        schedule,
        "horario_fim",
        None
    )


    if (
        intervalo_ativo
        and intervalo_valor
        and intervalo_valor > 0
        and intervalo_unidade
        and horario_fim
    ):

        if intervalo_unidade == "minutes":

            incremento = timedelta(
                minutes=intervalo_valor
            )

        elif intervalo_unidade == "hours":

            incremento = timedelta(
                hours=intervalo_valor
            )

        else:
            incremento = None


        if incremento:

            proxima = agora + incremento

            # Se ainda estiver dentro do período,
            # retorna a próxima ocorrência.

            fim = _horario_para_datetime(
                agora,
                horario_fim
            )

            if (
                fim is not None
                and proxima <= fim
            ):
                return proxima


    # ========================================================
    # SEM INTERVALO / FIM DO INTERVALO
    # ========================================================

    return calcular_proxima_execucao(
        schedule,
        agora
    )

def executar_agendamento(schedule_id):

    db = SessionLocal()

    try:

        schedule = db.query(
            Schedule
        ).filter(
            Schedule.id == schedule_id,
            Schedule.ativo == 1
        ).first()

        if not schedule:
            return

        robot_id = schedule.robot_id
        agent_id_agendado = schedule.agent_id

    finally:
        db.close()

    # ========================================================
    # ESCOLHA DO AGENT
    # ========================================================

    agent_ids = []

    db = SessionLocal()

    try:

        if agent_id_agendado:

            agent = db.query(Agent).filter(
                Agent.agent_id == agent_id_agendado
            ).first()

            if agent and agent.status == "online":
                agent_ids.append(agent.agent_id)

        else:

            agents = db.query(Agent).filter(
                Agent.status == "online"
            ).order_by(
                Agent.name
            ).all()

            agent_ids = [
                agent.agent_id
                for agent in agents
            ]

    finally:
        db.close()

    if not agent_ids:
        return {
            "status": "waiting",
            "message": "Nenhum Agent online"
        }

    # ========================================================
    # TENTA EXECUTAR
    # ========================================================

    ultimo_resultado = None

    for agent_id in agent_ids:

        resultado = run_agent_robot(
            agent_id,
            ExecutionRequest(
                robot_id=robot_id
            )
        )

        ultimo_resultado = resultado

        if resultado.get("status") == "success":

            agora = datetime.now()

            db = SessionLocal()

            try:

                schedule = db.query(
                    Schedule
                ).filter(
                    Schedule.id == schedule_id
                ).first()

                if schedule:

                    schedule.ultima_execucao = agora

                    if schedule.tipo == "once":

                        schedule.ativo = 0
                        schedule.proxima_execucao = None

                    else:

                        schedule.proxima_execucao = \
                            proxima_execucao_apos_execucao(
                                schedule,
                                agora
                            )

                    db.commit()

            finally:
                db.close()

            return resultado

        # Se esse Agent estiver ocupado, tenta o próximo.
        if resultado.get("message") == \
                "Agent não está disponível para execução":
            continue

        # Erro diferente de Agent ocupado.
        # Não tenta outro Agent automaticamente quando um Agent
        # específico foi escolhido.
        if agent_id_agendado:
            break

    return ultimo_resultado or {
        "status": "waiting",
        "message": "Nenhum Agent disponível"
    }


def scheduler_loop():

    while True:

        try:

            if scheduler_lock.acquire(blocking=False):

                try:

                    agora = datetime.now()

                    db = SessionLocal()

                    try:

                        schedules = db.query(
                            Schedule
                        ).filter(
                            Schedule.ativo == 1
                        ).all()

                        # Inicializa a próxima execução dos
                        # agendamentos antigos que ainda estão NULL.
                        for schedule in schedules:

                            if schedule.proxima_execucao is None:

                                proxima = calcular_proxima_execucao(
                                    schedule,
                                    agora
                                )

                                if proxima is not None:
                                    schedule.proxima_execucao = proxima

                        db.commit()

                        vencidos = [
                            schedule.id
                            for schedule in sorted(
                                schedules,
                                key=lambda s: s.proxima_execucao
                            )
                            if (
                                schedule.proxima_execucao is not None
                                and schedule.proxima_execucao <= agora
                            )
                        ]

                    finally:
                        db.close()

                    for schedule_id in vencidos:
                        executar_agendamento(schedule_id)

                finally:
                    scheduler_lock.release()

        except Exception as error:
            print(
                f"[SCHEDULER] Erro: {error}"
            )

        time.sleep(5)


def iniciar_scheduler():

    global scheduler_thread

    if scheduler_thread is not None and scheduler_thread.is_alive():
        return

    scheduler_thread = threading.Thread(
        target=scheduler_loop,
        daemon=True,
        name="RPA-Scheduler"
    )

    scheduler_thread.start()




# ============================================================
# ATIVAR / DESATIVAR AGENDAMENTO
# ============================================================

@app.put("/api/schedules/{schedule_id}/status")
def alterar_status_schedule(
    schedule_id: int,
    ativo: bool
):

    db = SessionLocal()

    try:

        schedule = db.query(
            Schedule
        ).filter(
            Schedule.id == schedule_id
        ).first()

        if not schedule:

            return {
                "status": "error",
                "message": "Agendamento não encontrado",
                "schedule_id": schedule_id
            }

        schedule.ativo = 1 if ativo else 0

        db.commit()
        db.refresh(schedule)

        return {
            "status": "success",
            "message": (
                "Agendamento ativado com sucesso"
                if ativo
                else
                "Agendamento desativado com sucesso"
            ),
            "schedule_id": schedule.id,
            "ativo": bool(schedule.ativo)
        }

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível alterar o status do agendamento",
            "error": str(error)
        }

    finally:

        db.close()
# ============================================================
# EXCLUIR AGENDAMENTO
# ============================================================

@app.delete("/api/schedules/{schedule_id}")
def delete_schedule(schedule_id: int):

    db = SessionLocal()

    try:

        schedule = db.query(Schedule).filter(
            Schedule.id == schedule_id
        ).first()

        if not schedule:

            return {
                "status": "error",
                "message": "Agendamento não encontrado",
                "schedule_id": schedule_id
            }

        db.delete(schedule)

        db.commit()

        return {
            "status": "success",
            "message": "Agendamento excluído com sucesso",
            "schedule_id": schedule_id
        }

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível excluir o agendamento",
            "schedule_id": schedule_id,
            "error": str(error)
        }

    finally:

        db.close()
# ============================================================
# ENDPOINT CRIAR AGENDAMENTO
# ============================================================

class ScheduleCreateRequest(BaseModel):

    robot_id: int

    agent_id: str | None = None

    tipo: str

    data_inicio: str

    horario: str

    dias_semana: str | None = None

    intervalo_ativo: bool = False

    intervalo_valor: int | None = None

    intervalo_unidade: str | None = None

    horario_fim: str | None = None


@app.post("/api/schedules")
def criar_agendamento(
    request: ScheduleCreateRequest
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Valida robô
        # ----------------------------------------------------

        robot = db.query(Robot).filter(
            Robot.id == request.robot_id
        ).first()

        if not robot:

            return {
                "status": "error",
                "message": "Robô não encontrado"
            }


        # ----------------------------------------------------
        # Valida Agent, caso tenha sido informado
        # ----------------------------------------------------

        if request.agent_id:

            agent = db.query(Agent).filter(
                Agent.agent_id == request.agent_id
            ).first()

            if not agent:

                return {
                    "status": "error",
                    "message": "Agent não encontrado"
                }


        # ----------------------------------------------------
        # Valida tipo
        # ----------------------------------------------------

        tipos_permitidos = [
            "once",
            "daily",
            "weekly",
            "monthly"
        ]

        if request.tipo not in tipos_permitidos:

            return {
                "status": "error",
                "message": "Tipo de agendamento inválido"
            }


        # ----------------------------------------------------
        # Converte data
        # ----------------------------------------------------

        try:

            data_inicio = datetime.fromisoformat(
                request.data_inicio
            )

        except ValueError:

            return {
                "status": "error",
                "message": "Data de início inválida"
            }


        # ----------------------------------------------------
        # Calcula a primeira execução
        # ----------------------------------------------------

        data_horario = _horario_para_datetime(
            data_inicio,
            request.horario
        )

        if data_horario is None:

            return {
                "status": "error",
                "message": "Horário inválido. Use HH:MM."
            }

        # ----------------------------------------------------
        # Valida se data/horário já passou
        # ----------------------------------------------------

        agora = datetime.now()

        if data_horario <= agora:
            return {
                "status": "error",
                "message": (
                    "O horário informado já passou. "
                    "Selecione uma data e horário futuros."
                )
            }

        # Para uma vez, a data/horário informados representam
        # exatamente a execução.
        if request.tipo == "once":

            proxima_execucao = data_horario

        else:

            proxima_execucao = calcular_proxima_execucao(
                Schedule(
                    robot_id=request.robot_id,
                    agent_id=request.agent_id,
                    tipo=request.tipo,
                    data_inicio=data_inicio,
                    horario=request.horario,
                    dias_semana=request.dias_semana,

                    intervalo_ativo=1 if request.intervalo_ativo else 0,
                    intervalo_valor=request.intervalo_valor,
                    intervalo_unidade=request.intervalo_unidade,
                    horario_fim=request.horario_fim
                ),
                datetime.now()
            )

        if proxima_execucao is None:

            return {
                "status": "error",
                "message": "Não foi possível calcular a próxima execução. Verifique a data, horário e dias selecionados."
            }

        # ----------------------------------------------------
        # Cria agendamento
        # ----------------------------------------------------

        schedule = Schedule(
        robot_id=request.robot_id,
        agent_id=request.agent_id,
        tipo=request.tipo,
        data_inicio=data_inicio,
        horario=request.horario,
        dias_semana=request.dias_semana,

        intervalo_ativo=1 if request.intervalo_ativo else 0,
        intervalo_valor=request.intervalo_valor,
        intervalo_unidade=request.intervalo_unidade,
        horario_fim=request.horario_fim,

        ativo=1,
        proxima_execucao=proxima_execucao,
        ultima_execucao=None
    )

        db.add(schedule)

        db.commit()

        db.refresh(schedule)


        return {

            "status": "success",

            "message": "Agendamento criado com sucesso",

            "schedule": {

                "id": schedule.id,

                "robot_id": schedule.robot_id,

                "agent_id": schedule.agent_id,

                "tipo": schedule.tipo,

                "data_inicio":
                    schedule.data_inicio.isoformat(),

                "horario": schedule.horario,

                "dias_semana":
                    schedule.dias_semana,

                "intervalo_ativo":
                bool(schedule.intervalo_ativo),

                "intervalo_valor":
                    schedule.intervalo_valor,

                "intervalo_unidade":
                    schedule.intervalo_unidade,

                "horario_fim":
                    schedule.horario_fim,

                "ativo":
                    bool(schedule.ativo),

                "proxima_execucao":
                    schedule.proxima_execucao.isoformat()
                    if schedule.proxima_execucao
                    else None

            }

        }

    except Exception as error:

        db.rollback()

        return {

            "status": "error",

            "message": "Não foi possível criar o agendamento",

            "error": str(error)

        }

    finally:

        db.close()

# ============================================================
# OPÇÕES PARA NOVO AGENDAMENTO
# ============================================================

@app.get("/api/schedules/options")
def opcoes_agendamento():

    db = SessionLocal()

    try:

        # ====================================================
        # ROBÔS
        # ====================================================

        robots_db = db.query(
            Robot
        ).order_by(
            Robot.name
        ).all()


        robots = []

        for robot in robots_db:

            # --------------------------------------------
            # Verifica se o arquivo físico existe
            # --------------------------------------------

            if not robot.file_path:
                continue


            caminho = Path(
                robot.file_path
            )


            if not caminho.exists():
                continue


            # --------------------------------------------
            # Robô válido
            # --------------------------------------------

            robots.append({

                "id":
                    robot.id,

                "name":
                    robot.name

            })


        # ====================================================
        # AGENTS
        # ====================================================

        agents_db = db.query(
            Agent
        ).order_by(
            Agent.name
        ).all()


        agents = [

            {

                "agent_id":
                    agent.agent_id,

                "name":
                    agent.name,

                "status":
                    agent.status

            }

            for agent in agents_db

        ]


        # ====================================================
        # RETORNO
        # ====================================================

        return {

            "status":
                "success",

            "robots":
                robots,

            "agents":
                agents

        }

    finally:

        db.close()

# ============================================================
# ENDPOINT - CONSULTAR AGENDAMENTO
# ============================================================
# ============================================================
# CONSULTAR AGENDAMENTO
# ============================================================

@app.get("/api/schedules/{schedule_id}")
def get_schedule(schedule_id: int):

    db = SessionLocal()

    try:

        schedule = db.query(
            Schedule
        ).filter(
            Schedule.id == schedule_id
        ).first()

        if not schedule:

            return {
                "status": "error",
                "message": "Agendamento não encontrado",
                "schedule_id": schedule_id
            }


        robot = db.query(
            Robot
        ).filter(
            Robot.id == schedule.robot_id
        ).first()


        agent = None

        if schedule.agent_id:

            agent = db.query(
                Agent
            ).filter(
                Agent.agent_id == schedule.agent_id
            ).first()


        return {
            "status": "success",

            "schedule": {

                "id":
                    schedule.id,

                "robot_id":
                    schedule.robot_id,

                "robot_name":
                    robot.name
                    if robot
                    else "",

                "agent_id":
                    schedule.agent_id,

                "agent_name":
                    agent.name
                    if agent
                    else "Automático",

                "tipo":
                    schedule.tipo,

                "data_inicio":
                    schedule.data_inicio.isoformat()
                    if schedule.data_inicio
                    else None,

                "horario":
                    schedule.horario,

                "dias_semana":
                    schedule.dias_semana,

                "intervalo_ativo":
                    bool(
                        schedule.intervalo_ativo
                    ),

                "intervalo_valor":
                    schedule.intervalo_valor,

                "intervalo_unidade":
                    schedule.intervalo_unidade,

                "horario_fim":
                    schedule.horario_fim,

                "proxima_execucao":
                    schedule.proxima_execucao.isoformat()
                    if schedule.proxima_execucao
                    else None,

                "ativo":
                    bool(
                        schedule.ativo
                    )

            }
        }


    except Exception as error:

        return {
            "status": "error",
            "message": "Erro ao consultar agendamento",
            "schedule_id": schedule_id,
            "error": str(error)
        }


    finally:

        db.close()
# ============================================================
# ATUALIZAR AGENDAMENTO
# ============================================================

@app.put("/api/schedules/{schedule_id}")
def update_schedule(
    schedule_id: int,
    request: ScheduleCreateRequest
):

    db = SessionLocal()

    try:

        schedule = db.query(Schedule).filter(
            Schedule.id == schedule_id
        ).first()

        if not schedule:
            return {
                "status": "error",
                "message": "Agendamento não encontrado",
                "schedule_id": schedule_id
            }

        data_inicio = datetime.fromisoformat(
            request.data_inicio
        )

        schedule.robot_id = request.robot_id
        schedule.agent_id = request.agent_id
        schedule.tipo = request.tipo
        schedule.data_inicio = data_inicio
        schedule.horario = request.horario
        schedule.dias_semana = request.dias_semana

        schedule.intervalo_ativo = (
            1 if request.intervalo_ativo else 0
        )

        schedule.intervalo_valor = (
            request.intervalo_valor
        )

        schedule.intervalo_unidade = (
            request.intervalo_unidade
        )

        schedule.horario_fim = (
            request.horario_fim
        )

        schedule.proxima_execucao = (
            calcular_proxima_execucao(
                schedule,
                datetime.now()
            )
        )

        db.commit()
        db.refresh(schedule)

        return {
            "status": "success",
            "message": "Agendamento atualizado com sucesso",
            "schedule_id": schedule.id
        }

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível atualizar o agendamento",
            "error": str(error)
        }

    finally:

        db.close()



# ============================================================
# ATIVAR / DESATIVAR AGENDAMENTO
# ============================================================

@app.put("/api/schedules/{schedule_id}/status")
def alterar_status_schedule(
    schedule_id: int,
    ativo: bool
):

    db = SessionLocal()

    try:

        schedule = db.query(
            Schedule
        ).filter(
            Schedule.id == schedule_id
        ).first()

        if not schedule:

            return {
                "status": "error",
                "message": "Agendamento não encontrado",
                "schedule_id": schedule_id
            }

        schedule.ativo = 1 if ativo else 0

        db.commit()
        db.refresh(schedule)

        return {
            "status": "success",
            "message": (
                "Agendamento ativado com sucesso"
                if ativo
                else "Agendamento desativado com sucesso"
            ),
            "schedule_id": schedule.id,
            "ativo": bool(schedule.ativo)
        }

    except Exception as error:

        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível alterar o status do agendamento",
            "schedule_id": schedule_id,
            "error": str(error)
        }

    finally:

        db.close()
# ============================================================
# INICIALIZAÇÃO DO SCHEDULER
# ============================================================

@app.on_event("startup")
def startup_scheduler():

    iniciar_scheduler()
    threading.Thread(
        target=monitorar_agents,
        daemon=True
    ).start()


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("RPA CONTROL ROOM")
    print("=" * 60)
    print("Porta: 9000")
    print("=" * 60)
    print()

    threading.Thread(
        target=monitorar_agents,
        daemon=True
    ).start()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000
    )
