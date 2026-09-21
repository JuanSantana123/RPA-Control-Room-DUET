
# ============================================================
# MÓDULOS DO SCHEDULER
# ============================================================
#
# O router HTTP utiliza os cálculos temporais do Scheduler,
# enquanto execução e gerenciamento da thread permanecem
# isolados nos módulos próprios da engine.
# ============================================================

from scheduler.calculations import (
    _horario_para_datetime,
    calcular_proxima_execucao,
)

# Contrato Pydantic utilizado pelos endpoints de criação
# e atualização de agendamentos.
from schemas.schedules import ScheduleCreateRequest
import os

from fastapi import APIRouter, Depends
# Importa a função responsável por verificar se o usuário
# possui a permissão necessária para executar cada operação.
from auth.permissions import require_permission
from database import SessionLocal
# Modelos utilizados pelos endpoints de gerenciamento
# e preservação histórica dos agendamentos.
from models import Schedule, Robot, Agent, Execution
from datetime import datetime
from pathlib import Path

# ============================================================
# CÁLCULOS TEMPORAIS DO SCHEDULER
# ============================================================
#
# As regras responsáveis por calcular datas e horários das
# próximas execuções ficam isoladas no módulo do Scheduler.
#
# O router continua consumindo as mesmas funções e mantendo
# exatamente o comportamento existente.
# ============================================================

from scheduler.calculations import (
    _horario_para_datetime,
    calcular_proxima_execucao,
    proxima_execucao_apos_execucao,
)

# Dependência responsável por validar
# a sessão do usuário autenticado.
from auth.dependencies import get_usuario_atual


router = APIRouter(
    tags=["Schedules"],
    dependencies=[
        Depends(get_usuario_atual)
    ]
)

# ============================================================
# ENDPOINT LISTAR AGENDAMENTOS
# ============================================================
#
# Permite visualizar os agendamentos somente para usuários
# que possuem a permissão:
#
#     Schedules:view
#
# A autenticação do usuário já é validada pelo mecanismo
# global de autenticação do Control Room.
# Aqui adicionamos a autorização específica desta operação.
# ============================================================

@router.get(
    "/schedules",
    summary="Listar agendamentos",
    description=(
        "Retorna todos os agendamentos ativos cadastrados no "
        "Control Room. A resposta contém informações do robô, "
        "Agent, tipo de agendamento, data e horário, periodicidade, "
        "próxima execução e última execução. "
        "Requer a permissão 'Schedules:view'."
    ),
    dependencies=[
        Depends(
            require_permission("Schedules", "view")
        )
    ]
)
def listar_agendamentos():
    """
    Lista os agendamentos ativos.

    Parâmetros:
        Nenhum.

    Permissão necessária:
        Schedules:view
    """

    db = SessionLocal()

    try:

        # Lista todos os agendamentos ainda existentes.
        #
        # IMPORTANTE:
        #   ativo = 1 -> Schedule habilitado para disparos.
        #   ativo = 0 -> Schedule desativado manualmente.
        #
        # Desativar NÃO significa excluir.
        #
        # Portanto, ambos devem permanecer visíveis na tela para que
        # o usuário possa posteriormente editar, reativar ou excluir.
        #
        # Schedules realmente encerrados, como "once" já consumido,
        # são removidos fisicamente pelo Scheduler e naturalmente não
        # aparecerão nesta consulta.
        schedules = (
            db.query(Schedule)
            .order_by(
                Schedule.id.desc()
            )
            .all()
        )

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
# EXECUTAR AGENDAMENTO
# ============================================================

