from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from agents.monitoring_service import monitor_agents_esta_ativo
from agents.token_security import configuracao_agent_token_disponivel
from core.logging_config import logger
from core.runtime_config import background_workers_habilitados
from database import engine
from executions.queue import worker_fila_esta_ativo
from scheduler.engine import scheduler_esta_ativo


router = APIRouter(tags=["Health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["rpa-control-room"]


class ReadinessChecks(BaseModel):
    database: Literal["ready", "unavailable"]
    schema_revision: str | None
    background_workers: Literal["running", "disabled", "degraded"]
    agent_token_protection: Literal["ready", "unavailable"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    service: Literal["rpa-control-room"]
    checks: ReadinessChecks


@router.get("/health/live", response_model=LivenessResponse)
def health_live():
    """Confirma que o processo HTTP está respondendo."""

    return LivenessResponse(status="ok", service="rpa-control-room")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
)
def health_ready():
    """Valida banco, revisão de schema e loops exigidos por esta instância."""

    database_status = "ready"
    schema_revision = None

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            schema_revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    except Exception as error:
        database_status = "unavailable"
        logger.warning(
            "Readiness detectou indisponibilidade do banco",
            extra={
                "event": "readiness_database_unavailable",
                "status": "not_ready",
                "error_type": type(error).__name__,
            },
        )

    if not background_workers_habilitados():
        workers_status = "disabled"
    elif all((
        scheduler_esta_ativo(),
        worker_fila_esta_ativo(),
        monitor_agents_esta_ativo(),
    )):
        workers_status = "running"
    else:
        workers_status = "degraded"

    agent_token_protection_status = (
        "ready" if configuracao_agent_token_disponivel() else "unavailable"
    )

    ready = (
        database_status == "ready"
        and schema_revision is not None
        and workers_status != "degraded"
        and agent_token_protection_status == "ready"
    )
    payload = ReadinessResponse(
        status="ready" if ready else "not_ready",
        service="rpa-control-room",
        checks=ReadinessChecks(
            database=database_status,
            schema_revision=schema_revision,
            background_workers=workers_status,
            agent_token_protection=agent_token_protection_status,
        ),
    )

    if not ready:
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload
