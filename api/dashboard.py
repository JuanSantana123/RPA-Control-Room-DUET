# ============================================================
# ROUTER DO DASHBOARD
# ============================================================

from fastapi import APIRouter
from database import SessionLocal
from models import Agent, Robot


router = APIRouter(
    tags=["Dashboard"]
)


# ============================================================
# HEALTH DO CONTROL ROOM
# ============================================================

@router.get("/health")
def health():

    return {
        "status": "online",
        "service": "RPA Control Room"
    }


# ============================================================
# API ESTATÍSTICAS DO DASHBOARD
# ============================================================
#
# Esta API fornece os principais indicadores do Dashboard
# para o frontend React.
#
# Indicadores retornados:
#
# - total_agents   → quantidade total de Agents cadastrados
# - agents_online  → quantidade de Agents online
# - total_robots   → quantidade total de robôs cadastrados
#
# ============================================================

@router.get("/dashboard/stats")
def dashboard_stats():

    # Abre uma sessão com o banco de dados.
    db = SessionLocal()

    try:

        # ========================================================
        # TOTAL DE AGENTS
        # ========================================================

        total_agents = db.query(Agent).count()

        # ========================================================
        # AGENTS ONLINE
        # ========================================================

        agents_online = db.query(Agent).filter(
            Agent.status == "online"
        ).count()

        # ========================================================
        # TOTAL DE ROBÔS
        # ========================================================

        total_robots = db.query(Robot).count()

        # ========================================================
        # RETORNO
        # ========================================================

        return {
            "status": "success",
            "total_agents": total_agents,
            "agents_online": agents_online,
            "total_robots": total_robots
        }

    except Exception as error:

        # ========================================================
        # TRATAMENTO DE ERRO
        # ========================================================

        return {
            "status": "error",
            "message": "Não foi possível carregar as estatísticas do Dashboard",
            "error": str(error)
        }

    finally:

        # Fecha a conexão com o banco independentemente
        # de a consulta ter funcionado ou apresentado erro.
        db.close()