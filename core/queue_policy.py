import os
from datetime import datetime


DEFAULT_QUEUE_WARNING_SECONDS = 900
MIN_QUEUE_WARNING_SECONDS = 60
MAX_QUEUE_WARNING_SECONDS = 86400
PRIORITY_RANK = {
    "urgent": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
}


def queue_sort_key(
    priority: str,
    queued_at: datetime | None,
    execution_id: int,
) -> tuple[int, datetime, int]:
    """Build the deterministic priority/FIFO ordering used by the queue."""

    return (
        PRIORITY_RANK.get(priority, PRIORITY_RANK["normal"]),
        queued_at or datetime.max,
        execution_id,
    )


def get_queue_warning_seconds() -> int:
    """Return the operational wait threshold without accepting unsafe values."""

    raw_value = os.getenv("DUET_QUEUE_WARNING_SECONDS", "").strip()
    if not raw_value:
        return DEFAULT_QUEUE_WARNING_SECONDS

    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_QUEUE_WARNING_SECONDS

    if value < MIN_QUEUE_WARNING_SECONDS or value > MAX_QUEUE_WARNING_SECONDS:
        return DEFAULT_QUEUE_WARNING_SECONDS

    return value
