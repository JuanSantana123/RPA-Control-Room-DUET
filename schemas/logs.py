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


class LogsSuccessResponse(BaseModel):
    status: Literal["success"]
    logs: list[SystemLogEntry]
    total: int = Field(..., ge=0)
    truncated: bool


class LogsErrorResponse(BaseModel):
    status: Literal["error"]
    message: str


LogsResponse = LogsSuccessResponse | LogsErrorResponse
