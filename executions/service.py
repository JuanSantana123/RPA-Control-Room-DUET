# ============================================================
# DUET CORE - EXECUTIONS - SERVIÇO DE EXECUÇÃO
# ============================================================
#
# Responsável pela lógica interna utilizada para executar
# Robots publicados e AutomationProjects em Desenvolvimento.
#
# Este módulo:
# - resolve Agent e origem da execução;
# - resolve Robot ou AutomationProject;
# - monta/reutiliza pacotes de Desenvolvimento;
# - reaproveita Executions existentes da fila;
# - valida arquivo executável;
# - valida comunicação e disponibilidade do Agent;
# - valida a sessão Windows;
# - realiza deploy do pacote;
# - cria ou atualiza o registro de Execution;
# - solicita a execução ao Agent;
# - preserva logs e transições de status existentes.
#
# Este módulo NÃO:
# - registra endpoints FastAPI;
# - autentica usuários HTTP;
# - controla o loop do Worker da fila;
# - contém schemas Pydantic;
# - inicia threads.
#
# IMPORTANTE:
# A função _executar_robot() abaixo deve ser copiada
# integralmente do api/executions.py atual.
#
# Nenhuma regra de execução, retorno, transação, timeout,
# status ou comunicação com o Agent deve ser alterada durante
# esta modularização.
# ============================================================

from pathlib import Path
from datetime import datetime

import logging
import requests
import uuid
# Utilizado para adquirir um advisory lock transacional no PostgreSQL.
#
# O lock serializa, por Agent, as decisões que podem criar ou promover
# uma Execution para "running". Assim dois processos/Workers diferentes
# não conseguem reservar simultaneamente o mesmo Agent.
from sqlalchemy import text
from database import SessionLocal

from models import (
    Agent,
    Robot,
    RobotVersion,
    Execution,
    AutomationProject,
)
from packaging.project_packager import (
    build_project_package,
    BUILD_REPOSITORY,
)

from schemas.executions import ExecutionRequest

from executions.logging_context import (
    obter_contexto_execucao_log,
)

# Recupera a credencial original do Agent somente em memória
# durante as chamadas Control Room -> Agent.
from agents.token_security import descriptografar_agent_token
# ============================================================
# GARANTIA DA SESSÃO WINDOWS DO AGENT
# ============================================================
#
# Centraliza:
#
# - validação da identidade Windows configurada;
# - consulta da sessão atual;
# - autenticação quando necessária;
# - revalidação da identidade após autenticação.
#
# O service de execução não manipula diretamente a senha.
# ============================================================

from executions.windows_session_service import (
    garantir_sessao_windows_agent,
)
# Logger compartilhado com o restante do Control Room.
logger = logging.getLogger("control_room")


# ============================================================
# RESERVA ATÔMICA DO AGENT PARA EXECUÇÃO DIRETA
# ============================================================
def _reservar_execucao_direta(
    *,
    agent_id: str,
    source_type: str,
    robot_id: int | None,
    robot_version: int | None,
    project_id: int | None,
    robot_name: str,
    robot_filename: str,
    user_id: int | None,
):
    """
    Tenta reservar atomicamente um Agent para uma execução
    iniciada diretamente pelo usuário.

    A própria linha Execution(status="running") representa a
    reserva lógica do Agent no Control Room.

    Retornos:
        reserved:
            reserva criada e execution_id retornado.

        busy:
            já existe outra Execution running para o Agent.

    CONCORRÊNCIA:
    O Control Room utiliza PostgreSQL.

    pg_advisory_xact_lock() cria um lock transacional associado
    ao Agent. Processos concorrentes que tentarem reservar o mesmo
    Agent serão serializados até o término da transação.

    O lock é liberado automaticamente pelo PostgreSQL no COMMIT
    ou ROLLBACK, inclusive em caso de exceção.
    """

    db = SessionLocal()

    try:

        # --------------------------------------------------------
        # LOCK TRANSACIONAL POR AGENT
        # --------------------------------------------------------
        #
        # hashtext(agent_id) produz uma chave determinística a partir
        # do identificador textual do Agent.
        #
        # pg_advisory_xact_lock() mantém o lock somente durante esta
        # transação. Não precisamos liberar manualmente.
        #
        # IMPORTANTE:
        # A Queue utiliza exatamente o mesmo namespace/chave.
        # Assim execução direta e Worker da fila disputam o mesmo lock.
        # --------------------------------------------------------

        db.execute(
            text(
                """
                SELECT pg_advisory_xact_lock(
                    hashtext(:agent_id)
                )
                """
            ),
            {
                "agent_id": agent_id,
            },
        )

        # --------------------------------------------------------
        # CONFIRMA QUE NÃO EXISTE RESERVA ATIVA
        # --------------------------------------------------------
        #
        # Esta consulta acontece DEPOIS de obter o advisory lock.
        # Portanto outro processo tentando reservar o mesmo Agent
        # precisa aguardar esta transação terminar.
        # --------------------------------------------------------

        execucao_running = (
            db.query(Execution.id)
            .filter(
                Execution.agent_id == agent_id,
                Execution.status == "running",
            )
            .first()
        )

        if execucao_running:

            db.rollback()

            return {
                "status": "busy",
            }

        # --------------------------------------------------------
        # CRIA A EXECUTION QUE REPRESENTA A RESERVA DO AGENT
        # --------------------------------------------------------
        #
        # Para Robot publicado, robot_version registra a versão
        # exata selecionada para esta execução.
        #
        # Para Development, robot_version permanece None.
        # --------------------------------------------------------

        execucao = Execution(
            source_type=source_type,
            robot_id=robot_id,
            robot_version=robot_version,
            project_id=project_id,
            robot_name=robot_name,
            robot_filename=robot_filename,
            agent_id=agent_id,
            user_id=user_id,
            status="running",
            started_at=datetime.now(),
        )

        db.add(execucao)

        # Obtém o ID ainda dentro da mesma transação e, portanto,
        # enquanto o advisory lock continua pertencendo à sessão.
        db.flush()

        execution_id = execucao.id

        # O COMMIT persiste a reserva e libera automaticamente
        # o pg_advisory_xact_lock().
        db.commit()

        return {
            "status": "reserved",
            "execution_id": execution_id,
        }

    except Exception:

        # O ROLLBACK também libera automaticamente o advisory lock.
        db.rollback()
        raise

    finally:

        db.close()
# ============================================================
# FINALIZA RESERVA QUE NÃO CHEGOU À EXECUÇÃO
# ============================================================

def _finalizar_reserva_execucao(
    *,
    execution_id: int,
    message: str,
):
    """
    Finaliza como error uma Execution reservada no banco quando
    sabemos que o Robot NÃO chegou a iniciar no Agent.

    O UPDATE exige status="running" para não sobrescrever um
    callback terminal que possa ter chegado concorrentemente.
    """

    db = SessionLocal()

    try:

        linhas = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id,
                Execution.status == "running",
            )
            .update(
                {
                    Execution.status: "error",
                    Execution.finished_at: datetime.now(),
                    Execution.error_message: message,
                },
                synchronize_session=False,
            )
        )

        if linhas == 1:
            db.commit()
        else:
            db.rollback()

        return linhas == 1

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()

