from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import criar_banco
import threading
import logging
from pathlib import Path


# ============================================================
# ROUTERS DA API
# ============================================================

from api.agents import (
    router as agents_router,
    monitorar_agents
)
from api.executions import router as executions_router
from api.robots import router as robots_router
from api.dashboard import router as dashboard_router
from api.schedules import (
    router as schedules_router,
    iniciar_scheduler
)
from api.logs import router as logs_router

# ============================================================
# CONTROL ROOM
# ============================================================

app = FastAPI(
    title="RPA Control Room",
    version="1.0.0"
)


# ============================================================
# REGISTRO DOS ROUTERS
# ============================================================

# Registra todas as APIs relacionadas aos Agents.
app.include_router(agents_router)
# Registra todas as APIs relacionadas às execuções.
app.include_router(executions_router)
# Registra todas as APIs relacionadas aos robôs.
app.include_router(robots_router)
# Registra todas as APIs relacionadas ao dashboard.
app.include_router(dashboard_router)
# Registra todas as APIs relacionadas aos agendamentos.
app.include_router(schedules_router)
# Registra todas as APIs relacionadas aos logs.
app.include_router(logs_router)

# ============================================================
# CORS
# Permite que o frontend React, executando em localhost:5173,
# faça requisições para a API FastAPI, executando em localhost:9000.
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# BANCO DE DADOS
# ============================================================

criar_banco()


# ============================================================
# LOG DO CONTROL ROOM
# ============================================================

LOG_DIRECTORY = Path("logs")
LOG_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = LOG_DIRECTORY / "control_room.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("control_room")




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

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000
    )
