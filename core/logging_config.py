# ============================================================
# DUET CORE - CONFIGURAÇÃO DE LOGGING
# ============================================================
#
# Responsável pela infraestrutura central de logging do
# Control Room.
#
# Este módulo:
# - configura logs estruturados em JSON;
# - adiciona metadados técnicos aos eventos;
# - cria o diretório de logs;
# - configura rotação diária dos arquivos;
# - mantém aproximadamente 30 arquivos de histórico;
# - disponibiliza o logger principal "control_room".
#
# Este módulo NÃO:
# - contém regras de negócio;
# - inicializa banco de dados;
# - inicializa Scheduler;
# - inicializa monitoramento de Agents;
# - registra routers FastAPI.
#
# A implementação abaixo foi extraída do main.py preservando
# o comportamento atual do Control Room.
# ============================================================

import json
import logging
import os

from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from core.request_context import get_request_id
from core.log_sanitizer import sanitize_log_payload

# ============================================================
# FORMATTER JSON
# ============================================================

class JsonFormatter(logging.Formatter):
    """
    Formata os registros de log como JSON.

    Além dos campos técnicos padrão, o formatter também
    adiciona automaticamente campos extras enviados através
    do parâmetro "extra" das chamadas de logging.

    Exemplo:

        logger.info(
            "Execução iniciada",
            extra={
                "event": "execution_started",
                "execution_id": 10,
                "agent_id": "AGENT-001"
            }
        )
    """

    # Campos adicionais que poderão ser utilizados pelos
    # diferentes módulos do Control Room.
    EXTRA_FIELDS = (
        "execution_id",
        "robot_id",
        "robot_name",
        "robot_filename",
        "robot_version",
        "robot_folder",
        "robot_path",

        "agent_id",
        "agent_name",
        "agent_host",
        "agent_port",

        "user_id",
        "username",
        "user_name",

        "pid",

        "status",
        "status_before",
        "status_after",
        "reason",

        "duration_ms",
        "queue_position",

        "http_method",
        "endpoint",
        "request_id",
        "correlation_id",
        "http_status",
        # Auditoria e classificação do evento.
        "actor_user_id",
        "actor_username",

        "action",

        "resource_type",
        "resource_id",
        "resource_name",

        # Metadado específico de versionamento publicado.
        # Necessário para diagnosticar referências quebradas
        # entre Library e sua versão vigente em Produção.
        "production_version_id",

        "workspace_path",

        "client_ip",

        # Preparação para tracing distribuído.
        "trace_id",
        "span_id",
        "error_type",
        "error_message",
    )

    def format(self, record):
        """
        Converte um LogRecord do Python para um objeto JSON.
        """

        # Timestamp UTC no padrão ISO 8601.
        #
        # Exemplo:
        #
        # 2026-09-12T20:30:15.123Z
        timestamp = (
            datetime
            .fromtimestamp(
                record.created,
                tz=timezone.utc
            )
            .isoformat(
                timespec="milliseconds"
            )
            .replace(
                "+00:00",
                "Z"
            )
        )

        # Estrutura básica presente em todos os logs.
        log_data = {
            "timestamp": timestamp,
            "level": record.levelname,
            "service": "rpa-control-room",

            # Categoria funcional utilizada pela área
            # "Logs do sistema".
            #
            # Exemplos:
            # SYSTEM
            # AUDIT
            # SECURITY
            # INTEGRATION
            # EXECUTION
            # HTTP
            "category": str(
                getattr(
                    record,
                    "category",
                    "SYSTEM",
                )
            ).upper(),

            # Componente interno que originou o evento.
            #
            # Quando nenhum componente explícito é informado,
            # utilizamos o nome do módulo Python.
            "component": str(
                getattr(
                    record,
                    "component",
                    record.module,
                )
            ),

            # Alguns eventos são importantes para telemetria
            # externa, mas não devem poluir a interface de
            # Logs do sistema.
            "ui_visible": bool(
                getattr(
                    record,
                    "ui_visible",
                    True,
                )
            ),

            # Permite diferenciar development, homologation,
            # production etc. sem alterar o código.
            #
            # Caso APP_ENVIRONMENT não exista,
            # será utilizado "development".
            "environment": os.getenv(
                "APP_ENVIRONMENT",
                "development"
            ),

            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,

            "process_id": record.process,
            "thread_name": record.threadName,

            # Caso nenhum evento específico seja informado
            # pelo logger, utiliza um evento genérico.
            "event": getattr(
                record,
                "event",
                "application_log"
            ),

            "message": record.getMessage(),
        }

        active_request_id = get_request_id()
        if active_request_id and not hasattr(record, "request_id"):
            log_data["request_id"] = active_request_id

        # Adiciona apenas os campos extras que realmente
        # existirem naquele registro de log.
        #
        # Dessa forma não teremos dezenas de campos null
        # em todos os eventos.
        for field in self.EXTRA_FIELDS:

            if hasattr(record, field):

                log_data[field] = getattr(
                    record,
                    field
                )

        # Caso o log tenha sido gerado durante uma exceção,
        # adiciona os dados técnicos da exceção.
        if record.exc_info:

            exception_type = (
                record.exc_info[0].__name__
                if record.exc_info[0]
                else None
            )

            exception_message = (
                str(record.exc_info[1])
                if record.exc_info[1]
                else None
            )

            log_data["exception"] = {
                "type": exception_type,
                "message": exception_message,
                "traceback": self.formatException(
                    record.exc_info
                )
            }

        # Nenhuma informação é persistida antes de passar
        # pela sanitização central de segredos.
        log_data = sanitize_log_payload(
            log_data
        )
        # ensure_ascii=False mantém caracteres como:
        #
        # execução
        # robô
        # conexão
        #
        # sem convertê-los para códigos Unicode.
        return json.dumps(
            log_data,
            ensure_ascii=False,
            default=str
        )


