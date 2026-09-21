from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import criar_banco
# Carrega a mesma lista de Origins confiáveis utilizada
# pela proteção das sessões autenticadas por cookie.
from auth.origin_security import obter_origins_permitidos
from permissions import (
    criar_permissoes_iniciais,
    criar_admin_inicial,
    sincronizar_permissoes_administrador,
)

# ============================================================
# LOGGING CENTRAL DO CONTROL ROOM
# ============================================================
#
# A configuração do logging estruturado fica centralizada
# em core.logging_config.
#
# Ao importar este módulo:
# - o formatter JSON é configurado;
# - o arquivo de log é configurado;
# - a rotação diária é configurada;
# - o logger principal "control_room" fica disponível.
# ============================================================

from core.logging_config import logger
# Importa os modelos SQLAlchemy antes da criação das tabelas.
#
# Isso garante que todas as classes declaradas em models.py,
# incluindo DevelopmentFolder e AutomationProject,
# sejam registradas em Base.metadata antes da chamada
# de criar_banco().
#
# O import é intencional mesmo que "models" não seja usado
# diretamente neste arquivo.
import models
import threading

from api.roles import router as roles_router
from api.user_roles import router as user_roles_router

# ============================================================
# ROUTERS DA API
# ============================================================

from api.agents import (
    router as agents_router,
    monitorar_agents
)
# Importa o router responsável exclusivamente
# pelo heartbeat enviado pelos Agents das VMs.
from api.agent_heartbeat import router as agent_heartbeat_router
# Importa o router responsável pelas APIs
# de comunicação das execuções com os Agents.
from api.agent_executions import router as agent_executions_router
from api.executions import router as executions_router
from api.robots import router as robots_router
# Importa o router responsável pela área
# de Desenvolvimento do DUET CORE.
from api.development import router as development_router
# Importa o router responsável pelo módulo de
# Bibliotecas reutilizáveis do DUET CORE.
from api.libraries import router as libraries_router
from api.dashboard import router as dashboard_router
# Router HTTP responsável pelas operações de agendamentos.
from api.schedules import (
    router as schedules_router,
)
# Engine executada em background responsável por verificar
# e disparar os agendamentos cadastrados no Control Room.
from scheduler.engine import (
    iniciar_scheduler,
)

# ============================================================
# EXECUTION QUEUE
# ============================================================
#
# O Worker da fila agora possui lifecycle explícito.
#
# Ele não é mais iniciado como efeito colateral do import
# de api.executions.
# ============================================================

from executions.queue import (
    iniciar_worker_fila,
)
# Importa o router responsável pelas rotas de logs.
from api.logs import router as logs_router
# Importa o router responsável pelas rotas
# de autenticação e gerenciamento de usuários.
from api.auth import router as auth_router
# Importa o router responsável pelas rotas
from api.vault import router as vault_router
# Importa o router responsável pelas credenciais
# armazenadas dentro do Vault.
from api.vault_credentials import (
    router as vault_credentials_router,
    master_key_router
)
# Importa o router técnico utilizado pelo Agent
# para solicitar credenciais ao Control Room.
#
# Este router não utiliza a sessão do usuário.
# A autenticação é feita pelo agent_token.
#
# IMPORTANTE:
# A implementação da consulta das credenciais
# está no módulo api.vault_credentials.
from api.vault_credentials import agent_router as vault_agent_router
# Importa o router responsável pelas permissões
from api.role_vault_permissions import router as role_vault_permissions_router
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
# Registra a API de heartbeat dos Agents.
# Essa rota é utilizada pelos Agents das VMs
# e não depende da sessão do usuário.
app.include_router(agent_heartbeat_router)
# Registra as APIs utilizadas pelos Agents
# para comunicar resultados de execução.
app.include_router(agent_executions_router)
# Registra todas as APIs relacionadas às execuções.
app.include_router(executions_router)
# Registra todas as APIs relacionadas aos robôs.
app.include_router(robots_router)
# Registra as APIs responsáveis pelos projetos
# e pastas da área de Desenvolvimento.
app.include_router(development_router)
# Registra as APIs responsáveis pelas bibliotecas reutilizáveis.
app.include_router(libraries_router)
# Registra todas as APIs relacionadas ao dashboard.
app.include_router(dashboard_router)
# Registra todas as APIs relacionadas aos agendamentos.
app.include_router(schedules_router)
# Registra todas as APIs relacionadas aos logs.
app.include_router(logs_router)
# Registra as rotas de autenticação na aplicação.
# Como o auth_router possui prefixo "/auth",
# as rotas de autenticação ficam sob:
#
# /auth/*
# As rotas públicas de autenticação são:
#
# POST /auth/login
#     Autenticação utilizada pelo Frontend.
#
# POST /auth/token
#     Autenticação utilizada para obtenção de Bearer Token
#     quando o usuário possui a permissão API:access.
#
# As demais rotas de /auth exigem autenticação e, quando
# aplicável, autorização RBAC.
app.include_router(auth_router)
# Registra as APIs responsáveis pelo gerenciamento das Roles.
app.include_router(roles_router)
# ============================================================
# VAULT
# ============================================================
#
# Registra as APIs responsáveis pelo gerenciamento
# das pastas e credenciais do Vault.
#
# O router já possui o prefixo "/vault",
# portanto suas rotas ficam:
#
# POST /vault/folders
# GET  /vault/folders
# ============================================================

app.include_router(vault_router)
# Registra as APIs responsáveis pelas credenciais
# armazenadas dentro do Vault.
app.include_router(vault_credentials_router)


# Registra as APIs responsáveis pela administração
# da Master Key do Vault.
#
# Rotas disponibilizadas:
#
# POST /vault/master-key/export
# POST /vault/master-key/import
app.include_router(master_key_router)