def executar_agendamento(schedule_id):
    logger.info(
        f"[SCHEDULER] DISPARANDO AGENDAMENTO | "
        f"Schedule ID: {schedule_id} | "
        f"Thread: {threading.current_thread().name}"
    )
    # ========================================================
    # CARREGA O AGENDAMENTO
    # ========================================================

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

        # Captura o usuário enquanto o Schedule ainda
        # está vinculado à sessão do banco.
        user_id = schedule.user_id

    finally:

        db.close()


    # ========================================================
    # ESCOLHA DO AGENT
    # ========================================================

    agent_ids = []

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Agent específico
        # ----------------------------------------------------

        if agent_id_agendado:

            # Busca o Agent específico somente se ele
            # continuar ativo no Control Room.
            agent = db.query(
                Agent
            ).filter(
                Agent.agent_id == agent_id_agendado,
                Agent.is_active == 1
            ).first()

            if agent and agent.status == "online":

                agent_ids.append(
                    agent.agent_id
                )

        # ----------------------------------------------------
        # Agent automático
        # ----------------------------------------------------

        else:

            # Seleciona somente Agents ativos e online.
            #
            # Um Agent removido logicamente pode continuar
            # armazenado no banco para preservar o histórico,
            # mas nunca deve receber novas execuções.
            agents = db.query(
                Agent
            ).filter(
                Agent.status == "online",
                Agent.is_active == 1
            ).order_by(
                Agent.name
            ).all()

            agent_ids = [
                agent.agent_id
                for agent in agents
            ]

    finally:

        db.close()


    # ========================================================
    # NENHUM AGENT DISPONÍVEL
    # ========================================================

    if not agent_ids:

        return {
            "status": "waiting",
            "message": "Nenhum Agent online"
        }


    # ========================================================
    # CONSUME O DISPARO DO AGENDAMENTO
    # ========================================================
    #
    # IMPORTANTE:
    #
    # Assim que o horário do agendamento chega, precisamos
    # retirar esse disparo da condição "vencido".
    #
    # Caso contrário, se a execução ficar "queued", o Scheduler
    # roda novamente daqui a 5 segundos e cria outra execução.
    #
    # Para "once":
    #   - desativa definitivamente.
    #
    # Para os demais:
    #   - calcula imediatamente a próxima execução.
    #
    # Dessa forma, o agendamento não fica preso no mesmo
    # horário enquanto a RPA está aguardando na fila.
    # ========================================================

    agora = datetime.now()

    db = SessionLocal()

    try:

        schedule = db.query(
            Schedule
        ).filter(
            Schedule.id == schedule_id,
            Schedule.ativo == 1
        ).first()

        if not schedule:
            return {
                "status": "error",
                "message": "Agendamento não encontrado ou inativo"
            }

        schedule.ultima_execucao = agora

        # ----------------------------------------------------
        # UMA VEZ
        # ----------------------------------------------------

        if schedule.tipo == "once":

            schedule.ativo = 0
            schedule.proxima_execucao = None

        # ----------------------------------------------------
        # RECORRENTES
        # ----------------------------------------------------

        else:

            schedule.proxima_execucao = (
                proxima_execucao_apos_execucao(
                    schedule,
                    agora
                )
            )

        db.commit()

    finally:

        db.close()


    # ========================================================
    # TENTA EXECUTAR
    # ========================================================

    ultimo_resultado = None

    for agent_id in agent_ids:

        try:

            # O Scheduler chama diretamente a função interna de execução.
            #
            # Diferente da execução manual, aqui não existe uma requisição
            # HTTP para o FastAPI resolver o usuário através de Depends.
            #
            # O user_id já foi recuperado do próprio agendamento.
            resultado = _executar_robot(
                agent_id=agent_id,
                request=ExecutionRequest(
                    robot_id=robot_id,
                    user_id=user_id
                )
            )

        except Exception as error:

            resultado = {
                "status": "error",
                "message": str(error)
            }

        ultimo_resultado = resultado


        # ====================================================
        # EXECUÇÃO ACEITA
        # ====================================================
        #
        # Tanto "success" quanto "queued" significam que o
        # disparo do agendamento foi consumido.
        #
        # "queued" NÃO é um erro.
        #
        # A execução ficará aguardando o Agent ficar disponível.
        # ====================================================

        if resultado.get("status") in (
            "success",
            "queued"
        ):

            return resultado


        # ====================================================
        # AGENT OCUPADO
        # ====================================================
        #
        # Se houver múltiplos Agents disponíveis, tenta o
        # próximo.
        # ====================================================

        if resultado.get("message") == \
                "Agent não está disponível para execução":

            continue


        # ====================================================
        # OUTRO ERRO
        # ====================================================
        #
        # Se foi escolhido um Agent específico, não tenta
        # outro automaticamente.
        # ====================================================

        if agent_id_agendado:

            break


    # ========================================================
    # RETORNO FINAL
    # ========================================================

    return ultimo_resultado or {
        "status": "waiting",
        "message": "Nenhum Agent disponível"
    }
# ============================================================
# ENDPOINT EXCLUIR AGENDAMENTO
# ============================================================
#
# Permite excluir um agendamento somente para usuários
# que possuem a permissão:
#
#     Schedules:delete
#
# A autenticação do usuário já é validada pelo router.
# Aqui adicionamos a autorização específica da operação.
# ============================================================