# ============================================================
# DIRETÓRIO DOS LOGS
# ============================================================

LOG_DIRECTORY = Path("logs")

LOG_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# Arquivo principal de logs técnicos do Control Room.
LOG_FILE = (
    LOG_DIRECTORY
    / "control_room.log"
)


# ============================================================
# FORMATTER JSON
# ============================================================

json_formatter = JsonFormatter()


# ============================================================
# HANDLER DO ARQUIVO
# ============================================================
#
# Cria um novo arquivo de log diariamente.
#
# backupCount=30 mantém aproximadamente
# os últimos 30 arquivos.
# ============================================================

file_handler = TimedRotatingFileHandler(
    filename=LOG_FILE,
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8",
    utc=True
)

file_handler.setFormatter(
    json_formatter
)

# ============================================================
# LOGGER PRINCIPAL DO CONTROL ROOM
# ============================================================
#
# O logger do DUET possui seu próprio handler em vez de
# depender do root logger do Python.
#
# Isso é importante porque bibliotecas e ferramentas externas,
# como Alembic e Uvicorn, podem reconfigurar o root logger
# durante o ciclo de vida da aplicação.
#
# Dessa forma:
#
# - logs do DUET continuam indo para control_room.log;
# - Alembic pode configurar seu próprio logging;
# - Uvicorn pode configurar seu próprio logging;
# - nenhuma dessas configurações remove o handler do DUET;
# - evita duplicação através do root logger.
# ============================================================

logger = logging.getLogger(
    "control_room"
)

logger.setLevel(
    logging.INFO
)

# O próprio logger "control_room" é responsável pela
# persistência no arquivo estruturado.
file_handler.setLevel(
    logging.INFO
)

logger.addHandler(
    file_handler
)

# Impede que o mesmo registro seja propagado novamente
# para o root logger e apareça duplicado no console ou
# em outro handler configurado por terceiros.
logger.propagate = False