# Registra as APIs responsáveis pelas credenciais associadas aos Agents.
app.include_router(vault_agent_router)


# Registra as APIs responsáveis pelo gerenciamento dos usuarios e suas roles.
app.include_router(user_roles_router)
# Registra as APIs responsáveis pelo gerenciamento dos roles e suas permissões de acesso ao Vault.
app.include_router(role_vault_permissions_router)
# ============================================================

# ============================================================
# CORS
# ============================================================
#
# O CORS e a proteção das sessões por cookie utilizam a mesma
# fonte de configuração.
#
# Desenvolvimento padrão:
#
#     http://localhost:5173
#
# Produção:
#
#     CONTROL_ROOM_ALLOWED_ORIGINS=https://duet.empresa.com.br
#
# Múltiplos Origins podem ser separados por vírgula.
# ============================================================

ALLOWED_ORIGINS = obter_origins_permitidos()


app.add_middleware(
    CORSMiddleware,

    # Origins explicitamente confiáveis.
    allow_origins=ALLOWED_ORIGINS,

    # Necessário porque o Frontend utiliza session_id
    # através de cookie.
    allow_credentials=True,

    # Mantemos o comportamento HTTP atual da aplicação.
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================================
# INÍCIO DA APLICAÇÃO
# ============================================================

logger.info(
    "Inicialização do Control Room iniciada",
    extra={
        "event": "control_room_starting",
        "status": "starting"
    }
)

# ============================================================
# BANCO DE DADOS
# ============================================================
try:

    criar_banco()

    logger.info(
        "Banco de dados inicializado",
        extra={
            "event": "database_initialized",
            "status": "success"
        }
    )

except Exception as error:

    logger.exception(
        "Falha ao inicializar banco de dados",
        extra={
            "event": "database_initialization_failed",
            "status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
    )

    raise


# ============================================================
# INICIALIZA PERMISSÕES DO SISTEMA
# ============================================================

# Garante que o catálogo básico de permissões exista no banco.
#
# A função é idempotente, portanto permissões já existentes
# não serão duplicadas.
try:

    criar_permissoes_iniciais()

    logger.info(
        "Permissões iniciais verificadas",
        extra={
            "event": "permissions_initialized",
            "status": "success"
        }
    )

except Exception as error:

    logger.exception(
        "Falha ao inicializar permissões",
        extra={
            "event": "permissions_initialization_failed",
            "status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
    )

    raise


# ============================================================
# ADMINISTRADOR INICIAL
# ============================================================

# Se o banco ainda não possuir nenhum usuário,
# cria automaticamente o administrador inicial:
#
#     usuário: admin
#     senha:   gerada aleatoriamente durante o bootstrap
#     role:    Administrador
#
# A senha inicial é exibida no terminal somente durante
# a criação do primeiro administrador.
#
# Apenas o hash da senha é armazenado no banco de dados.
#
# O administrador recebe todas as permissões existentes
# no catálogo.
#
# A função também é idempotente:
# se já existir algum usuário, nenhuma conta será criada
# ou alterada.
try:

    criar_admin_inicial()

    logger.info(
        "Administrador inicial verificado",
        extra={
            "event": "initial_admin_checked",
            "status": "success"
        }
    )

except Exception as error:

    logger.exception(
        "Falha ao verificar administrador inicial",
        extra={
            "event": "initial_admin_check_failed",
            "status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
    )

    raise


# ============================================================
# SINCRONIZA PERMISSÕES DA ROLE ADMINISTRADOR
# ============================================================
#
# O catálogo de Permissions pode crescer entre versões do DUET.
#
# Em uma instalação nova, criar_admin_inicial() já concede todas
# as Permissions existentes à Role Administrador.
#
# Em uma instalação já existente, porém, novas Permissions podem
# ter sido criadas por criar_permissoes_iniciais().
#
# Esta sincronização garante que a Role Administrador continue
# possuindo todas as Permissions disponíveis no sistema após
# upgrades, sem depender do nome do usuário que possui a Role.
#
# A função é idempotente e adiciona somente relacionamentos que
# ainda não existem.
# ============================================================

try:

    sincronizar_permissoes_administrador()

    logger.info(
        "Permissões da Role Administrador sincronizadas",
        extra={
            "event": "administrator_permissions_synchronized",
            "status": "success"
        }
    )

except Exception as error:

    logger.exception(
        "Falha ao sincronizar permissões da Role Administrador",
        extra={
            "event": "administrator_permissions_sync_failed",
            "status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
    )

    raise



# ============================================================
# INICIALIZAÇÃO DO SCHEDULER
# ============================================================
@app.on_event("startup")
def startup_scheduler():
    """
    Inicializa os componentes executados durante
    o startup da aplicação.
    """

    try:

        iniciar_scheduler()
        # ====================================================
        # EXECUTION QUEUE
        # ====================================================
        #
        # Reiniciar o Control Room não perde Executions queued,
        # porque a fila é persistida no banco.
        # ====================================================

        iniciar_worker_fila()

        logger.info(
            "Scheduler inicializado",
            extra={
                "event": "scheduler_started",
                "status": "success"
            }
        )

        threading.Thread(
            target=monitorar_agents,
            daemon=True
        ).start()

        logger.info(
            "Monitoramento de Agents inicializado",
            extra={
                "event": "agent_monitor_started",
                "status": "success"
            }
        )

        logger.info(
            "Control Room inicializado",
            extra={
                "event": "control_room_ready",
                "status": "ready"
            }
        )

    except Exception as error:

        logger.exception(
            "Falha durante a inicialização do Control Room",
            extra={
                "event": "control_room_startup_failed",
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

        raise

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
