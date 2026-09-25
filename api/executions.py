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
from pathlib import Path
from datetime import datetime

# Logging utilizado pelos endpoints e operações que ainda
# permanecem sob responsabilidade deste router.
import logging

import requests
import uuid
from fastapi import APIRouter, Depends
from database import SessionLocal
# Modelos utilizados pelas APIs de execução.
# User será usado para representar o usuário autenticado
# que solicitou uma execução manual.
# Modelos utilizados pelas APIs de execução.
# RobotFolder será usado para montar o caminho completo
# da pasta do robô, incluindo todas as subpastas.
from models import (
    Agent,
    Robot,
    Execution,
    User,
    RobotFolder,
    AutomationProject
)



# Dependência responsável por validar
# a sessão do usuário autenticado.
from auth.dependencies import get_usuario_atual
# Dependência usada para validar as permissões RBAC do usuário.
# Nesta task será utilizada para exigir a permissão
# "Executions:create" antes de iniciar um robô.
from auth.permissions import require_permission


# ============================================================
# EXECUTIONS - MÓDULOS INTERNOS
# ============================================================
#
# A lógica de execução, contratos e contexto de observabilidade
# foram separados do router HTTP para manter responsabilidades
# independentes sem alterar o comportamento da API.
# ============================================================

from schemas.executions import (
    ExecutionRequest,
    DevelopmentExecutionRequest,
)

from executions.logging_context import (
    obter_contexto_execucao_log,
)

from executions.service import (
    _executar_robot,
)
# Recupera o token técnico do Agent somente em memória
# para chamadas Control Room -> Agent.
from agents.token_security import descriptografar_agent_token

# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    tags=["Executions"],
    dependencies=[
        Depends(get_usuario_atual)
    ]
)




# ============================================================
# PROCESSADOR DA FILA DE EXECUÇÕES
# ============================================================
# Logger do Control Room.
# O main.py configura esse mesmo nome de logger.
logger = logging.getLogger("control_room")


# ============================================================
# EXECUTAR ROBÔ
# ============================================================
#
# Esta é a API pública utilizada para iniciar um robô
# manualmente pelo usuário do Control Room.
#
# O usuário autenticado é obtido pelo backend através
# de get_usuario_atual().
#
# Depois disso, o ID do usuário autenticado é colocado
# no ExecutionRequest antes da execução continuar.
#
# Isso impede que o frontend escolha arbitrariamente
# qual usuário ficará associado à Execution.
# ============================================================

@router.post("/agents/{agent_id}/execution/run",
    summary="Executar robô no Agent",
    description=(
        "Inicia a execução de um robô em um Agent específico. "
        "O Control Room localiza o Agent e o robô, verifica a "
        "disponibilidade do Agent, realiza o deploy do robô e "
        "solicita sua execução. "
        "Requer autenticação do usuário e a permissão "
        "'Executions:execute'."
    )
)
def run_agent_robot(
    agent_id: str,
    request: ExecutionRequest,
    usuario: User = Depends(
        require_permission("Executions", "execute")
    )
):
    """
    Inicia a execução de um robô em um Agent.

    Parâmetros:
        agent_id:
            Identificador único do Agent onde o robô será executado.

        request:
            Dados necessários para identificar o robô a ser executado.

    Permissão necessária:
        Executions:execute
    """
    # ========================================================
    # EXECUÇÃO MANUAL VIA API
    # ========================================================
    #
    # Esta função é chamada pelo FastAPI quando o usuário
    # clica em "Executar" no Control Room.
    #
    # O FastAPI resolve automaticamente:
    #
    #     Depends(get_usuario_atual)
    #
    # e entrega aqui o objeto User autenticado.
    #
    # O user_id é obtido do usuário autenticado e NÃO do
    # frontend.
    #
    # Depois encaminhamos a execução para a função interna,
    # que também poderá ser utilizada pelo Worker.
    # ========================================================

    request.user_id = usuario.id

    return _executar_robot(
        agent_id=agent_id,
        request=request
    )


