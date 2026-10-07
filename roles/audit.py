# ============================================================
# AUDITORIA - ROLES
# ============================================================
#
# Responsabilidade:
#     Centralizar os eventos estruturados de auditoria
#     relacionados ao domínio de Roles.
#
# Este módulo NÃO altera banco de dados e NÃO aplica regras
# de autorização. Ele apenas registra eventos já concluídos.
# ============================================================

from models import User
from core.event_logger import log_event


# ============================================================
# ALTERAÇÃO DE PERMISSÕES DA ROLE
# ============================================================

def registrar_alteracao_permissoes_role(
    *,
    usuario_executor: User,
    role_id: int,
    role_name: str,
    permissoes_antes: list[str],
    permissoes_depois: list[str],
) -> None:
    """
    Registra a substituição das permissões de uma Role.

    As permissões são registradas somente por seus identificadores
    funcionais, no formato:

        Resource:action

    Exemplo:

        Users:view
        Users:edit
        Roles:view
    """

    status_before = (
        ", ".join(permissoes_antes)
        if permissoes_antes
        else "(sem permissões)"
    )

    status_after = (
        ", ".join(permissoes_depois)
        if permissoes_depois
        else "(sem permissões)"
    )

    log_event(
        "Permissões da Role alteradas",
        event="role.permissions.changed",
        category="AUDIT",
        component="roles",
        status="success",

        # Usuário autenticado que executou a alteração.
        actor_user_id=usuario_executor.id,
        actor_username=usuario_executor.username,

        action="permissions_replace",

        # Role que sofreu a alteração.
        resource_type="role",
        resource_id=role_id,
        resource_name=role_name,

        # Snapshot funcional antes/depois.
        status_before=status_before,
        status_after=status_after,

        ui_visible=True,
    )