def _claim_execucao_queued(
    execution_id: int,
    agent_id: str,
):
    """
    Tenta retirar atomicamente uma Execution da fila.

    A proteção acontece em duas dimensões:

    1. a própria Execution precisa continuar queued;
    2. o Agent não pode possuir outra Execution running.

    CONCORRÊNCIA:
    O PostgreSQL utiliza pg_advisory_xact_lock() para serializar
    todas as tentativas de reserva do mesmo Agent.

    A execução direta e a Queue utilizam a mesma chave baseada
    em agent_id. Portanto os dois fluxos não conseguem reservar
    simultaneamente o mesmo Agent.

    Retornos:
        claimed:
            Execution passou de queued para running.

        claim_lost:
            Execution já foi consumida por outro Worker.

        agent_busy:
            outra Execution já ocupa o Agent.
    """

    db = SessionLocal()

    try:

        # --------------------------------------------------------
        # LOCK TRANSACIONAL POR AGENT
        # --------------------------------------------------------
        #
        # Precisa ser exatamente o mesmo mecanismo utilizado por
        # _reservar_execucao_direta().
        #
        # Isso serializa:
        #
        #   execução direta  <-> execução direta
        #   execução direta  <-> Queue
        #   Queue            <-> Queue
        #
        # para o mesmo Agent.
        # --------------------------------------------------------

        db.execute(
            text(
                """
                SELECT pg_advisory_xact_lock(
                    hashtext(:agent_id)
                )
                """
            ),
            {
                "agent_id": agent_id,
            },
        )

        # --------------------------------------------------------
        # CONFIRMA QUE A EXECUTION AINDA ESTÁ NA FILA
        # --------------------------------------------------------

        execucao = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id,
                Execution.agent_id == agent_id,
                Execution.status == "queued",
            )
            .first()
        )

        if not execucao:

            db.rollback()

            return {
                "status": "claim_lost",
            }

        # --------------------------------------------------------
        # CONFIRMA QUE O AGENT CONTINUA LIVRE
        # --------------------------------------------------------

        outra_execucao_running = (
            db.query(Execution.id)
            .filter(
                Execution.agent_id == agent_id,
                Execution.status == "running",
                Execution.id != execution_id,
            )
            .first()
        )

        if outra_execucao_running:

            db.rollback()

            return {
                "status": "agent_busy",
            }

        # --------------------------------------------------------
        # PROMOVE QUEUED -> RUNNING
        # --------------------------------------------------------

        started_at = datetime.now()

        linhas_atualizadas = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id,
                Execution.agent_id == agent_id,
                Execution.status == "queued",
            )
            .update(
                {
                    Execution.status: "running",
                    Execution.started_at: started_at,
                },
                synchronize_session=False,
            )
        )

        if linhas_atualizadas != 1:

            db.rollback()

            return {
                "status": "claim_lost",
            }

        # Persiste a transição e libera automaticamente
        # o advisory lock transacional.
        db.commit()

        return {
            "status": "claimed",
            "started_at": started_at,
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()

# ============================================================
# RESOLVE ROBOTVERSION IMUTÁVEL PARA EXECUÇÃO
# ============================================================
def _resolver_robot_version_execucao(
    db,
    robot: Robot,
    version: int | None = None,
):
    """
    Resolve e valida o artefato imutável de uma RobotVersion.

    Parâmetros:
        db:
            sessão SQLAlchemy utilizada para consultar a versão.

        robot:
            Robot lógico ao qual a versão pertence.

        version:
            versão específica que deve ser executada.

            - None:
                utiliza a versão atualmente publicada em Robot.version.

            - número informado:
                utiliza exatamente essa RobotVersion.

    Esse parâmetro é importante para a Queue:
    uma Execution que entrou na fila com a versão 7 deve continuar
    executando a versão 7 mesmo que o Robot já esteja na versão 8.
    """

    # --------------------------------------------------------
    # DEFINE QUAL VERSÃO DEVE SER RESOLVIDA
    # --------------------------------------------------------

    versao_resolvida = (
        version
        if version is not None
        else robot.version
    )

    if versao_resolvida is None:

        raise RuntimeError(
            "Robot não possui versão publicada definida."
        )

    # --------------------------------------------------------
    # LOCALIZA A ROBOTVERSION EXATA
    # --------------------------------------------------------

    robot_version = (
        db.query(RobotVersion)
        .filter(
            RobotVersion.robot_id == robot.id,
            RobotVersion.version == versao_resolvida,
        )
        .first()
    )

    if not robot_version:

        raise RuntimeError(
            "RobotVersion correspondente à versão solicitada "
            "não foi encontrada."
        )

    # --------------------------------------------------------
    # RESOLVE O ARTEFATO FÍSICO
    # --------------------------------------------------------

    artifact_path = Path(
        robot_version.artifact_path
    )

    # RobotVersion normalmente persiste caminho relativo à raiz
    # do Control Room.
    #
    # Caminhos absolutos continuam suportados para registros
    # existentes.
    if not artifact_path.is_absolute():

        artifact_path = (
            Path(__file__).resolve().parent.parent
            / artifact_path
        )

    artifact_path = artifact_path.resolve()

    if not artifact_path.is_file():

        raise RuntimeError(
            "Artefato da RobotVersion não foi encontrado."
        )

    # --------------------------------------------------------
    # VALIDA INTEGRIDADE DO ARTEFATO
    # --------------------------------------------------------

    import hashlib

    sha256 = hashlib.sha256()

    with artifact_path.open("rb") as arquivo:

        while True:

            chunk = arquivo.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    actual_hash = sha256.hexdigest()

    if actual_hash != robot_version.file_hash:

        raise RuntimeError(
            "Artefato da RobotVersion falhou na validação "
            "de integridade."
        )

    return (
        robot_version,
        artifact_path,
    )
def _executar_robot(
    agent_id: str,
    request: ExecutionRequest
):
    # ========================================================
    # FUNÇÃO INTERNA DE EXECUÇÃO
    # ========================================================
    #
    # Esta função contém a lógica real de execução do Robot.
    #
    # Ela NÃO possui Depends().
    #
    # Isso é importante porque ela pode ser chamada tanto:
    #
    # 1. pelo endpoint HTTP, após autenticar o usuário;
    # 2. pelo Worker da fila, que já possui uma Execution
    #    criada no banco.
    #
    # Dessa forma evitamos passar um objeto Depends para
    # dentro da lógica do Worker.
    # ========================================================
        # ========================================================
    # 1. ABRE BANCO
    # ========================================================

    db = SessionLocal()

    try:

        # ========================================================
        # 2. BUSCA O AGENT
        # ========================================================

        agent = (
            db.query(Agent)
            .filter(
                Agent.agent_id == agent_id
            )
            .first()
        )

        if not agent:

            return {
                "status": "error",
                "message": "Agent não encontrado",
                "agent_id": agent_id
            }


        # ========================================================
        # CREDENCIAL WINDOWS DE EXECUÇÃO DO AGENT
        # ========================================================
        #
        # Guardamos somente o ID antes de fechar a sessão SQLAlchemy.
        #
        # A senha NÃO é carregada aqui.
        #
        # Posteriormente windows_session_service decidirá se precisa
        # ou não resolver o segredo.
        # ========================================================

        execution_credential_id = (
            agent.execution_credential_id
        )

        # ========================================================
        # 3. RESOLVE A ORIGEM DA EXECUÇÃO
        # ========================================================

        source_type = (
            request.source_type or "robot"
        ).strip().lower()

        if source_type not in {
            "robot",
            "development"
        }:

            return {
                "status": "error",
                "message": "Origem de execução inválida",
                "source_type": source_type
            }

        robot_id = None
        project_id = None
        robot_version = None

        # --------------------------------------------------------
        # ROBOT PUBLICADO
        # --------------------------------------------------------
        if source_type == "robot":

            robot_id = request.robot_id

            if robot_id is None:

                return {
                    "status": "error",
                    "message": "robot_id é obrigatório para execução de Robot",
                    "agent_id": agent_id
                }

            robot = (
                db.query(Robot)
                .filter(
                    Robot.id == robot_id
                )
                .first()
            )

            if not robot:

                return {
                    "status": "error",
                    "message": "Robot não encontrado",
                    "robot_id": robot_id,
                    "agent_id": agent_id
                }

            # ------------------------------------------------
            # ====================================================
            # DEFINE A ROBOTVERSION EXATA DA EXECUÇÃO
            # ====================================================
            #
            # Execução direta:
            #     utiliza Robot.version, ou seja, a versão
            #     publicada atualmente.
            #
            # Execução que já está na Queue:
            #     utiliza Execution.robot_version, congelada no
            #     momento em que a Execution foi criada.
            #
            # Dessa forma uma publicação posterior não altera o
            # código de uma Execution que já estava aguardando.
            # ====================================================

            versao_para_execucao = robot.version

            if request.execution_id is not None:

                execucao_origem = (
                    db.query(Execution)
                    .filter(
                        Execution.id == request.execution_id,
                        Execution.agent_id == agent_id,
                        Execution.source_type == "robot",
                        Execution.robot_id == robot_id,
                    )
                    .first()
                )

                if not execucao_origem:

                    return {
                        "status": "error",
                        "message": (
                            "Execução de Robot da fila "
                            "não encontrada."
                        ),
                        "execution_id": request.execution_id,
                        "robot_id": robot_id,
                        "agent_id": agent_id,
                    }

                # Executions antigas, criadas antes do controle
                # explícito de versão, podem possuir NULL.
                #
                # Não utilizamos silenciosamente a versão atual,
                # pois isso quebraria a garantia de proveniência.
                if execucao_origem.robot_version is None:

                    return {
                        "status": "error",
                        "message": (
                            "Execução da fila não possui "
                            "RobotVersion congelada."
                        ),
                        "execution_id": request.execution_id,
                        "robot_id": robot_id,
                        "agent_id": agent_id,
                    }

                versao_para_execucao = (
                    execucao_origem.robot_version
                )

            # ----------------------------------------------------
            # RESOLVE E VALIDA O ARTEFATO IMUTÁVEL
            # ----------------------------------------------------

            (
                robot_version_obj,
                robot_version_path,
            ) = _resolver_robot_version_execucao(
                db=db,
                robot=robot,
                version=versao_para_execucao,
            )

            robot_name = robot.name

            robot_filename = (
                robot_version_obj.filename
            )

            robot_file_path = str(
                robot_version_path
            )

            robot_version = (
                robot_version_obj.version
            )

        # --------------------------------------------------------
        # AUTOMATIONPROJECT
        # --------------------------------------------------------
        else:

            project_id = request.project_id

            if project_id is None:

                return {
                    "status": "error",
                    "message": "project_id é obrigatório para execução de Desenvolvimento",
                    "agent_id": agent_id
                }

            project = (
                db.query(AutomationProject)
                .filter(
                    AutomationProject.id == project_id,
                    AutomationProject.is_active == 1
                )
                .first()
            )

            if not project:

                return {
                    "status": "error",
                    "message": "AutomationProject ativo não encontrado",
                    "project_id": project_id,
                    "agent_id": agent_id
                }

            robot_name = project.name
            robot_version = None

            # ----------------------------------------------------
            # EXECUÇÃO DE DESENVOLVIMENTO JÁ NA FILA
            # ----------------------------------------------------
            # O pacote foi congelado quando a execução entrou na
            # fila. O Worker deve reutilizar exatamente o mesmo ZIP.
            # ----------------------------------------------------
            if request.execution_id is not None:

                execucao_origem = (
                    db.query(Execution)
                    .filter(
                        Execution.id == request.execution_id,
                        Execution.agent_id == agent_id,
                        Execution.source_type == "development",
                        Execution.project_id == project_id
                    )
                    .first()
                )

                if not execucao_origem:

                    return {
                        "status": "error",
                        "message": "Execução de Desenvolvimento da fila não encontrada",
                        "execution_id": request.execution_id,
                        "project_id": project_id,
                        "agent_id": agent_id
                    }

                robot_filename = execucao_origem.robot_filename
                robot_file_path = str(
                    (
                        BUILD_REPOSITORY /
                        "executions" /
                        robot_filename
                    ).resolve()
                )

            # ----------------------------------------------------
            # NOVA EXECUÇÃO DE DESENVOLVIMENTO
            # ----------------------------------------------------
            else:

                robot_filename = (
                    f"development_project_{project_id}_"
                    f"{uuid.uuid4().hex}.zip"
                )

                robot_path_build = (
                    BUILD_REPOSITORY /
                    "executions" /
                    robot_filename
                )

                try:

                    build_result = build_project_package(
                        db=db,
                        project_id=project_id,
                        output_path=robot_path_build
                    )

                except Exception as error:

                    logger.exception(
                        "Falha ao montar pacote de Desenvolvimento",
                        extra={
                            "event": "development_package_build_failed",
                            "project_id": project_id,
                            "agent_id": agent_id,
                            "user_id": request.user_id,
                            "status": "error",
                            "error_type": type(error).__name__,
                            "error_message": str(error)
                        }
                    )

                    return {
                        "status": "error",
                        "message": "Não foi possível montar o pacote do projeto",
                        "project_id": project_id,
                        "agent_id": agent_id
                    }

                robot_file_path = str(
                    build_result.package_path
                )

        # ========================================================
        # VERIFICA SE É EXECUÇÃO DA FILA
        # ========================================================

        if request.execution_id is not None:

            query_execucao = db.query(Execution).filter(
                Execution.id == request.execution_id,
                Execution.agent_id == agent_id,
                Execution.source_type == source_type
            )

            if source_type == "development":
                query_execucao = query_execucao.filter(
                    Execution.project_id == project_id
                )
            else:
                query_execucao = query_execucao.filter(
                    Execution.robot_id == robot_id
                )

            execucao = query_execucao.first()

            # ----------------------------------------------------
            # EXECUÇÃO DA FILA NÃO ENCONTRADA
            # ----------------------------------------------------

            if not execucao:

                return {
                    "status": "error",
                    "message": "Execução da fila não encontrada",
                    "execution_id": request.execution_id,
                    "agent_id": agent_id,
                    "robot_id": robot_id,
                    "project_id": project_id,
                    "source_type": source_type
                }

            if request.user_id is None:
                request.user_id = execucao.user_id

            # ----------------------------------------------------
            # CONFIRMA QUE ESTÁ NA FILA
            # ----------------------------------------------------
            # ----------------------------------------------------
            # CLAIM ATÔMICO DA EXECUÇÃO DA FILA
            # ----------------------------------------------------
            #
            # Não fazemos:
            #
            #     SELECT queued
            #     depois UPDATE running
            #
            # como duas decisões independentes.
            #
            # O próprio UPDATE exige status="queued".
            # Assim, se outro Worker já reivindicou a Execution,
            # rowcount será 0 e este Worker não poderá dispará-la.
            # ----------------------------------------------------

            execution_id = execucao.id

            # ------------------------------------------------
            # CLAIM DA EXECUTION + RESERVA DO AGENT
            # ------------------------------------------------
            #
            # A decisão é feita por uma transação própria,
            # serializada no PostgreSQL por advisory lock.
            #
            # Isso impede que duas Executions diferentes
            # reservem simultaneamente o mesmo Agent.
            # ------------------------------------------------

            # Esta sessão já realizou SELECTs anteriormente.
            # Encerramos sua transação atual antes de executar
            # o claim dedicado em sua própria sessão/transação.
            db.rollback()

            resultado_claim = (
                _claim_execucao_queued(
                    execution_id=execution_id,
                    agent_id=agent_id,
                )
            )

            if (
                resultado_claim["status"]
                == "claim_lost"
            ):

                return {
                    "status": "error",
                    "message": (
                        "Execução já foi retirada da fila "
                        "por outro Worker."
                    ),
                    "execution_id": execution_id,
                    "agent_id": agent_id,
                    "robot_id": robot_id,
                    "claim_lost": True,
                }

            if (
                resultado_claim["status"]
                == "agent_busy"
            ):

                return {
                    "status": "queued",
                    "message": (
                        "Agent já possui outra execução "
                        "em andamento."
                    ),
                    "execution_id": execution_id,
                    "agent_id": agent_id,
                    "robot_id": robot_id,
                    "agent_busy": True,
                }

            started_at = (
                resultado_claim["started_at"]
            )

            # ========================================================
            # MANTÉM OS DADOS DO AGENT CARREGADOS APÓS O COMMIT
            # ========================================================
            #
            # O SQLAlchemy pode expirar os atributos dos objetos ORM
            # após um commit.
            #
            # Como esta sessão será fechada logo abaixo e o fluxo ainda
            # utiliza os dados do Agent posteriormente, acessamos os
            # atributos necessários enquanto ele ainda está associado
            # à sessão.
            #
            # Isso evita DetachedInstanceError após o db.close().
            # ========================================================

            agent.name
            agent.host
            agent.port
            agent.agent_token_encrypted

            # A alteração de status já foi persistida no banco.
            # Portanto, este evento representa efetivamente
            # a transição da execução de queued para running.
            contexto_log = obter_contexto_execucao_log(
                execution_id=execution_id,
                robot_id=robot_id,
                agent_id=agent_id
            )

            logger.info(
                "Execução retirada da fila e iniciada",
                extra={
                    "event": "queued_execution_started",
                    **contexto_log,
                    "status": "running",
                    "status_before": "queued",
                    "status_after": "running"
                }
            )

        # EXECUÇÃO NORMAL
        # ========================================================
        #
        # IMPORTANTE:
        #
        # Neste momento NÃO criamos a Execution.
        #
        # Primeiro precisamos validar:
        #
        # - Agent
        # - sessão Windows
        # - status de execução
        # - deploy do Robot
        #
        # A Execution será criada somente depois
        # que o deploy for concluído com sucesso.
        #
        # ========================================================

        else:

            execution_id = None

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

        # O caminho físico pertence à infraestrutura interna do
        # Control Room e não deve ser devolvido ao frontend.
        #
        # O nome lógico do arquivo é suficiente para identificar
        # qual artefato apresentou problema.
        logger.error(
            "Arquivo do Robot não encontrado no Control Room",
            extra={
                "event": "execution_robot_file_not_found",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "agent_id": agent_id,
                "user_id": request.user_id,
                "file_path": str(robot_path),
                "status": "error",
            }
        )

        return {
            "status": "error",
            "message": "Arquivo do Robot não encontrado no Control Room",
            "robot_id": robot_id,
            "robot_name": robot_name,
            "filename": robot_filename
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
        # ========================================================
    # TOKEN DO AGENT PARA COMUNICAÇÃO
    # ========================================================
    #
    # O banco armazena o token criptografado.
    #
    # Neste ponto recuperamos o token original somente em
    # memória porque ele será enviado no Authorization Bearer
    # das chamadas HTTP feitas pelo Control Room ao Agent.
    #
    # Nenhum token plaintext é persistido novamente no banco.
    # ========================================================

    agent_token = descriptografar_agent_token(
        agent.agent_token_encrypted
    )

    try:

        health_response = requests.get(
            health_url,
            headers={
                "Authorization": f"Bearer {agent_token}"
            },
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

        logger.error(
            "Agent indisponível durante validação de health",
            extra={
                "event": "execution_agent_health_failed",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "robot_version": robot_version,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "offline",
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

        return {
            "status": "error",
            "message": "Agent está offline ou indisponível",
            "agent_id": agent_id,
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

        logger.error(
            "Agent respondeu com erro na validação de health",
            extra={
                "event": "execution_agent_health_http_error",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "robot_version": robot_version,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "offline",
                "http_status": health_response.status_code
            }
        )

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

        logger.error(
            "Agent retornou JSON inválido na validação de health",
            extra={
                "event": "execution_agent_health_invalid_json",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "robot_version": robot_version,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "error"
            }
        )

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

        logger.error(
            "Agent não está online para execução",
            extra={
                "event": "execution_agent_not_online",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "robot_version": robot_version,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "offline"
            }
        )
        return {
            "status": "error",
            "message": "Agent não está online",
            "agent_id": agent_id,
            "health": health
        }


    # ========================================================
    # 5.4 AGENT ESTÁ ACESSÍVEL
    # ========================================================

    logger.info(
    "Agent acessível para execução",
    extra={
        "event": "execution_agent_available",
        "agent_id": agent_id,
        "agent_name": agent.name
    }
    )


    # ========================================================
    # ========================================================
    # 5.5 GARANTE A SESSÃO WINDOWS DE EXECUÇÃO
    # ========================================================
    #
    # O fluxo de sessão agora fica centralizado em:
    #
    #     executions/windows_session_service.py
    #
    # Esse serviço:
    #
    # 1. identifica a conta Windows configurada no Vault;
    # 2. consulta a sessão atual do Agent;
    # 3. se a sessão já estiver correta, NÃO abre a senha;
    # 4. caso necessário, resolve a senha somente em memória;
    # 5. chama /session/authenticate;
    # 6. revalida a identidade Windows observada.
    #
    # O antigo bypass de sessão "disconnected" deixa de existir.
    # A execução somente continua se a identidade correta estiver
    # efetivamente pronta.
    # ========================================================

    try:

        windows_session_result = (
            garantir_sessao_windows_agent(
                agent_host=agent.host,
                agent_port=agent.port,
                agent_token=agent_token,
                execution_credential_id=(
                    execution_credential_id
                ),
                execution_id=execution_id,
            )
        )

    except Exception as error:

        # ====================================================
        # FALHA INESPERADA NA CAMADA DE SESSÃO
        # ====================================================
        #
        # Não registramos conteúdo de credencial ou password.
        # ====================================================

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=request.user_id,
        )

        logger.exception(
            "Falha inesperada ao preparar sessão Windows do Agent",
            extra={
                "event": (
                    "windows_session_preparation_failed"
                ),
                **contexto_log,
                "status": "error",
                "error_type": type(error).__name__,
            },
        )

        return {
            "status": "error",
            "message": (
                "Não foi possível preparar a sessão "
                "Windows do Agent."
            ),
            "agent_id": agent_id,
        }


    # ========================================================
    # VALIDA RESULTADO DA PREPARAÇÃO
    # ========================================================

    if not windows_session_result.get(
        "success"
    ):

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=request.user_id,
        )

        logger.error(
            (
                "Sessão Windows não disponível para execução | "
                f"Status: "
                f"{windows_session_result.get('status')}"
            ),
            extra={
                "event": "windows_session_not_ready",
                **contexto_log,
                "status": "blocked",
                "session_status": (
                    windows_session_result.get(
                        "status"
                    )
                ),
            },
        )

        return {
            "status": "error",
            "message": (
                windows_session_result.get(
                    "message"
                )
                or
                "Sessão Windows do Agent não está "
                "pronta para execução."
            ),
            "agent_id": agent_id,
            "session_status": (
                windows_session_result.get(
                    "status"
                )
            ),
        }


    # ========================================================
    # SESSÃO WINDOWS VALIDADA
    # ========================================================

    username = windows_session_result.get(
        "username"
    )

    domain = windows_session_result.get(
        "domain"
    )

    session_action = windows_session_result.get(
        "action"
    )

    contexto_log = obter_contexto_execucao_log(
        execution_id=execution_id,
        robot_id=robot_id,
        agent_id=agent_id,
        user_id=request.user_id,
    )

    logger.info(
        (
            "Sessão Windows validada | "
            f"Windows User: "
            f"{domain or '-'}\\{username or '-'} | "
            f"Action: {session_action or '-'}"
        ),
        extra={
            "event": "windows_session_validated",
            **contexto_log,
            "session_action": session_action,
        },
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
            headers={
                # Utiliza o token que já foi descriptografado em memória
                # antes da primeira comunicação HTTP com o Agent.
                "Authorization": f"Bearer {agent_token}"
            },
            timeout=5
        )

    except requests.RequestException as error:

        return {
            "status": "error",
            "message": "Não foi possível consultar o status de execução do Agent",
            "agent_id": agent_id
        }
    # ========================================================
    # 6. VALIDA STATUS HTTP
    # ========================================================

    if response.status_code != 200:
        logger.error(
            "Agent respondeu com erro ao consultar status de execução",
            extra={
                "event": "execution_status_http_error",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "error",
                "http_status": response.status_code
            }
        )
        return {
            "status": "error",
            "message": "Agent respondeu com erro ao consultar status",
            "agent_id": agent_id,
            "http_status": response.status_code
        }


    # ========================================================
    # 7. LÊ STATUS
    # ========================================================

    try:

        status_response = response.json()

    except ValueError:

        logger.error(
            "Agent retornou JSON inválido ao consultar status de execução",
            extra={
                "event": "execution_status_invalid_json",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "error"
            }
        )

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido",
            "agent_id": agent_id
        }


    execution_status = status_response.get(
        "execution_status"
    )
    logger.debug(
        "Status de execução recebido do Agent",
        extra={
            "event": "agent_execution_status_received",
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": execution_status
        }
    )


    # ========================================================
    # 8. VERIFICA SE AGENT ESTÁ LIVRE
    # ========================================================

        # ========================================================
    # 8. VERIFICA SE AGENT ESTÁ LIVRE
    # ========================================================
    #
    # Se o Agent estiver ocupado, NÃO retornamos erro.
    #
    # A solicitação será registrada como "queued"
    # e posteriormente será processada pela fila.
    #
    # ========================================================

    if execution_status != "idle":

              # ====================================================
        # CRIA NOVA EXECUÇÃO NA FILA
        # ====================================================
        #
        # Cada solicitação recebida representa uma execução
        # independente.
        #
        # Portanto, mesmo que já existam outras execuções
        # "queued" para o mesmo Agent e Robot, esta execução
        # também deve entrar na fila.
        #
        # Exemplo:
        #
        # 206 -> running
        # 207 -> queued
        # 208 -> queued
        # 209 -> queued
        #
        # O Worker será responsável por executar uma por vez.
        # ====================================================

        db = SessionLocal()

        try:

            # ----------------------------------------------------
            # CRIA A EXECUTION QUE REPRESENTA A RESERVA DO AGENT
            # ----------------------------------------------------
            #
            # Para Robots publicados, robot_version registra
            # exatamente a versão que será executada.
            #
            # Para Development, robot_version permanece None.
            # ----------------------------------------------------

            execucao = Execution(
                source_type=source_type,
                robot_id=robot_id,
                robot_version=robot_version,
                project_id=project_id,
                robot_name=robot_name,
                robot_filename=robot_filename,
                agent_id=agent_id,

                # Mantém o usuário responsável mesmo enquanto
                # a execução estiver aguardando na fila.
                user_id=request.user_id,

                status="queued",
                started_at=None
            )

            db.add(execucao)

            db.commit()

            db.refresh(execucao)

            execution_id = execucao.id

            contexto_log = obter_contexto_execucao_log(
                execution_id=execution_id,
                robot_id=robot_id,
                agent_id=agent_id,
                user_id=request.user_id
            )

            logger.info(
                "Execução adicionada à fila",
                extra={
                    "event": "execution_queued",
                    **contexto_log,
                    "status": "queued"
                }
            )
        except Exception as error:
            logger.exception(
                "Falha ao criar execução na fila",
                extra={
                    "event": "execution_queue_creation_failed",
                    "robot_id": robot_id,
                    "robot_name": robot_name,
                    "robot_filename": robot_filename,
                    "robot_version": robot_version,
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "user_id": request.user_id,
                    "status": "error",
                    "error_type": type(error).__name__,
                    "error_message": str(error)
                }
            )
            raise

        finally:
            db.close()

        return {
            "status": "queued",
            "message": "Agent está ocupado. Execução adicionada à fila.",
            "execution_id": execution_id,
            "agent_id": agent_id,
            "source_type": source_type,
            "robot_id": robot_id,
            "project_id": project_id,
            "robot_name": robot_name,
            "execution_status": execution_status
        }


    # ========================================================
    # RESERVA ATÔMICA DA EXECUÇÃO DIRETA
    # ========================================================
    #
    # A Queue já possui sua própria Execution e seu próprio
    # claim atômico.
    #
    # Para execução direta ainda não existe Execution neste
    # ponto. Portanto reservamos o Agent antes do deploy.
    # ========================================================

    if execution_id is None:

        reserva = _reservar_execucao_direta(
            agent_id=agent_id,
            source_type=source_type,
            robot_id=robot_id,
            robot_version=robot_version,
            project_id=project_id,
            robot_name=robot_name,
            robot_filename=robot_filename,
            user_id=request.user_id,
        )

        if reserva["status"] == "busy":

            # Outro fluxo conseguiu reservar o Agent depois
            # da nossa consulta HTTP de /execution/status.
            #
            # Não enviamos o Robot. Esta solicitação entra na
            # fila normalmente.
            db = SessionLocal()

            try:

                execucao = Execution(
                    source_type=source_type,
                    robot_id=robot_id,
                    project_id=project_id,
                     robot_version=robot_version,
                    robot_name=robot_name,
                    robot_filename=robot_filename,
                    agent_id=agent_id,
                    user_id=request.user_id,
                    status="queued",
                    started_at=None,
                )

                db.add(execucao)
                db.commit()
                db.refresh(execucao)

                execution_id_fila = execucao.id

            except Exception:

                db.rollback()
                raise

            finally:

                db.close()

            return {
                "status": "queued",
                "message": (
                    "Agent foi reservado por outra execução. "
                    "Execução adicionada à fila."
                ),
                "execution_id": execution_id_fila,
                "agent_id": agent_id,
                "source_type": source_type,
                "robot_id": robot_id,
                "project_id": project_id,
                "robot_name": robot_name,
                "execution_status": "running",
            }

        execution_id = reserva["execution_id"]

        logger.info(
            "Agent reservado para execução direta",
            extra={
                "event": "direct_execution_reserved",
                "execution_id": execution_id,
                "agent_id": agent_id,
                "robot_id": robot_id,
                "project_id": project_id,
                "user_id": request.user_id,
                "status": "running",
            }
        )
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

                headers={
                    # Utiliza o token que já foi descriptografado em memória
                    # antes da primeira comunicação HTTP com o Agent.
                    "Authorization": f"Bearer {agent_token}"
                },

                timeout=60
            )

    except requests.RequestException as error:
        # O Agent foi reservado antes do deploy.
        #
        # Como o upload não foi concluído, sabemos que esta
        # execução não chegou ao /execution/run.
        _finalizar_reserva_execucao(
            execution_id=execution_id,
            message=(
                "Não foi possível fazer upload do Robot "
                "para o Agent."
            ),
        )
        logger.error(
            "Falha de comunicação durante deploy do robô",
            extra={
                "event": "robot_deploy_request_failed",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "robot_version": robot_version,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

        return {
            "status": "error",
            "message": "Não foi possível fazer upload do Robot para o Agent",
            "agent_id": agent_id,
            "robot_id": robot_id
        }


    # ========================================================
    # 10. VALIDA DEPLOY

    if deploy_response_http.status_code != 200:

        # O Agent recusou o pacote antes de /execution/run.
        #
        # Portanto a reserva "running" criada no Control Room
        # precisa ser encerrada como erro.
        _finalizar_reserva_execucao(
            execution_id=execution_id,
            message=(
                "Agent recusou o deploy do Robot. "
                f"HTTP {deploy_response_http.status_code}."
            ),
        )

        logger.error(
            "Agent recusou o deploy do robô",
            extra={
                "event": "robot_deploy_rejected",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "robot_version": robot_version,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "error",
                "http_status": deploy_response_http.status_code
            }
        )

        return {
            "status": "error",
            "message": "Agent recusou o deploy do Robot",
            "agent_id": agent_id,
            "robot_id": robot_id,
            "http_status": deploy_response_http.status_code
        }


    try:

        deploy_response = deploy_response_http.json()

    except ValueError:
        _finalizar_reserva_execucao(
            execution_id=execution_id,
            message=(
                "Agent retornou resposta inválida "
                "durante o deploy do Robot."
            ),
        )
        logger.error(
            "Agent retornou JSON inválido durante deploy do robô",
            extra={
                "event": "robot_deploy_invalid_json",
                "robot_id": robot_id,
                "robot_name": robot_name,
                "robot_filename": robot_filename,
                "robot_version": robot_version,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "user_id": request.user_id,
                "status": "error"
            }
        )
        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no deploy",
            "agent_id": agent_id,
            "robot_id": robot_id
        }
    # ========================================================
    
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
    contexto_log = obter_contexto_execucao_log(
        execution_id=execution_id,
        robot_id=robot_id,
        agent_id=agent_id,
        user_id=request.user_id
    )

    logger.info(
        "Envio do comando de execução ao Agent iniciado",
        extra={
            "event": "execution_command_sending",
            **contexto_log,
            "status": "running"
        }
    )

    try:

        response = requests.post(
        execution_url,
        json={
            "robot_name": robot_filename,
            "execution_id": execution_id
        },
        headers={
            # Utiliza o token que já foi descriptografado em memória
            # antes da primeira comunicação HTTP com o Agent.
            "Authorization": f"Bearer {agent_token}"
        },
        timeout=25
            )
    except requests.Timeout as error:

        # ========================================================
        # TIMEOUT COM RESULTADO INDETERMINADO
        # ========================================================
        #
        # Um timeout não prova que o Agent deixou de receber o
        # comando. O processo pode ter sido iniciado enquanto a
        # resposta HTTP se perdeu ou demorou além do limite.
        #
        # Portanto NÃO finalizamos a Execution como error.
        #
        # Ela permanece running e será posteriormente reconciliada
        # através de /execution/status pelo mecanismo já existente.
        # ========================================================

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=request.user_id
        )

        logger.warning(
            "Timeout ao aguardar confirmação de início do Agent",
            extra={
                "event": "execution_start_timeout",
                **contexto_log,
                "status": "running",
                "result": "indeterminate",
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

        return {
            "status": "running",
            "message": (
                "Confirmação do Agent não foi recebida no prazo. "
                "A execução será reconciliada automaticamente."
            ),
            "agent_id": agent_id,
            "robot_id": robot_id,
            "execution_id": execution_id,
            "confirmation_pending": True
        }

    except requests.RequestException as error:

        # ========================================================
        # FALHA DE COMUNICAÇÃO COM RESULTADO INDETERMINADO
        # ========================================================
        #
        # Depois que o POST /execution/run foi enviado, uma falha
        # de transporte não permite afirmar com segurança que o
        # Agent deixou de iniciar o Robot.
        #
        # Mantemos a Execution em running e deixamos a confirmação
        # para o reconciliador.
        # ========================================================

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=request.user_id
        )

        logger.error(
            "Falha de comunicação ao aguardar início da execução",
            extra={
                "event": "execution_start_request_failed",
                **contexto_log,
                "status": "running",
                "result": "indeterminate",
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

        return {
            "status": "running",
            "message": (
                "Não foi possível confirmar imediatamente "
                "o início da execução no Agent. "
                "A execução será reconciliada automaticamente."
            ),
            "agent_id": agent_id,
            "robot_id": robot_id,
            "execution_id": execution_id,
            "confirmation_pending": True
        }
    # ========================================================
    # 12. VALIDA EXECUÇÃO
    # ========================================================

    if response.status_code != 200:

        # ========================================================
        # AGENT RECUSOU A EXECUÇÃO
        # ========================================================
        # A execução já foi criada no banco como "running".
        # Como o Agent recusou o comando, precisamos finalizar
        # essa execução como "error".
        # ========================================================

        db = SessionLocal()

        try:

            execucao = db.query(Execution).filter(
                Execution.id == execution_id
            ).first()

            if execucao:
                execucao.status = "error"
                execucao.finished_at = datetime.now()
                execucao.error_message = (
                    "Agent recusou o comando de execução. "
                    f"HTTP {response.status_code}."
                )

                db.commit()

        finally:
            db.close()

        # ========================================================
        # LOG TÉCNICO - AGENT RECUSOU A EXECUÇÃO
        # ========================================================

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=request.user_id
        )

        logger.error(
            "Agent recusou o comando de execução",
            extra={
                "event": "execution_command_rejected",
                **contexto_log,
                "status": "error",
                "status_before": "running",
                "status_after": "error",
                "http_status": response.status_code
            }
        )

        return {
            "status": "error",
            "message": "Agent recusou o comando de execução",
            "agent_id": agent_id,
            "robot_id": robot_id,
            "execution_id": execution_id,
            "http_status": response.status_code
        }


    try:

        execution_response = response.json()

    except ValueError:

        # ========================================================
        # AGENT RETORNOU JSON INVÁLIDO
        # ========================================================
        # A execução já foi criada como "running".
        # Como não conseguimos interpretar a resposta do Agent,
        # finalizamos a execução como "error".
        # ========================================================

        db = SessionLocal()

        try:

            execucao = db.query(Execution).filter(
                Execution.id == execution_id
            ).first()

            if execucao:
                execucao.status = "error"
                execucao.finished_at = datetime.now()
                execucao.error_message = (
                    "Agent retornou uma resposta inválida "
                    "ao iniciar a execução."
                )

                db.commit()

        finally:
            db.close()


        # ========================================================
        # LOG TÉCNICO - RESPOSTA INVÁLIDA DO AGENT
        # ========================================================

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=request.user_id
        )

        logger.error(
            "Agent retornou JSON inválido ao iniciar execução",
            extra={
                "event": "execution_start_invalid_json",
                **contexto_log,
                "status": "error",
                "status_before": "running",
                "status_after": "error"
            }
        )

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido na execução",
            "agent_id": agent_id,
            "robot_id": robot_id,
            "execution_id": execution_id
        }



    # ========================================================
    # 12.0 BUSCA O PID REAL DA EXECUÇÃO
    # ========================================================

    pid = execution_response.get("pid")


    # ========================================================
    # 12.0.1 VALIDA PID DA EXECUÇÃO
    # ========================================================
    #
    # Uma resposta "success" do Agent só representa uma
    # execução realmente iniciada quando existe um PID.
    #
    # Isso impede manter a Execution em running quando a
    # thread do Agent falhou antes do subprocess.Popen().
    # ========================================================

    if (
        execution_response.get("status") == "success"
        and pid is None
    ):

        db = SessionLocal()

        try:

            execucao = db.query(Execution).filter(
                Execution.id == execution_id
            ).first()

            if execucao and execucao.status == "running":

                execucao.status = "error"
                execucao.finished_at = datetime.now()
                execucao.error_message = (
                    "Agent informou início da execução "
                    "sem disponibilizar o PID do processo."
                )

                db.commit()

        finally:

            db.close()

        logger.error(
            "Agent informou execução iniciada sem PID",
            extra={
                "event": "execution_started_without_pid",
                "execution_id": execution_id,
                "robot_id": robot_id,
                "agent_id": agent_id,
                "user_id": request.user_id,
                "status": "error",
                "status_before": "running",
                "status_after": "error"
            }
        )

        return {
            "status": "error",
            "message": (
                "Agent não confirmou a criação "
                "do processo do Robot."
            ),
            "agent_id": agent_id,
            "robot_id": robot_id,
            "execution_id": execution_id
        }
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

                # Neste momento o Agent já retornou o PID real
                # e ele já foi persistido na Execution.
                contexto_log = obter_contexto_execucao_log(
                    execution_id=execution_id,
                    robot_id=robot_id,
                    agent_id=agent_id
                )

                logger.info(
                    "Processo do robô iniciado no Agent",
                    extra={
                        "event": "execution_started",
                        **contexto_log,
                        "pid": pid,
                        "status": "running"
                    }
                )

        finally:
            db.close()
    # ========================================================
    # 12.1 VALIDA STATUS DA EXECUÇÃO
    # ========================================================

    if execution_response.get("status") != "success":

        # ========================================================
        # AGENT NÃO CONSEGUIU INICIAR O ROBÔ
        # ========================================================
        # A execução já foi criada como "running".
        # Como o Agent informou que não conseguiu iniciar,
        # finalizamos a execução como "error".
        # ========================================================

        db = SessionLocal()

        try:

            execucao = db.query(Execution).filter(
                Execution.id == execution_id
            ).first()

            if execucao:
                execucao.status = "error"
                execucao.finished_at = datetime.now()

                execucao.error_message = execution_response.get(
                    "message",
                    "Agent recusou a execução do Robot"
                )

                db.commit()

        finally:
            db.close()


        # ========================================================
        # LOG TÉCNICO - AGENT NÃO CONSEGUIU INICIAR
        # ========================================================

        contexto_log = obter_contexto_execucao_log(
            execution_id=execution_id,
            robot_id=robot_id,
            agent_id=agent_id,
            user_id=request.user_id
        )

        logger.error(
            "Agent não conseguiu iniciar o robô",
            extra={
                "event": "execution_start_failed",
                **contexto_log,
                "status": "error",
                "status_before": "running",
                "status_after": "error",
                "error_message": execution_response.get(
                    "message",
                    "Agent recusou a execução do Robot"
                )
            }
        )

        # ========================================================
        # DEVOLVE AO FRONTEND A CAUSA REAL INFORMADA PELO AGENT
        # ========================================================
        #
        # O Agent já devolve em "message" a causa específica da
        # falha ocorrida antes da criação do processo do Robot.
        #
        # Antes, o Control Room descartava essa informação neste
        # retorno e sempre enviava a mensagem genérica:
        #
        #     "Agent recusou a execução do Robot"
        #
        # Isso escondia erros importantes, como falha de sessão,
        # token Windows, runtime Python ou CreateProcessAsUser.
        #
        # Mantemos uma mensagem fallback apenas para o caso de
        # algum Agent antigo não fornecer o campo "message".
        # ========================================================

        mensagem_erro_agent = execution_response.get(
            "message",
            "Agent recusou a execução do Robot"
        )

        return {

            "status": "error",

            # Propaga para o frontend a causa real devolvida
            # pelo Agent.
            "message": mensagem_erro_agent,

            "agent_id": agent_id,

            "robot_id": robot_id,

            "execution_id": execution_id,

            "robot_name": robot_name,

            "filename": robot_filename,

            "deploy": deploy_response,

            # Preserva também a resposta completa do Agent
            # para diagnóstico e compatibilidade.
            "execution": execution_response

        }


    # ========================================================
    # 13. RETORNO FINAL
    # ========================================================

    return {

        "status": "success",

        "message": "Robot enviado para o Agent e execução iniciada",

        "agent_id": agent_id,

        "source_type": source_type,

        "robot_id": robot_id,

        "project_id": project_id,

        "robot_name": robot_name,

        "filename": robot_filename,

        "version": robot_version,

        "deploy": deploy_response,

        "execution": execution_response

    }
# ============================================================

# ============================================================
# RECONCILIA EXECUÇÃO RUNNING COM O ESTADO REAL DO AGENT
# ============================================================

def reconciliar_execucao_running(
    execution_id: int,
):
    """
    Reconcilia uma Execution que continua como "running" no
    Control Room com o estado real conhecido pelo Agent.

    Esta função existe principalmente para recuperar situações
    em que:

        Robot terminou no Agent
                ↓
        callback final falhou
                ↓
        Control Room permaneceu com status "running"

    IMPORTANTE:
    - indisponibilidade do Agent NÃO vira erro da execução;
    - Agent ainda executando NÃO altera a Execution;
    - somente um resultado final pertencente ao MESMO
      execution_id pode finalizar a Execution.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. CARREGA A EXECUÇÃO
        # ====================================================

        execucao = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id
            )
            .first()
        )

        if not execucao:

            return {
                "status": "ignored",
                "reason": "execution_not_found",
            }

        # Só reconciliamos execuções ainda abertas.
        if execucao.status != "running":

            return {
                "status": "ignored",
                "reason": "execution_not_running",
            }

        # ====================================================
        # 2. CARREGA O AGENT DONO DA EXECUÇÃO
        # ====================================================

        agent = (
            db.query(Agent)
            .filter(
                Agent.agent_id == execucao.agent_id,
                Agent.is_active == 1,
            )
            .first()
        )

        if not agent:

            # Não concluímos nada.
            #
            # Ausência/inatividade do Agent não prova que o
            # Robot falhou.
            return {
                "status": "waiting",
                "reason": "agent_not_available",
            }

        agent_id = agent.agent_id
        agent_host = agent.host
        agent_port = agent.port
        agent_token_encrypted = agent.agent_token_encrypted

        # ====================================================
        # PID REGISTRADO PELO CONTROL ROOM
        # ====================================================
        #
        # Guardamos o PID antes de fechar a sessão do banco.
        #
        # Esse PID será utilizado somente se o Agent informar
        # que atualmente conhece outra execution_id.
        #
        # Nesse cenário, consultaremos o próprio Agent para
        # descobrir se o processo antigo ainda existe na VM.
        # ====================================================

        execution_pid = execucao.pid

    finally:

        db.close()

    # ========================================================
    # 3. CONSULTA O ESTADO REAL DO AGENT
    # ========================================================
    #
    # A chamada HTTP acontece fora da sessão de banco.
    # Não mantemos transação aberta durante operação de rede.
    # ========================================================

    try:

        agent_token = descriptografar_agent_token(
            agent_token_encrypted
        )

        response = requests.get(
            (
                f"http://{agent_host}:"
                f"{agent_port}/execution/status"
            ),
            headers={
                "Authorization": (
                    f"Bearer {agent_token}"
                )
            },
            timeout=5,
        )

        if response.status_code != 200:

            return {
                "status": "waiting",
                "reason": "agent_http_error",
            }

        try:

            estado_agent = response.json()

        except ValueError:

            return {
                "status": "waiting",
                "reason": "agent_invalid_json",
            }

    except requests.RequestException:

        # Falha de rede não é evidência de falha do Robot.
        return {
            "status": "waiting",
            "reason": "agent_unreachable",
        }

    except Exception:

        # Também não convertemos falhas internas de consulta
        # em resultado falso da automação.
        return {
            "status": "waiting",
            "reason": "agent_status_unavailable",
        }

    # ========================================================
    # 4. ANALISA A ÚLTIMA EXECUÇÃO CONHECIDA PELO AGENT
    # ========================================================

    last_execution = (
        estado_agent.get("last_execution")
        or {}
    )

    agent_execution_id = last_execution.get(
        "execution_id"
    )

    agent_execution_status = last_execution.get(
        "status"
    )

    # O resultado precisa pertencer EXATAMENTE à Execution
    # que estamos reconciliando.
    #
    # Nunca usamos o resultado de outra execução para
    # finalizar esta.
    if str(agent_execution_id) != str(execution_id):

        # ====================================================
        # EXECUÇÃO NÃO É MAIS A CONHECIDA PELO AGENT
        # ====================================================
        #
        # Isso NÃO significa automaticamente que a execução
        # antiga terminou.
        #
        # Exemplo:
        #
        # Control Room:
        #     Execution 372 = running
        #     PID = 11868
        #
        # Agent:
        #     já conhece outra execution_id
        #
        # Antes, o Control Room simplesmente retornava
        # "different_agent_execution" e a Execution 372 podia
        # permanecer eternamente como "running".
        #
        # Agora consultamos o próprio Agent para descobrir se
        # o PID registrado para a execução antiga ainda existe
        # na máquina.
        # ====================================================

        if execution_pid is None:

            # Sem PID não temos evidência suficiente para
            # afirmar que o processo desapareceu.
            #
            # Portanto, preservamos o comportamento seguro:
            # a execução continua aguardando reconciliação.
            return {
                "status": "waiting",
                "reason": "different_agent_execution_without_pid",
            }

        try:

            # ------------------------------------------------
            # CONSULTA O PID NA PRÓPRIA MÁQUINA DO AGENT
            # ------------------------------------------------
            #
            # O endpoint /execution/process/{pid} apenas
            # verifica a existência do processo.
            #
            # Ele NÃO encerra nem modifica o processo.
            # ------------------------------------------------

            process_response = requests.get(
                (
                    f"http://{agent_host}:"
                    f"{agent_port}/execution/process/"
                    f"{execution_pid}"
                ),
                headers={
                    "Authorization": (
                        f"Bearer {agent_token}"
                    )
                },
                timeout=5,
            )

            # Se o Agent não conseguiu responder corretamente,
            # não alteramos o status da Execution.
            if process_response.status_code != 200:

                return {
                    "status": "waiting",
                    "reason": "process_check_http_error",
                }

            try:

                process_state = process_response.json()

            except ValueError:

                return {
                    "status": "waiting",
                    "reason": "process_check_invalid_json",
                }

        except requests.RequestException:

            # Falha de rede não prova que o processo morreu.
            return {
                "status": "waiting",
                "reason": "process_check_unreachable",
            }

        except Exception:

            # Qualquer falha inesperada durante a consulta
            # também mantém a Execution intacta.
            return {
                "status": "waiting",
                "reason": "process_check_unavailable",
            }

        processo_existe = process_state.get(
            "exists"
        )

        # ====================================================
        # PID AINDA EXISTE
        # ====================================================
        #
        # Mesmo que o Agent já esteja apontando para outra
        # execution_id, não vamos finalizar automaticamente
        # uma Execution cujo PID ainda está presente.
        # ====================================================

        if processo_existe is True:

            return {
                "status": "waiting",
                "reason": "different_agent_execution_process_exists",
            }

        # ====================================================
        # AGENT NÃO CONSEGUIU DETERMINAR
        # ====================================================
        #
        # exists=None significa que o próprio Agent não teve
        # evidência suficiente para dizer se o PID existe.
        #
        # Portanto, também não alteramos o banco.
        # ====================================================

        if processo_existe is not False:

            return {
                "status": "waiting",
                "reason": "process_existence_unknown",
            }

        # ====================================================
        # PROCESSO NÃO EXISTE MAIS
        # ====================================================
        #
        # Agora temos as duas evidências:
        #
        # 1. o Agent já não reconhece esta execution_id como
        #    sua execução atual/última;
        #
        # 2. o PID registrado pelo Control Room não existe
        #    mais na máquina do Agent.
        #
        # Não sabemos se o Robot terminou com success, error
        # ou stopped. Portanto o estado correto é "unknown".
        # ====================================================

        db = SessionLocal()

        try:

            # ------------------------------------------------
            # ATUALIZAÇÃO CONDICIONAL
            # ------------------------------------------------
            #
            # Revalidamos que a Execution continua "running".
            #
            # Isso evita sobrescrever um callback final que
            # possa ter chegado enquanto consultávamos o Agent.
            # ------------------------------------------------

            execucao = (
                db.query(Execution)
                .filter(
                    Execution.id == execution_id,
                    Execution.agent_id == agent_id,
                    Execution.status == "running",
                )
                .first()
            )

            if not execucao:

                return {
                    "status": "ignored",
                    "reason": "execution_already_finalized",
                }

            execucao.status = "unknown"
            execucao.finished_at = datetime.now()
            execucao.error_message = (
                "Estado final desconhecido. "
                "O processo não está mais presente no Agent."
            )

            db.commit()

        except Exception:

            db.rollback()
            raise

        finally:

            db.close()

        logger.warning(
            "Execution órfã reconciliada como unknown",
            extra={
                "event": "execution_reconciled_unknown",
                "execution_id": execution_id,
                "agent_id": agent_id,
                "pid": execution_pid,
            }
        )

        return {
            "status": "reconciled",
            "execution_id": execution_id,
            "execution_status": "unknown",
            "reason": "process_no_longer_exists",
        }

    # Ainda está realmente rodando.
    if agent_execution_status == "running":

        return {
            "status": "running",
            "reason": "agent_confirms_running",
        }

    # Só aceitamos estados terminais conhecidos.
    if agent_execution_status not in {
        "success",
        "error",
        "stopped",
    }:

        return {
            "status": "waiting",
            "reason": "agent_result_not_terminal",
        }

    # ========================================================
    # 5. FINALIZA DE FORMA CONDICIONAL
    # ========================================================
    #
    # Reabrimos uma sessão e verificamos novamente status
    # "running".
    #
    # Isso evita sobrescrever um callback que tenha chegado
    # enquanto consultávamos o Agent.
    # ========================================================

    db = SessionLocal()

    try:

        execucao = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id,
                Execution.agent_id == agent_id,
                Execution.status == "running",
            )
            .first()
        )

        if not execucao:

            return {
                "status": "ignored",
                "reason": "execution_already_finalized",
            }

        finished_at = last_execution.get(
            "finished_at"
        )

        finished_at_db = datetime.now()

        if finished_at:

            try:

                finished_at_db = datetime.fromisoformat(
                    finished_at
                )

            except (TypeError, ValueError):
                pass

        execucao.status = agent_execution_status
        execucao.finished_at = finished_at_db

        # Em sucesso não deixamos mensagem de erro residual.
        if agent_execution_status == "success":

            execucao.error_message = None

        else:

            execucao.error_message = (
                last_execution.get("message")
                or (
                    "Resultado final recuperado "
                    "diretamente do Agent."
                )
            )

        db.commit()

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()

    logger.warning(
        "Execution reconciliada a partir do estado do Agent",
        extra={
            "event": "execution_reconciled",
            "execution_id": execution_id,
            "agent_id": agent_id,
            "status_after": agent_execution_status,
        }
    )

    return {
        "status": "reconciled",
        "execution_id": execution_id,
        "execution_status": agent_execution_status,
    }