@router.delete(
    "/schedules/{schedule_id}",
    summary="Excluir agendamento",
    description=(
        "Exclui um agendamento cadastrado no Control Room. "
        "O agendamento é identificado pelo parâmetro 'schedule_id'. "
        "Requer a permissão 'Schedules:delete'."
    ),
    dependencies=[
        Depends(
            require_permission("Schedules", "delete")
        )
    ]
)

def delete_schedule(schedule_id: int):
    """
    Exclui definitivamente um agendamento sem remover o
    histórico das execuções que ele já originou.

    Parâmetros:
        schedule_id:
            Identificador único do agendamento.

    Regra de negócio:
        - o Schedule representa planejamento futuro;
        - a Execution representa histórico;
        - excluir o Schedule interrompe novos disparos;
        - Executions existentes são sempre preservadas;
        - schedule_id das Executions históricas é desvinculado;
        - schedule_run_id permanece preservado.

    Permissão necessária:
        Schedules:delete
    """

    db = SessionLocal()

    try:

        # ====================================================
        # LOCALIZA O AGENDAMENTO
        # ====================================================

        schedule = (
            db.query(Schedule)
            .filter(
                Schedule.id == schedule_id
            )
            .first()
        )

        if not schedule:

            return {
                "status": "error",
                "message": "Agendamento não encontrado",
                "schedule_id": schedule_id
            }

        # ====================================================
        # INTERROMPE O PLANEJAMENTO
        # ====================================================
        #
        # Antes de remover o registro, retiramos o Schedule
        # explicitamente da condição de execução.
        #
        # Isso também deixa clara a intenção da operação caso
        # futuramente existam outros passos dentro desta
        # transação.
        # ====================================================

        schedule.ativo = 0
        schedule.proxima_execucao = None

        db.flush()

        # ====================================================
        # PRESERVA O HISTÓRICO DE EXECUÇÕES
        # ====================================================
        #
        # Execution NÃO pertence ao ciclo de vida do Schedule.
        #
        # Removemos somente a FK schedule_id.
        #
        # Permanecem preservados:
        #
        #   - Execution.id
        #   - Robot / nome histórico
        #   - versão
        #   - Agent
        #   - usuário
        #   - status
        #   - início/fim
        #   - erros
        #   - schedule_run_id
        #
        # Portanto, excluir um Schedule nunca apaga o histórico.
        # ====================================================

        executions_desvinculadas = (
            db.query(Execution)
            .filter(
                Execution.schedule_id == schedule_id
            )
            .update(
                {
                    Execution.schedule_id: None
                },
                synchronize_session=False
            )
        )

        # ====================================================
        # REMOVE O PLANEJAMENTO
        # ====================================================

        db.delete(schedule)

        # Schedule + desvinculação das Executions fazem parte
        # da mesma transação.
        db.commit()

        return {
            "status": "success",
            "message": "Agendamento excluído com sucesso",
            "schedule_id": schedule_id,
            "executions_preserved":
                executions_desvinculadas
        }

    except Exception:

        # Nenhum estado parcial é mantido caso a operação falhe.
        db.rollback()

        return {
            "status": "error",
            "message": "Não foi possível excluir o agendamento",
            "schedule_id": schedule_id
        }

    finally:

        db.close()
# ============================================================
# ENDPOINT CRIAR AGENDAMENTO
# ============================================================
#
# Permite criar um novo agendamento somente para usuários
# que possuem a permissão:
#
#     Schedules:create
#
# A função continua recebendo somente o request do agendamento.
# A autorização é feita antes da execução da função.
# ============================================================