# ============================================================
# EXECUTAR PROJETO DE DESENVOLVIMENTO
# ============================================================
@router.post(
    "/development/projects/{project_id}/execution/run",
    summary="Executar projeto de Desenvolvimento",
    description=(
        "Monta um snapshot executável do AutomationProject, incluindo "
        "as versões fixadas das Libraries, e envia o pacote ao Agent."
    ),
    dependencies=[
        Depends(
            require_permission("Development", "edit")
        )
    ]
)
def run_development_project(
    project_id: int,
    request: DevelopmentExecutionRequest,
    usuario: User = Depends(
        require_permission("Executions", "execute")
    )
):
    """
    Executa um AutomationProject sem criar um Robot publicado.

    O usuário precisa possuir:
    - Development:edit
    - Executions:execute

    O pacote é montado pelo Project Packager e contém exatamente
    as LibraryVersions fixadas no projeto.
    """

    return _executar_robot(
        agent_id=request.agent_id,
        request=ExecutionRequest(
            source_type="development",
            project_id=project_id,
            user_id=usuario.id
        )
    )



# ============================================================
# ENDPOINT CONSULTAR STATUS DE EXECUÇÃO DO AGENT
# ============================================================

@router.get(
    "/agents/{agent_id}/execution/status",
    summary="Consultar status da execução",
    description=(
        "Consulta o status atual da execução associada a um Agent. "
        "O Agent é identificado pelo parâmetro agent_id."
    )
)
def get_execution_status(
    agent_id: str,

    # Consultar o estado atual de uma execução expõe
    # informações do domínio Executions.
    usuario: User = Depends(
        require_permission("Executions", "view")
    ),
):
    """
    Consulta o status atual da execução do Agent.

    Parâmetros:
        agent_id:
            Identificador único do Agent.

    Retorna as informações disponíveis sobre a execução atual
    do Agent.
    """

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
        # Recupera a credencial somente para a chamada ao Agent.
        agent_token = descriptografar_agent_token(
            agent.agent_token_encrypted
        )

        # Consulta somente o estado atual do Agent.
        #
        # Este endpoint NÃO realiza STOP e, portanto,
        # não envia execution_id no corpo da requisição.
        response = requests.get(
            agent_url,
            headers={
                "Authorization": f"Bearer {agent_token}"
            },
            timeout=10
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
#
# Permite parar uma execução somente para usuários que
# possuem a permissão:
#
#     Executions:stop
#
# A autenticação do usuário continua sendo feita pelo router.
# Aqui adicionamos a autorização específica para a operação
# de STOP.
# ============================================================
# ============================================================
# ENDPOINT PARAR EXECUÇÃO DO AGENT
# ============================================================
#
# Interrompe uma Execution específica que esteja atualmente
# em execução no Agent informado.
#
# Segurança:
# - exige Executions:stop;
# - valida se a Execution existe;
# - valida se pertence ao Agent informado;
# - aceita STOP somente para status "running";
# - envia o execution_id ao Agent para impedir que um comando
#   atrasado encerre uma execução diferente.
# ============================================================

@router.post(
    "/agents/{agent_id}/execution/stop",
    summary="Parar execução do Agent",
    description=(
        "Solicita ao Agent a interrupção de uma execução específica. "
        "O Agent e a Execution são validados antes do envio do comando."
    )
)
def stop_agent_execution(
    agent_id: str,
    execution_id: int,

    # Parar uma execução exige autorização específica.
    usuario: User = Depends(
        require_permission("Executions", "stop")
    ),
):
    """
    Solicita a interrupção de uma Execution específica.

    Parâmetros:
        agent_id:
            Agent responsável pela execução.

        execution_id:
            ID da Execution que deverá ser interrompida.

    O execution_id é validado tanto no Control Room quanto
    posteriormente pelo próprio Agent.
    """

    # ========================================================
    # 1. BUSCA AGENT E EXECUTION
    # ========================================================
    #
    # Fazemos as duas consultas dentro da mesma sessão.
    # ========================================================

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


        execucao = db.query(Execution).filter(
            Execution.id == execution_id
        ).first()

        if not execucao:

            return {
                "status": "error",
                "message": "Execução não encontrada",
                "execution_id": execution_id
            }


        # ====================================================
        # 2. VALIDA AGENT DA EXECUÇÃO
        # ====================================================

        if execucao.agent_id != agent_id:

            return {
                "status": "error",
                "message": (
                    "A execução informada não pertence "
                    "ao Agent solicitado."
                ),
                "execution_id": execution_id,
                "agent_id": agent_id
            }


        # ====================================================
        # 3. VALIDA ESTADO
        # ====================================================

        if execucao.status != "running":

            return {
                "status": "error",
                "message": (
                    "Somente uma execução em estado running "
                    "pode receber comando de stop."
                ),
                "execution_id": execution_id,
                "execution_status": execucao.status
            }


        # ====================================================
        # 4. COPIA DADOS NECESSÁRIOS ANTES DE FECHAR A SESSÃO
        # ====================================================
        #
        # Evita utilizar o objeto ORM depois que a sessão
        # SQLAlchemy for encerrada.
        # ====================================================

        agent_host = agent.host
        agent_port = agent.port
        agent_token_encrypted = agent.agent_token_encrypted

    finally:

        db.close()


    # ========================================================
    # 5. MONTA URL DO AGENT
    # ========================================================

    stop_url = (
        f"http://{agent_host}:{agent_port}"
        "/execution/stop"
    )


    # ========================================================
    # 6. ENVIA STOP PARA O AGENT
    # ========================================================

    try:

        # O token é descriptografado somente em memória
        # durante a comunicação Control Room -> Agent.
        agent_token = descriptografar_agent_token(
            agent_token_encrypted
        )

        response = requests.post(
            stop_url,

            # O Agent valida este ID contra a execução
            # realmente ativa antes de encerrar o processo.
            json={
                "execution_id": execution_id
            },

            headers={
                "Authorization": f"Bearer {agent_token}"
            },

            timeout=10
        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": (
                "Não foi possível enviar comando "
                "de stop para o Agent"
            ),
            "agent_id": agent_id,
            "execution_id": execution_id,
            "error": str(error)
        }


    # ========================================================
    # 7. VALIDA RESPOSTA HTTP
    # ========================================================

    if response.status_code != 200:

        return {
            "status": "error",
            "message": (
                "Agent respondeu com erro ao parar o Robot"
            ),
            "agent_id": agent_id,
            "execution_id": execution_id,
            "http_status": response.status_code,
            "response": response.text
        }


    # ========================================================
    # 8. LÊ RESPOSTA DO AGENT
    # ========================================================

    try:

        resultado = response.json()

    except ValueError:

        return {
            "status": "error",
            "message": (
                "Agent retornou JSON inválido "
                "ao parar o Robot"
            ),
            "agent_id": agent_id,
            "execution_id": execution_id
        }


    # ========================================================
    # 9. VALIDA RESULTADO
    # ========================================================

    if resultado.get("status") != "success":

        return {
            "status": "error",
            "message": resultado.get(
                "message",
                "Agent recusou o comando de stop"
            ),
            "agent_id": agent_id,
            "execution_id": execution_id,
            "agent_response": resultado
        }


    # ========================================================
    # 10. RETORNO
    # ========================================================

    return {
        "status": "success",
        "message": "Comando de stop enviado para o Agent",
        "agent_id": agent_id,
        "execution_id": execution_id,
        "agent_response": resultado
    }
