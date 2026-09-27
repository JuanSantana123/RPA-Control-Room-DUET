import os
from datetime import datetime
from typing import Literal

from core.timezone import local_now_naive


DEFAULT_AGENT_HEARTBEAT_TIMEOUT_SECONDS = 60
MIN_AGENT_HEARTBEAT_TIMEOUT_SECONDS = 15
MAX_AGENT_HEARTBEAT_TIMEOUT_SECONDS = 3600

AgentHealthState = Literal["healthy", "stale", "offline", "never_seen"]


def get_agent_heartbeat_timeout_seconds() -> int:
    raw_value = os.getenv(
        "DUET_AGENT_HEARTBEAT_TIMEOUT_SECONDS",
        str(DEFAULT_AGENT_HEARTBEAT_TIMEOUT_SECONDS),
    )
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_AGENT_HEARTBEAT_TIMEOUT_SECONDS

    if not MIN_AGENT_HEARTBEAT_TIMEOUT_SECONDS <= value <= MAX_AGENT_HEARTBEAT_TIMEOUT_SECONDS:
        return DEFAULT_AGENT_HEARTBEAT_TIMEOUT_SECONDS
    return value


def describe_agent_health(
    status: str,
    last_heartbeat: datetime | None,
    *,
    now: datetime | None = None,
    timeout_seconds: int | None = None,
) -> tuple[AgentHealthState, int | None]:
    """Deriva saúde e idade sem misturar conectividade com manutenção."""

    if last_heartbeat is None:
        return "never_seen", None

    reference = now or local_now_naive()
    heartbeat_age_seconds = max(
        0,
        int((reference - last_heartbeat).total_seconds()),
    )

    if status.lower() != "online":
        return "offline", heartbeat_age_seconds

    effective_timeout = timeout_seconds or get_agent_heartbeat_timeout_seconds()
    if heartbeat_age_seconds > effective_timeout:
        return "stale", heartbeat_age_seconds

    return "healthy", heartbeat_age_seconds