@router.post(
    "/schedules",
    summary="Criar agendamento",
    description=(
        "Cria um novo agendamento para execução de um robô. "
        "O agendamento pode ser único, diário, semanal ou mensal. "
        "Também permite configurar intervalo de execução e horário "
        "de término quando aplicável. "
        "Requer a permissão 'Schedules:create'."
    ),
    dependencies=[
        Depends(
            require_permission("Schedules", "create")
        )
    ]
)
def criar_agendamento(
    request: ScheduleCreateRequest,

    # Recupera o usuário autenticado para registrar
    # quem criou o agendamento.
    usuario=Depends(get_usuario_atual)
):
    """
    Cria um novo agendamento.

    Parâmetros:
        request:
            Dados do agendamento, incluindo robô, Agent opcional,
            tipo, data, horário e configurações de periodicidade.

    Permissão necessária:
        Schedules:create
    """

    db = SessionLocal()

    try:

        robot = db.query(
            Robot
        ).filter(
            Robot.id == request.robot_id
        ).first()

        if not robot:

            return {
                "status": "error",
                "message": "Robô não encontrado"
            }


        if request.agent_id:

            # Permite criar o agendamento somente com um Agent
            # que ainda esteja ativo no Control Room.
            #
            # Agents removidos logicamente continuam no banco
            # para preservar o histórico, mas não podem receber
            # novos agendamentos.
            agent = db.query(
                Agent
            ).filter(
                Agent.agent_id == request.agent_id,
                Agent.is_active == 1
            ).first()

            if not agent:

                return {
                    "status": "error",
                    "message": "Agent não encontrado ou inativo"
                }


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


        try:

            data_inicio = datetime.fromisoformat(
                request.data_inicio
            )

        except ValueError:

            return {
                "status": "error",
                "message": "Data de início inválida"
            }


        data_horario = _horario_para_datetime(
            data_inicio,
            request.horario
        )

        if data_horario is None:

            return {
                "status": "error",
                "message": "Horário inválido. Use HH:MM."
            }


        agora = datetime.now()

        # ========================================================
        # VALIDAÇÕES ESPECÍFICAS DO TIPO
        # ========================================================

        # --------------------------------------------------------
        # SEMANAL
        # --------------------------------------------------------
        #
        # Um Schedule semanal precisa possuir pelo menos um
        # dia da semana válido.
        if request.tipo == "weekly":

            dias_validos = {
                "mon",
                "tue",
                "wed",
                "thu",
                "fri",
                "sat",
                "sun",
            }

            dias_selecionados = {
                dia.strip().lower()
                for dia in (
                    request.dias_semana or ""
                ).split(",")
                if dia.strip()
            }

            if not dias_selecionados:

                return {
                    "status": "error",
                    "message": (
                        "Selecione pelo menos um dia da semana."
                    )
                }

            if not dias_selecionados.issubset(
                dias_validos
            ):

                return {
                    "status": "error",
                    "message": (
                        "Existem dias da semana inválidos."
                    )
                }


        # --------------------------------------------------------
        # INTERVALO
        # --------------------------------------------------------

        if request.intervalo_ativo:

            if (
                request.intervalo_valor is None
                or request.intervalo_valor <= 0
            ):

                return {
                    "status": "error",
                    "message": (
                        "Informe um intervalo maior que zero."
                    )
                }

            if request.intervalo_unidade not in (
                "minutes",
                "hours",
            ):

                return {
                    "status": "error",
                    "message": (
                        "Unidade de intervalo inválida."
                    )
                }

            if not request.horario_fim:

                return {
                    "status": "error",
                    "message": (
                        "Informe o horário final do intervalo."
                    )
                }

            fim_intervalo = _horario_para_datetime(
                data_inicio,
                request.horario_fim
            )

            if fim_intervalo is None:

                return {
                    "status": "error",
                    "message": (
                        "Horário final inválido. Use HH:MM."
                    )
                }

            if fim_intervalo <= data_horario:

                return {
                    "status": "error",
                    "message": (
                        "O horário final deve ser posterior "
                        "ao horário inicial."
                    )
                }


        # ========================================================
        # CALCULA PRIMEIRA OCORRÊNCIA
        # ========================================================

        if request.tipo == "once":

            # Uma execução única não possui uma ocorrência futura
            # alternativa. Portanto, o horário configurado precisa
            # efetivamente estar no futuro.
            if data_horario <= agora:

                return {
                    "status": "error",
                    "message": (
                        "O horário informado já passou. "
                        "Selecione uma data e horário futuros."
                    )
                }

            proxima_execucao = data_horario

        else:

            # Recorrências NÃO devem ser rejeitadas simplesmente
            # porque o primeiro horário possível já passou.
            #
            # O cálculo procura a próxima ocorrência futura válida.
            #
            # Exemplo:
            # sábado 18:51 + semanal às 18:50
            # -> domingo 18:50, se domingo estiver selecionado.
            proxima_execucao = calcular_proxima_execucao(

                Schedule(
                    robot_id=request.robot_id,
                    agent_id=request.agent_id,
                    tipo=request.tipo,
                    data_inicio=data_inicio,
                    horario=request.horario,
                    dias_semana=request.dias_semana,
                    intervalo_ativo=(
                        1
                        if request.intervalo_ativo
                        else 0
                    ),
                    intervalo_valor=request.intervalo_valor,
                    intervalo_unidade=request.intervalo_unidade,
                    horario_fim=request.horario_fim
                ),

                agora
            )


        if proxima_execucao is None:

            return {
                "status": "error",
                "message": (
                    "Não foi possível calcular a próxima "
                    "execução. Verifique a data, horário "
                    "e dias selecionados."
                )
            }


        schedule = Schedule(

            robot_id=request.robot_id,

            agent_id=request.agent_id,
                # Usuário que criou o agendamento.
            user_id=usuario.id,

            tipo=request.tipo,

            data_inicio=data_inicio,

            horario=request.horario,

            dias_semana=request.dias_semana,

            intervalo_ativo=(
                1
                if request.intervalo_ativo
                else 0
            ),

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

            "message":
                "Não foi possível criar o agendamento",

            "error": str(error)
        }

    finally:

        db.close()


