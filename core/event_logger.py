# ============================================================
# DUET CORE - EVENT LOGGER
# ============================================================
#
# Responsabilidade:
#     Padronizar a emissão de eventos estruturados do DUET.
#
# Este módulo concentra o contrato utilizado por eventos de:
#
#     SYSTEM
#     AUDIT
#     SECURITY
#     INTEGRATION
#
# Dessa forma, os services não precisam montar manualmente
# estruturas diferentes de "extra" em cada operação.
#
# IMPORTANTE:
#     A sanitização de segredos continua sendo responsabilidade
#     de core.logging_config / core.log_sanitizer antes da
#     persistência física do registro.
# ============================================================

from __future__ import annotations

import logging


logger = logging.getLogger(
    "control_room"
)


def log_event(
    message: str,
    *,
    event: str,
    category: str,
    component: str,
    status: str | None = None,
    actor_user_id: int | None = None,
    actor_username: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    resource_name: str | None = None,
    client_ip: str | None = None,
    status_before: str | None = None,
    status_after: str | None = None,
    ui_visible: bool = True,
    level: int = logging.INFO,
) -> None:
    """
    Emite um evento estruturado utilizando o logger central
    do Control Room.

    Parâmetros
    ----------
    message:
        Mensagem legível por uma pessoa.

    event:
        Identificador técnico estável do evento.

        Exemplos:
            user.disabled
            user.enabled
            auth.login.failed

    category:
        Categoria funcional do evento.

        Exemplos:
            SYSTEM
            AUDIT
            SECURITY
            INTEGRATION

    component:
        Componente funcional responsável pelo evento.

        Exemplos:
            users
            auth
            roles
            vault

    actor_user_id / actor_username:
        Usuário responsável pela ação.

    resource_*:
        Recurso afetado pela ação.

    status_before / status_after:
        Estado anterior e posterior quando aplicável.

    ui_visible:
        Define se o evento deve aparecer em
        "Logs do sistema".

    level:
        Nível padrão do módulo logging.
    """

    extra = {
        "event": event,
        "category": category.upper(),
        "component": component,
        "ui_visible": ui_visible,
        "status": status,

        "actor_user_id": actor_user_id,
        "actor_username": actor_username,

        "action": action,

        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": resource_name,

        # IP de origem quando o evento estiver relacionado
        # a autenticação ou comunicação remota.
        "client_ip": client_ip,
        "status_before": status_before,
        "status_after": status_after,
    }

    # Evita inserir propriedades sem informação no LogRecord.
    extra = {
        key: value
        for key, value in extra.items()
        if value is not None
    }

    logger.log(
        level,
        message,
        extra=extra,
    )