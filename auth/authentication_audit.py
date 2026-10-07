# ============================================================
# AUDITORIA - AUTENTICAÇÃO
# ============================================================
#
# Responsabilidade:
#     Centralizar os eventos estruturados relacionados
#     à segurança do processo de autenticação.
#
# Este módulo NÃO:
#     - valida senha;
#     - cria sessão;
#     - controla rate limit;
#     - autentica usuário.
#
# Senhas, hashes, tokens e session_id nunca são registrados.
# ============================================================

import logging

from core.event_logger import log_event


# ============================================================
# LOGIN RECUSADO
# ============================================================

def registrar_login_falho(
    *,
    username: str,
    user_id: int | None = None,
) -> None:
    """
    Registra uma tentativa de login que falhou na autenticação.

    O mesmo evento é utilizado tanto para username inexistente
    quanto para senha incorreta, evitando expor detalhes
    desnecessários sobre a credencial.
    """

    log_event(
        "Falha de autenticação no login",
        event="auth.login.failed",
        category="SECURITY",
        component="auth",
        status="failed",

        action="login",

        resource_type="user",
        resource_id=user_id,
        resource_name=username,

        ui_visible=True,
        level=logging.WARNING,
    )


# ============================================================
# CONTA INATIVA
# ============================================================

def registrar_login_conta_inativa(
    *,
    user_id: int,
    username: str,
) -> None:
    """
    Registra tentativa de login utilizando uma conta inativa.

    O usuário ainda não está autenticado, portanto ele não é
    registrado como actor do evento.
    """

    log_event(
        "Login bloqueado para conta inativa",
        event="auth.account.inactive",
        category="SECURITY",
        component="auth",
        status="failed",

        action="login",

        resource_type="user",
        resource_id=user_id,
        resource_name=username,

        ui_visible=True,
        level=logging.WARNING,
    )