# ============================================================
# ENDPOINT OPÇÕES PARA NOVO AGENDAMENTO
# ============================================================
#
# Permite consultar as opções disponíveis para criação de
# agendamentos somente para usuários que possuem a permissão:
#
#     Schedules:view
#
# A autenticação do usuário já é validada pelo router.
# Aqui adicionamos a autorização específica da operação.
# ============================================================
@router.get(
    "/schedules/options",
    summary="Consultar opções de agendamento",
    description=(
        "Retorna as opções disponíveis para criação de um agendamento. "
        "A resposta contém os robôs disponíveis no repositório e "
        "os Agents cadastrados no Control Room. "
        "Requer a permissão 'Schedules:view'."
    ),
    dependencies=[
        Depends(
            require_permission("Schedules", "view")
        )
    ]
)
def opcoes_agendamento():
    """
    Retorna as opções disponíveis para criação de agendamentos.

    Parâmetros:
        Nenhum.

    Retorna:
        robots:
            Robôs disponíveis para seleção.

        agents:
            Agents disponíveis para seleção.

    Permissão necessária:
        Schedules:view
    """

    db = SessionLocal()

    try:

        robots_db = db.query(
            Robot
        ).order_by(
            Robot.name
        ).all()

        robots = []

        for robot in robots_db:

            if not robot.file_path:
                continue

            caminho = Path(
                robot.file_path
            )

            if not caminho.exists():
                continue

            robots.append({

                "id": robot.id,

                "name": robot.name
            })


        # Retorna somente Agents ativos para seleção
        # em novos agendamentos.
        #
        # Agents removidos logicamente permanecem no banco
        # para preservar o histórico, mas não podem mais
        # ser selecionados para novas execuções.
        agents_db = db.query(
            Agent
        ).filter(
            Agent.is_active == 1
        ).order_by(
            Agent.name
        ).all()

        agents = [

            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "status": agent.status
            }

            for agent in agents_db
        ]


        return {

            "status": "success",

            "robots": robots,

            "agents": agents
        }

    finally:

        db.close()


# ============================================================
# ENDPOINT CONSULTAR AGENDAMENTO
# ============================================================
#
# Permite consultar um agendamento específico somente para
# usuários que possuem a permissão:
#
#     Schedules:view
#
# A autenticação do usuário já é validada pelo router.
# Aqui adicionamos a autorização específica da operação.
# ============================================================

@router.get(
    "/schedules/{schedule_id}",
    summary="Consultar agendamento",
    description=(
        "Retorna os dados completos de um agendamento específico. "
        "O agendamento é localizado pelo parâmetro 'schedule_id'. "
        "Requer a permissão 'Schedules:view'."
    ),
    dependencies=[
        Depends(
            require_permission("Schedules", "view")
        )
    ]
)
def get_schedule(schedule_id: int):
    """
    Consulta um agendamento específico.

    Parâmetros:
        schedule_id:
            Identificador único do agendamento.

    Permissão necessária:
        Schedules:view
    """

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

                "id": schedule.id,

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
                    bool(schedule.intervalo_ativo),

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
                    bool(schedule.ativo)
            }
        }

    except Exception as error:

        return {

            "status": "error",

            "message":
                "Erro ao consultar agendamento",

            "schedule_id":
                schedule_id,

            "error":
                str(error)
        }

    finally:

        db.close()


