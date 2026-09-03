# ============================================================
# ROUTER DE EXECUÇÕES
# ============================================================
#
# Este arquivo concentra as APIs relacionadas à execução de robôs.
#
# Importante:
# Não usamos prefix="/executions" porque algumas rotas existentes
# pertencem ao fluxo de execução de um Agent e precisam manter
# exatamente as URLs atuais, por exemplo:
#
#   /agents/{agent_id}/execution/run
#   /agents/{agent_id}/execution/status
#   /agents/{agent_id}/execution/stop
#
# Assim, a migração não altera o contrato atual da API.
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel
from database import SessionLocal
from models import Agent, Robot, Execution
from pathlib import Path
from datetime import datetime
import requests
import logging

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["Executions"]
)


# Logger do Control Room.
# O main.py configura esse mesmo nome de logger.
logger = logging.getLogger("control_room")


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

@router.post("/agents/{agent_id}/execution/run")
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
        # ============================================================
        # REGISTRA SOLICITAÇÃO DE EXECUÇÃO NO LOG OPERACIONAL
        # ============================================================

        logger.info(
            f"[EXECUTION] Execução solicitada | "
            f"ID: {execution_id} | "
            f"Robô: {robot_name} | "
            f"Agent: {agent.name} | "
            f"Agent ID: {agent_id}"
        )

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
    logger.info(
    f"[EXECUTION] Comando enviado ao Agent | "
    f"ID: {execution_id} | "
    f"Robô: {robot_name} | "
    f"Agent: {agent.name}"
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
    # 12.0 BUSCA O PID REAL DA EXECUÇÃO
    # ========================================================

    pid = execution_response.get("pid")
    # ========================================================
    # 12.1 SALVA O PID NO BANCO
    # ========================================================

    if pid is not None:

        db = SessionLocal()

        try:
            execucao = db.query(Execution).filter(
                Execution.id == execution_id
            ).first()

            if execucao:
                execucao.pid = pid
                db.commit()

                logger.info(
                    f"[EXECUTION] PID salvo | "
                    f"Execution ID: {execution_id} | "
                    f"PID: {pid}"
                )

        finally:
            db.close()
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

@router.get("/agents/{agent_id}/execution/status")
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

@router.post("/agents/{agent_id}/execution/stop")
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
# RECEBE RESULTADO DA EXECUÇÃO DO AGENT
# ============================================================

class ExecutionResultRequest(BaseModel):
    # Identifica o Agent que enviou o resultado.
    execution_id: int
    agent_id: str

    # Resultado final da execução.
    status: str
    message: str

    # Datas enviadas pelo Agent.
    started_at: str
    finished_at: str


@router.post("/executions/{execution_id}/result")
def receber_resultado_execucao(
    execution_id: int,
    request: ExecutionResultRequest
):
    # Abre conexão com o banco.
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
        # Fecha a conexão com o banco.
        db.close()

# ============================================================
# ENDPOINT LISTAR EXECUÇÕES EM ANDAMENTO
# ============================================================

@router.get("/executions")
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
                # ID do Agent que está executando o robô.
                "agent_id": execution.agent_id,
                # PID do processo Python responsável pela execução.
                "pid": execution.pid,

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

@router.get("/executions/history")
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
