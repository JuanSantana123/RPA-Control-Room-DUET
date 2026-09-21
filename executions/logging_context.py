# ============================================================
# DUET CORE - EXECUTIONS - CONTEXTO DE LOG
# ============================================================
#
# Responsável por montar o contexto técnico usado nos logs
# das execuções do Control Room.
#
# Este módulo é somente leitura e NÃO altera status, não faz
# commit, não executa robôs e não comunica com Agents.
#
# A função foi extraída literalmente do api/executions.py.
# ============================================================

from database import SessionLocal
from models import Agent, Robot, Execution, User, RobotFolder


def obter_contexto_execucao_log(
    execution_id=None,
    robot_id=None,
    agent_id=None,
    user_id=None
):
    """
    Consulta informações técnicas relacionadas a uma execução
    para enriquecer os logs de observabilidade.

    Esta função é somente leitura:
    - não altera status;
    - não executa commit;
    - não interfere na fila;
    - não envia comandos ao Agent.

    Parâmetros:
        execution_id:
            ID da execução, quando já existir.

        robot_id:
            ID do robô, quando conhecido.

        agent_id:
            ID do Agent, quando conhecido.

        user_id:
            ID do usuário responsável pela execução,
            quando conhecido.

    Retorno:
        Dicionário com os dados disponíveis para o log.
    """

    db = SessionLocal()

    try:

        execucao = None
        robot = None
        agent = None
        usuario = None

        # ========================================================
        # EXECUÇÃO
        # ========================================================

        if execution_id is not None:

            execucao = (
                db.query(Execution)
                .filter(
                    Execution.id == execution_id
                )
                .first()
            )

            if execucao:

                if robot_id is None:
                    robot_id = execucao.robot_id

                if agent_id is None:
                    agent_id = execucao.agent_id

                if user_id is None:
                    user_id = execucao.user_id

        # ========================================================
        # ROBÔ
        # ========================================================

        if robot_id is not None:

            robot = (
                db.query(Robot)
                .filter(
                    Robot.id == robot_id
                )
                .first()
            )

        # ========================================================
        # AGENT
        # ========================================================

        if agent_id is not None:

            agent = (
                db.query(Agent)
                .filter(
                    Agent.agent_id == agent_id
                )
                .first()
            )

        # ========================================================
        # USUÁRIO
        # ========================================================

        if user_id is not None:

            usuario = (
                db.query(User)
                .filter(
                    User.id == user_id
                )
                .first()
            )

        # ========================================================
        # CONTEXTO ESTRUTURADO
        # ========================================================

        contexto = {}

        if execution_id is not None:
            contexto["execution_id"] = execution_id

        if robot_id is not None:
            contexto["robot_id"] = robot_id

        if robot:

            contexto["robot_name"] = robot.name
            contexto["robot_filename"] = robot.filename

            contexto["robot_version"] = getattr(
                robot,
                "version",
                None
            )

            # ========================================================
            # CAMINHO COMPLETO DA PASTA DO ROBÔ PARA O LOG
            # ========================================================
            #
            # O Worker pode chamar este helper logo após iniciar.
            #
            # Por isso, montamos o caminho diretamente aqui e não
            # dependemos da função montar_caminho_pasta(), que está
            # declarada mais abaixo neste arquivo.
            #
            # Esta consulta é somente leitura.
            # ========================================================

            partes_pasta = []
            pasta_atual_id = robot.folder_id

            while pasta_atual_id is not None:

                pasta = (
                    db.query(RobotFolder)
                    .filter(
                        RobotFolder.id == pasta_atual_id
                    )
                    .first()
                )

                if not pasta:
                    break

                partes_pasta.insert(
                    0,
                    pasta.name
                )

                pasta_atual_id = pasta.parent_id

            contexto["robot_folder"] = (
                " / ".join(partes_pasta)
                if partes_pasta
                else "Pasta raiz"
            )

        if agent_id is not None:
            contexto["agent_id"] = agent_id

        if agent:
            contexto["agent_name"] = agent.name

        if user_id is not None:
            contexto["user_id"] = user_id

        if usuario:
            contexto["username"] = usuario.username
            contexto["user_name"] = usuario.name

        # PID só é enviado ao log quando realmente existir.
        if execucao and execucao.pid is not None:
            contexto["pid"] = execucao.pid

        return contexto

    finally:

        db.close()
