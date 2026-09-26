import os


def background_workers_habilitados():
    """Indica se esta instância é responsável pelos loops operacionais."""

    value = os.getenv("CONTROL_ROOM_ENABLE_BACKGROUND_WORKERS", "true")
    return value.strip().lower() in {"1", "true", "yes", "on"}
