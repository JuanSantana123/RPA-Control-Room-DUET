# ============================================================
# ROUTER DE AGENDAMENTOS
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel
from database import SessionLocal
from models import Schedule, Robot, Agent
from datetime import datetime, timedelta
from pathlib import Path
from api.executions import run_agent_robot, ExecutionRequest
import time


router = APIRouter(
    tags=["Schedules"]
)


# ============================================================
# LISTAR AGENDAMENTOS
# ============================================================

@router.get("/api/schedules")
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
# FUNÇÃO AUXILIAR - CONVERTE HORÁRIO
# ============================================================

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


# ============================================================
# CALCULAR PRÓXIMA EXECUÇÃO
# ============================================================

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
    # CONFIGURAÇÕES DE INTERVALO
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


# ============================================================
# PRÓXIMA EXECUÇÃO APÓS UMA EXECUÇÃO
# ============================================================

def proxima_execucao_apos_execucao(
    schedule,
    agora=None
):

    if agora is None:
        agora = datetime.now()


    # ========================================================
    # UMA VEZ
    # ========================================================

    if schedule.tipo == "once":

        return None


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

            proxima = agora + incremento

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


# ============================================================
# EXECUTAR AGENDAMENTO
# ============================================================

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

            agent = db.query(
                Agent
            ).filter(
                Agent.agent_id == agent_id_agendado
            ).first()

            if agent and agent.status == "online":

                agent_ids.append(
                    agent.agent_id
                )

        else:

            agents = db.query(
                Agent
            ).filter(
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

                        schedule.proxima_execucao = (
                            proxima_execucao_apos_execucao(
                                schedule,
                                agora
                            )
                        )

                    db.commit()

            finally:

                db.close()

            return resultado


        # Agent ocupado → tenta o próximo.

        if resultado.get("message") == \
                "Agent não está disponível para execução":

            continue


        # Outro erro → não tenta outro Agent
        # quando um Agent específico foi escolhido.

        if agent_id_agendado:

            break


    return ultimo_resultado or {
        "status": "waiting",
        "message": "Nenhum Agent disponível"
    }


# ============================================================
# SCHEDULER
# ============================================================

def scheduler_loop():

    while True:

        try:

            agora = datetime.now()

            db = SessionLocal()

            try:

                schedules = db.query(
                    Schedule
                ).filter(
                    Schedule.ativo == 1
                ).all()

                # Inicializa próxima execução dos
                # agendamentos que ainda estão NULL.

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
                        or datetime.max
                    )

                    if (
                        schedule.proxima_execucao is not None
                        and schedule.proxima_execucao <= agora
                    )
                ]

            finally:

                db.close()


            for schedule_id in vencidos:

                executar_agendamento(
                    schedule_id
                )

        except Exception as error:

            print(
                f"[SCHEDULER] Erro: {error}"
            )

        # Verifica os agendamentos a cada 5 segundos.

        
        time.sleep(5)


# ============================================================
# INICIAR SCHEDULER
# ============================================================

scheduler_thread = None


def iniciar_scheduler():

    global scheduler_thread

    if (
        scheduler_thread is not None
        and scheduler_thread.is_alive()
    ):

        return

    import threading

    scheduler_thread = threading.Thread(
        target=scheduler_loop,
        daemon=True,
        name="RPA-Scheduler"
    )

    scheduler_thread.start()


# ============================================================
# EXCLUIR AGENDAMENTO
# ============================================================

@router.delete("/api/schedules/{schedule_id}")
def delete_schedule(schedule_id: int):

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
# MODELO DE CRIAÇÃO/ATUALIZAÇÃO
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


# ============================================================
# CRIAR AGENDAMENTO
# ============================================================

@router.post("/api/schedules")
def criar_agendamento(
    request: ScheduleCreateRequest
):

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

            agent = db.query(
                Agent
            ).filter(
                Agent.agent_id == request.agent_id
            ).first()

            if not agent:

                return {
                    "status": "error",
                    "message": "Agent não encontrado"
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

        if data_horario <= agora:

            return {
                "status": "error",
                "message": (
                    "O horário informado já passou. "
                    "Selecione uma data e horário futuros."
                )
            }


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
                    intervalo_ativo=(
                        1
                        if request.intervalo_ativo
                        else 0
                    ),
                    intervalo_valor=request.intervalo_valor,
                    intervalo_unidade=request.intervalo_unidade,
                    horario_fim=request.horario_fim
                ),

                datetime.now()
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
# OPÇÕES PARA NOVO AGENDAMENTO
# ============================================================

@router.get("/api/schedules/options")
def opcoes_agendamento():

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


        agents_db = db.query(
            Agent
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
# CONSULTAR AGENDAMENTO
# ============================================================

@router.get("/api/schedules/{schedule_id}")
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
# ATUALIZAR AGENDAMENTO
# ============================================================

@router.put("/api/schedules/{schedule_id}")
def update_schedule(
    schedule_id: int,
    request: ScheduleCreateRequest
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

                "message":
                    "Agendamento não encontrado",

                "schedule_id":
                    schedule_id
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
# ATIVAR / DESATIVAR AGENDAMENTO
# ============================================================

@router.put("/api/schedules/{schedule_id}/status")
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

                "message":
                    "Agendamento não encontrado",

                "schedule_id":
                    schedule_id
            }


        schedule.ativo = (
            1
            if ativo
            else 0
        )


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