# ============================================================
# ENDPOINT ATUALIZAR AGENDAMENTO
# ============================================================
#
# Permite alterar um agendamento somente para usuários
# que possuem a permissão:
#
#     Schedules:edit
#
# A autenticação do usuário já é validada pelo router.
# Aqui adicionamos a autorização específica da operação.
# ============================================================

@router.put(
    "/schedules/{schedule_id}",
    summary="Atualizar agendamento",
    description=(
        "Atualiza as configurações de um agendamento existente. "
        "Permite alterar o robô, Agent, tipo, data, horário, "
        "periodicidade e configurações de intervalo. "
        "Requer a permissão 'Schedules:edit'."
    ),
    dependencies=[
        Depends(
            require_permission("Schedules", "edit")
        )
    ]
)
def update_schedule(
    schedule_id: int,
    request: ScheduleCreateRequest
):
    """
    Atualiza um agendamento existente.

    Parâmetros:
        schedule_id:
            Identificador único do agendamento.

        request:
            Novas configurações do agendamento.

    Permissão necessária:
        Schedules:edit
    """

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

                "message":
                    "Agendamento não encontrado",

                "schedule_id":
                    schedule_id
            }



        # ========================================================
        # VALIDAÇÕES DA EDIÇÃO
        # ========================================================

        tipos_permitidos = {
            "once",
            "daily",
            "weekly",
            "monthly",
        }

        if request.tipo not in tipos_permitidos:

            return {
                "status": "error",
                "message": "Tipo de agendamento inválido"
            }


        # O Robot precisa continuar existindo.
        robot = (
            db.query(Robot)
            .filter(
                Robot.id == request.robot_id
            )
            .first()
        )

        if not robot:

            return {
                "status": "error",
                "message": "Robô não encontrado"
            }


        # Agent específico precisa continuar ativo.
        if request.agent_id:

            agent = (
                db.query(Agent)
                .filter(
                    Agent.agent_id == request.agent_id,
                    Agent.is_active == 1,
                )
                .first()
            )

            if not agent:

                return {
                    "status": "error",
                    "message": "Agent não encontrado ou inativo"
                }


        # Semanal exige pelo menos um dia válido.
        if request.tipo == "weekly":

            dias_validos = {
                "mon",
                "tue",
                "wed",
                "thu",
                "fri",
                "sat",
                "sun",
            }

            dias_selecionados = {
                dia.strip().lower()
                for dia in (
                    request.dias_semana or ""
                ).split(",")
                if dia.strip()
            }

            if (
                not dias_selecionados
                or not dias_selecionados.issubset(
                    dias_validos
                )
            ):

                return {
                    "status": "error",
                    "message": (
                        "Selecione dias da semana válidos."
                    )
                }


        # Intervalo exige configuração completa.
        if request.intervalo_ativo:

            if (
                request.intervalo_valor is None
                or request.intervalo_valor <= 0
            ):

                return {
                    "status": "error",
                    "message": (
                        "Informe um intervalo maior que zero."
                    )
                }

            if request.intervalo_unidade not in (
                "minutes",
                "hours",
            ):

                return {
                    "status": "error",
                    "message": (
                        "Unidade de intervalo inválida."
                    )
                }

            if not request.horario_fim:

                return {
                    "status": "error",
                    "message": (
                        "Informe o horário final do intervalo."
                    )
                }

        data_inicio = datetime.fromisoformat(
            request.data_inicio
        )

        # Converte o horário inicial informado.
        data_horario = _horario_para_datetime(
            data_inicio,
            request.horario
        )

        if data_horario is None:

            return {
                "status": "error",
                "message": "Horário inválido. Use HH:MM."
            }


        if request.intervalo_ativo:

            fim_intervalo = _horario_para_datetime(
                data_inicio,
                request.horario_fim
            )

            if (
                fim_intervalo is None
                or fim_intervalo <= data_horario
            ):

                return {
                    "status": "error",
                    "message": (
                        "O horário final deve ser posterior "
                        "ao horário inicial."
                    )
                }


        # Schedule "once" não pode ser atualizado para uma
        # ocorrência que já passou.
        if (
            request.tipo == "once"
            and data_horario <= datetime.now()
        ):

            return {
                "status": "error",
                "message": (
                    "O horário informado já passou. "
                    "Selecione uma data e horário futuros."
                )
            }


        schedule.robot_id = request.robot_id

        schedule.agent_id = request.agent_id

        schedule.tipo = request.tipo

        schedule.data_inicio = data_inicio

        schedule.horario = request.horario

        schedule.dias_semana = request.dias_semana

        schedule.intervalo_ativo = (
            1
            if request.intervalo_ativo
            else 0
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


        # Recalcula a próxima ocorrência com a configuração
        # já aplicada ao objeto Schedule.
        nova_proxima_execucao = (
            calcular_proxima_execucao(
                schedule,
                datetime.now()
            )
        )

        if nova_proxima_execucao is None:

            db.rollback()

            return {
                "status": "error",
                "message": (
                    "Não foi possível calcular a próxima execução. "
                    "Verifique a data, horário e periodicidade."
                )
            }

        schedule.proxima_execucao = (
            nova_proxima_execucao
        )

        db.commit()

        db.refresh(schedule)


        return {

            "status": "success",

            "message":
                "Agendamento atualizado com sucesso",

            "schedule_id":
                schedule.id
        }

    except Exception as error:

        db.rollback()

        return {

            "status": "error",

            "message":
                "Não foi possível atualizar o agendamento",

            "error":
                str(error)
        }

    finally:

        db.close()


# ============================================================
# ENDPOINT ATIVAR / DESATIVAR AGENDAMENTO
# ============================================================
#
# Permite ativar ou desativar um agendamento somente para
# usuários que possuem a permissão:
#
#     Schedules:edit
#
# A autenticação do usuário já é validada pelo router.
# Aqui adicionamos a autorização específica da operação.
# ============================================================

@router.put(
    "/schedules/{schedule_id}/status",
    summary="Alterar status do agendamento",
    description=(
        "Ativa ou desativa um agendamento existente. "
        "O parâmetro 'ativo' define se o agendamento ficará "
        "habilitado ou desabilitado para execução. "
        "Requer a permissão 'Schedules:edit'."
    ),
    dependencies=[
        Depends(
            require_permission("Schedules", "edit")
        )
    ]
)
def alterar_status_schedule(
    schedule_id: int,
    ativo: bool
):
    """
    Ativa ou desativa um agendamento.

    Parâmetros:
        schedule_id:
            Identificador único do agendamento.

        ativo:
            Define o novo status do agendamento.
            True ativa o agendamento.
            False desativa o agendamento.

    Permissão necessária:
        Schedules:edit
    """

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

                "message":
                    "Agendamento não encontrado",

                "schedule_id":
                    schedule_id
            }


        # ========================================================
        # ATIVAR
        # ========================================================

        if ativo:

            agora = datetime.now()

            # Para Schedule "once", a ocorrência original precisa
            # continuar no futuro.
            if schedule.tipo == "once":

                proxima_execucao = (
                    calcular_proxima_execucao(
                        schedule,
                        agora
                    )
                )

                if (
                    proxima_execucao is None
                    or proxima_execucao <= agora
                ):

                    return {
                        "status": "error",
                        "message": (
                            "Este agendamento único já venceu. "
                            "Edite a data/horário antes de reativá-lo."
                        ),
                        "schedule_id": schedule_id,
                    }

            else:

                # Recorrentes procuram a próxima ocorrência futura
                # válida a partir do momento da reativação.
                proxima_execucao = (
                    calcular_proxima_execucao(
                        schedule,
                        agora
                    )
                )

                if proxima_execucao is None:

                    return {
                        "status": "error",
                        "message": (
                            "Não existe próxima execução válida "
                            "para este agendamento."
                        ),
                        "schedule_id": schedule_id,
                    }

            schedule.proxima_execucao = (
                proxima_execucao
            )

            schedule.ativo = 1


        # ========================================================
        # DESATIVAR
        # ========================================================

        else:

            # Desativar não exclui e não apaga a configuração.
            #
            # O Schedule permanece visível na interface e poderá
            # posteriormente ser editado, reativado ou excluído.
            schedule.ativo = 0


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

            "schedule_id":
                schedule.id,

            "ativo":
                bool(schedule.ativo)
        }

    except Exception as error:

        db.rollback()

        return {

            "status": "error",

            "message":
                "Não foi possível alterar o status "
                "do agendamento",

            "schedule_id":
                schedule_id,

            "error":
                str(error)
        }

    finally:

        db.close()