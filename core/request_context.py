from contextvars import ContextVar
import re
import uuid


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def normalize_request_id(candidate: str | None) -> str:
    if candidate and REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


def get_request_id() -> str | None:
    return request_id_context.get()
