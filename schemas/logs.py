from typing import Literal

from pydantic import BaseModel, Field


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SystemLogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    event: str | None = None
    request_id: str | None = None
    service: str | None = None
    category: str | None = None
    component: str | None = None
    status: str | None = None

    actor_user_id: int | None = None
    actor_username: str | None = None

    action: str | None = None

    resource_type: str | None = None
    resource_id: str | int | None = None
    resource_name: str | None = None

    client_ip: str | None = None

    http_method: str | None = None
    endpoint: str | None = None
    http_status: int | None = None
    duration_ms: float | None = None

    error_type: str | None = None
    error_message: str | None = None

    trace_id: str | None = None
    span_id: str | None = None


class LogsSuccessResponse(BaseModel):
    status: Literal["success"]
    logs: list[SystemLogEntry]
    total: int = Field(..., ge=0)
    truncated: bool


class LogsErrorResponse(BaseModel):
    status: Literal["error"]
    message: str


LogsResponse = LogsSuccessResponse | LogsErrorResponse