# ============================================================
# ENDPOINT CANCELAR EXECUÇÃO DA FILA
# ============================================================
#
# Cancela SOMENTE execuções que ainda estão "queued".
#
# IMPORTANTE:
# - Não envia comando para o Agent.
# - Não interfere em nenhuma execução "running".
# - Apenas remove a execução da fila lógica.
# ============================================================

# ============================================================
# CANCELAR EXECUÇÃO DA FILA
# ============================================================
#
# Esta API cancela uma execução que ainda está aguardando
# na fila ("queued").
#
# A permissão específica para essa ação no catálogo RBAC
# de Executions é:
#
#     Executions:cancel
#
# O usuário precisa possuir essa permissão antes que
# a função de cancelamento seja executada.
# ============================================================

@router.post(
    "/executions/{execution_id}/cancel",
    summary="Cancelar execução da fila",
    description=(
        "Cancela uma execução que ainda está aguardando na fila. "
        "Somente execuções com status 'queued' podem ser canceladas. "
        "O cancelamento não envia comando ao Agent e não interfere "
        "em execuções que já estão em andamento."
    )
)
def cancel_execution(
    execution_id: int,

    # Cancelar uma execução queued altera seu estado e exige
    # autorização específica para cancelamento.
    usuario: User = Depends(
        require_permission("Executions", "cancel")
    ),
):
    """
    Cancela uma execução que está aguardando na fila.

    Parâmetros:
        execution_id:
            Identificador único da execução.

    A execução somente pode ser cancelada enquanto estiver
    com status 'queued'.
    """

    db = SessionLocal()

    try:

        # ========================================================
        # 1. BUSCA A EXECUÇÃO
        # ========================================================

        execucao = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id
            )
            .first()
        )

        if not execucao:

            return {
                "status": "error",
                "message": "Execução não encontrada",
                "execution_id": execution_id
            }

        # ========================================================
        # 2. SÓ PODE CANCELAR SE ESTIVER NA FILA
        # ========================================================

        if execucao.status != "queued":

            return {
                "status": "error",
                "message": (
                    "Somente execuções que estão na fila "
                    "podem ser canceladas."
                ),
                "execution_id": execution_id,
                "status_atual": execucao.status
            }

        # ========================================================
        # 3. CANCELA A EXECUÇÃO
        # ========================================================

        execucao.status = "cancelled"

        execucao.finished_at = datetime.now()

        execucao.error_message = (
            "Execução cancelada pelo usuário."
        )

        db.commit()

        # ========================================================
        # MANTÉM OS IDENTIFICADORES CARREGADOS APÓS O COMMIT
        # ========================================================
        #
        # Após o commit, o SQLAlchemy pode expirar os atributos
        # do objeto ORM.
        #
        # Como ainda precisamos desses IDs para montar o log,
        # acessamos os valores enquanto a sessão continua aberta.
        # ========================================================

        execucao.robot_id
        execucao.agent_id
        execucao.user_id

        # ========================================================
        # LOG TÉCNICO - EXECUÇÃO CANCELADA
        # ========================================================

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=execucao.robot_id,
            agent_id=execucao.agent_id,
            user_id=execucao.user_id
        )

        logger.info(
            "Execução da fila cancelada",
            extra={
                "event": "queued_execution_cancelled",
                **contexto_log,
                "status": "cancelled",
                "status_before": "queued",
                "status_after": "cancelled"
            }
        )

        return {
            "status": "success",
            "message": "Execução da fila cancelada com sucesso.",
            "execution_id": execution_id
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro ao cancelar execução da fila",
            extra={
                "event": "queued_execution_cancel_failed",
                "execution_id": execution_id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

        return {
            "status": "error",
            "message": "Não foi possível cancelar a execução.",
            "execution_id": execution_id,
            "error": str(error)
        }

    finally:

        db.close()
# ============================================================
# LISTAR EXECUÇÕES EM ANDAMENTO
# ============================================================
#
# Esta API retorna as execuções que estão atualmente:
#
#     - queued
#     - running
#
# Como estamos consultando informações de execução,
# o usuário precisa possuir:
#
#     Executions:view
#
# A validação acontece antes da função ser executada.
# ============================================================
@router.get(
    "/executions",
    summary="Listar execuções em andamento",
    description=(
        "Retorna as execuções que estão atualmente aguardando "
        "na fila ou em execução. "
        "A resposta contém informações sobre o robô, pasta, usuário, "
        "Agent, status e horários da execução."
    )
)
def list_executions(
    # A visão de execuções em andamento exige autorização
    # explícita de leitura do domínio Executions.
    usuario: User = Depends(
        require_permission("Executions", "view")
    ),
):
    """
    Lista as execuções atualmente em andamento.

    Retorna execuções com os status:
        - queued
        - running

    Também retorna:
        - usuário que solicitou a execução;
        - nome do usuário;
        - pasta completa do robô;
        - Agent;
        - PID;
        - horários;
        - mensagem de erro, quando existir.
    """

    db = SessionLocal()

    try:

        # ========================================================
        # BUSCA EXECUÇÕES COM ROBÔ, AGENT E USUÁRIO
        # ========================================================

        executions = (
            db.query(
                Execution,
                Robot,
                Agent,
                User
            )
            # Relaciona a execução ao robô cadastrado.
            .outerjoin(
                Robot,
                Execution.robot_id == Robot.id
            )
            # Relaciona a execução ao Agent responsável.
            .outerjoin(
                Agent,
                Execution.agent_id == Agent.agent_id
            )
            # Relaciona a execução ao usuário que iniciou o processo.
            .outerjoin(
                User,
                Execution.user_id == User.id
            )
            # Retorna somente execuções na fila ou em andamento.
            .filter(
                Execution.status.in_(["queued", "running"])
            )
            # Mais recentes primeiro.
            .order_by(
                Execution.id.desc()
            )
            .all()
        )

        resultado = []

        for execution, robot, agent, user in executions:

            # ====================================================
            # MONTA O CAMINHO COMPLETO DA PASTA
            # ====================================================

            folder_name = montar_caminho_pasta(
                db,
                robot.folder_id if robot else None
            )

            # ====================================================
            # MONTA RESULTADO DA EXECUÇÃO
            # ====================================================

            resultado.append({

                # ID da execução.
                "id": execution.id,

                # ID do robô relacionado.
                "robot_id": execution.robot_id,

                # Nome do robô.
                "robot_name": (
                    execution.robot_name
                    if execution.robot_name
                    else (
                        robot.name
                        if robot
                        else "Desconhecido"
                    )
                ),

                # Nome do arquivo do robô.
                "filename": (
                    execution.robot_filename
                    if execution.robot_filename
                    else (
                        robot.filename
                        if robot
                        else "Desconhecido"
                    )
                ),

                # ====================================================
                # DADOS DA PASTA
                # ====================================================

                # Caminho completo incluindo subpastas.
                "folder_name": folder_name,

                # ====================================================
                # DADOS DO USUÁRIO
                # ====================================================

                # ID do usuário que iniciou a execução.
                "user_id": execution.user_id,

                # Username/login do usuário.
                "username": (
                    user.username
                    if user
                    else None
                ),

                # Nome de exibição do usuário.
                "user_name": (
                    user.name
                    if user
                    else None
                ),

                # ====================================================
                # DADOS DO AGENT
                # ====================================================

                "agent_id": execution.agent_id,

                "agent_name": (
                    agent.name
                    if agent
                    else "Agent excluído"
                ),

                # PID real do processo no Agent.
                "pid": execution.pid,

                # ====================================================
                # STATUS E HORÁRIOS
                # ====================================================

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

                # Mensagem de erro, se houver.
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
# MONTAR CAMINHO COMPLETO DA PASTA DO ROBÔ
# ============================================================

def montar_caminho_pasta(db, folder_id):
    """
    Monta o caminho completo da pasta de um robô.

    Exemplo de estrutura no banco:

        Servicos a Clientes
        └── Faturamento
            └── Primeiro Faturamento

    Retorno:

        Servicos a Clientes / Faturamento / Primeiro Faturamento

    Parâmetros:
        db:
            Sessão atual do SQLAlchemy.

        folder_id:
            ID da pasta diretamente associada ao robô.

    Retorno:
        String com o caminho completo da pasta.
        Retorna "Pasta raiz" quando o robô não possui pasta.
    """

    # Se o robô não possui pasta associada,
    # retornamos uma identificação padrão.
    if folder_id is None:
        return "Pasta raiz"

    partes = []

    # Começamos pela pasta diretamente associada ao robô.
    pasta_atual_id = folder_id

    # Percorremos a hierarquia até chegar à pasta raiz.
    while pasta_atual_id is not None:

        pasta = (
            db.query(RobotFolder)
            .filter(
                RobotFolder.id == pasta_atual_id
            )
            .first()
        )

        # Se a pasta não existir mais no banco,
        # interrompemos para evitar loop infinito.
        if not pasta:
            break

        # Inserimos o nome no início da lista,
        # pois estamos subindo da subpasta para a raiz.
        partes.insert(0, pasta.name)

        # Avançamos para a pasta pai.
        pasta_atual_id = pasta.parent_id

    # Se nenhuma pasta foi encontrada,
    # retornamos um valor padrão.
    if not partes:
        return "Pasta não encontrada"

    # Junta todos os níveis da hierarquia.
    return " / ".join(partes)
# ============================================================
# HISTÓRICO DE EXECUÇÕES
# ============================================================
#
# Esta API retorna as execuções que já foram finalizadas,
# incluindo execuções concluídas, com erro ou canceladas.
#
# O Histórico possui uma visão funcional própria no
# Control Room.
#
# A permissão necessária é:
#
#     History:view
#
# A validação RBAC acontece antes da função ser executada.
# ============================================================
# ============================================================
# HISTÓRICO DE EXECUÇÕES
# ============================================================

@router.get(
    "/executions/history",
    summary="Listar histórico de execuções",
    description=(
        "Retorna o histórico das execuções já finalizadas. "
        "A resposta contém informações sobre o robô, Agent, "
        "usuário responsável, pasta completa, status, horários "
        "e eventual mensagem de erro."
    )
)
def list_execution_history(
    # O Histórico possui uma visão funcional própria no
    # Control Room e, por isso, utiliza sua permissão
    # específica de visualização.
    usuario: User = Depends(
        require_permission("History", "view")
    ),
):
    """
    Lista o histórico das execuções finalizadas.

    Também retorna:

        - Nome do usuário que executou;
        - Username do usuário;
        - Caminho completo da pasta do robô;
        - Agent responsável;
        - Status e horários.
    """

    db = SessionLocal()

    try:

        # ========================================================
        # BUSCA EXECUÇÕES FINALIZADAS
        # ========================================================

        executions = (
            db.query(
                Execution,
                Robot,
                Agent,
                User
            )
            .outerjoin(
                Robot,
                Execution.robot_id == Robot.id
            )
            .outerjoin(
                Agent,
                Execution.agent_id == Agent.agent_id
            )
            .outerjoin(
                User,
                Execution.user_id == User.id
            )
            .filter(
                Execution.status.notin_(["running", "queued"])
            )
            .order_by(
                Execution.id.desc()
            )
            .all()
        )

        resultado = []

        # ========================================================
        # MONTA RETORNO DO HISTÓRICO
        # ========================================================

        for execution, robot, agent, user in executions:

            # ----------------------------------------------------
            # Descobre o caminho completo da pasta.
            #
            # O folder_id vem do Robot atual.
            # A função sobe pelos parent_id até a raiz.
            # ----------------------------------------------------

            folder_name = montar_caminho_pasta(
                db=db,
                folder_id=robot.folder_id if robot else None
            )

            resultado.append({

                # ID da execução.
                "id": execution.id,

                # ID do robô.
                "robot_id": execution.robot_id,

                # Nome do robô.
                "robot_name": (
                    execution.robot_name
                    if execution.robot_name
                    else (
                        robot.name
                        if robot
                        else "Desconhecido"
                    )
                ),

                # Nome do arquivo executado.
                "filename": (
                    execution.robot_filename
                    if execution.robot_filename
                    else (
                        robot.filename
                        if robot
                        else "Desconhecido"
                    )
                ),

                # Informações do Agent.
                "agent_id": execution.agent_id,

                "agent_name": (
                    agent.name
                    if agent
                    else "Agent excluído"
                ),

                # ------------------------------------------------
                # Usuário que iniciou a execução.
                # ------------------------------------------------

                "user_id": execution.user_id,

                "username": (
                    user.username
                    if user
                    else "Usuário desconhecido"
                ),

                "user_name": (
                    user.name
                    if user
                    else "Usuário desconhecido"
                ),

                # ------------------------------------------------
                # Caminho completo da pasta.
                # Exemplo:
                #
                # Servicos a Clientes /
                # Faturamento /
                # Primeiro Faturamento
                # ------------------------------------------------

                "folder_name": folder_name,

                # Status da execução.
                "status": execution.status,

                # Data/hora de início.
                "started_at": (
                    execution.started_at.isoformat()
                    if execution.started_at
                    else None
                ),

                # Data/hora de finalização.
                "finished_at": (
                    execution.finished_at.isoformat()
                    if execution.finished_at
                    else None
                ),

                # Mensagem de erro, quando existir.
                "error_message": execution.error_message

            })

        return {
            "status": "success",
            "total": len(resultado),
            "executions": resultado
        }

    finally:
        db.close()