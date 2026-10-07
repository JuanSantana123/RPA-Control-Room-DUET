# ============================================================
# DUET - USER ROLES AUDIT
# ============================================================
#
# Responsabilidade:
#     Centralizar os eventos de auditoria relacionados às
#     alterações de Roles associadas aos usuários.
#
# Este módulo NÃO:
#     - altera Roles;
#     - executa commit;
#     - aplica regras RBAC;
#     - acessa diretamente o banco.
#
# Ele apenas traduz uma alteração já concluída pelo domínio
# User Roles para o contrato estruturado de observabilidade.
# ============================================================

from __future__ import annotations

from models import User

from core.event_logger import log_event


def registrar_alteracao_roles_usuario(
    *,
    usuario_executor: User,
    usuario_alvo: User,
    action: str,
    message: str,
) -> None:
    """
    Registra uma alteração efetiva nas Roles de um usuário.

    O evento é emitido somente depois que a alteração já foi
    persistida com sucesso pelo service responsável.

    Parâmetros
    ----------
    usuario_executor:
        Usuário autenticado que realizou a alteração.

    usuario_alvo:
        Usuário cujas Roles foram alteradas.

    action:
        Tipo técnico da alteração.

        Exemplos:
            role_add
            role_remove
            roles_replace

    message:
        Descrição legível da alteração.
    """

    log_event(
        message,
        event="user.roles.changed",
        category="AUDIT",
        component="user_roles",
        status="success",

        actor_user_id=usuario_executor.id,
        actor_username=usuario_executor.username,

        action=action,

        resource_type="user",
        resource_id=usuario_alvo.id,
        resource_name=usuario_alvo.username,

        ui_visible=True,
    )