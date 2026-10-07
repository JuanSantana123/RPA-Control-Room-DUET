# ============================================================
# DUET CORE - LOG SANITIZER
# ============================================================
#
# Responsabilidade:
#     Remover informações sensíveis antes que um evento seja
#     persistido nos arquivos de log do Control Room.
#
# IMPORTANTE:
#     A sanitização ocorre ANTES da gravação física.
#
#     Dessa forma, futuros coletores como Datadog,
#     OpenTelemetry Collector, Splunk ou Elastic nunca recebem
#     o segredo original através dos arquivos do DUET.
# ============================================================

from __future__ import annotations

import re
from typing import Any


REDACTED_VALUE = "***REDACTED***"


# ============================================================
# NOMES DE CAMPOS SENSÍVEIS
# ============================================================

_SENSITIVE_KEYS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "client_secret",
    "authorization",
    "cookie",
    "set_cookie",
    "session_id",
    "agent_token",
    "master_key",
    "private_key",
)


# ============================================================
# PADRÕES SENSÍVEIS EMBUTIDOS EM TEXTO
# ============================================================

_BEARER_PATTERN = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]+=*"
)

_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    \b(
        password|
        passwd|
        pwd|
        secret|
        token|
        access_token|
        refresh_token|
        api_key|
        api-key|
        client_secret|
        client-secret|
        authorization|
        session_id
    )
    (\s*[:=]\s*)
    ([^\s,;]+)
    """
)


def _normalize_key(key: object) -> str:
    """Normaliza o nome de um campo para comparação segura."""

    return (
        str(key)
        .strip()
        .lower()
        .replace("-", "_")
    )


def _is_sensitive_key(key: object) -> bool:
    """Indica se o nome do campo representa informação sensível."""

    normalized = _normalize_key(key)

    return any(
        sensitive in normalized
        for sensitive in _SENSITIVE_KEYS
    )


def _sanitize_text(value: str) -> str:
    """Remove segredos eventualmente embutidos em mensagens."""

    sanitized = _BEARER_PATTERN.sub(
        "Bearer ***REDACTED***",
        value,
    )

    sanitized = _ASSIGNMENT_PATTERN.sub(
        lambda match: (
            f"{match.group(1)}"
            f"{match.group(2)}"
            f"{REDACTED_VALUE}"
        ),
        sanitized,
    )

    return sanitized


def sanitize_log_value(
    value: Any,
    *,
    field_name: object | None = None,
) -> Any:
    """
    Sanitiza recursivamente um valor utilizado em logging.

    Campos reconhecidos como secretos são completamente
    substituídos. Strings também passam por sanitização de
    padrões como Bearer Tokens e password=...
    """

    if field_name is not None and _is_sensitive_key(field_name):
        return REDACTED_VALUE

    if isinstance(value, str):
        return _sanitize_text(value)

    if isinstance(value, dict):
        return {
            str(key): sanitize_log_value(
                nested_value,
                field_name=key,
            )
            for key, nested_value in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            sanitize_log_value(item)
            for item in value
        ]

    if value is None or isinstance(
        value,
        (bool, int, float),
    ):
        return value

    # Objetos não serializáveis são transformados em texto,
    # mas ainda passam pelo redator antes da persistência.
    return _sanitize_text(str(value))


def sanitize_log_payload(payload: dict) -> dict:
    """Sanitiza o payload completo de um evento de log."""

    return {
        str(key): sanitize_log_value(
            value,
            field_name=key,
        )
        for key, value in payload.items()
    }