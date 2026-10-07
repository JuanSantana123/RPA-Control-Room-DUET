# ============================================================
# OBSERVABILIDADE - VAULT
# ============================================================
#
# Responsabilidade:
#     Centralizar eventos técnicos importantes relacionados
#     ao funcionamento do Vault.
#
# Este módulo NÃO:
#     - criptografa ou descriptografa dados;
#     - acessa banco de dados;
#     - conhece valores secretos;
#     - registra password, ciphertext ou Master Key;
#     - altera fluxo de execução.
#
# IMPORTANTE:
#
# Falhas criptográficas exigem tratamento diferente de erros
# comuns do sistema.
#
# Não utilizamos logger.exception() aqui porque uma exceção
# proveniente de uma biblioteca criptográfica pode, em algum
# cenário futuro, carregar material sensível em sua mensagem.
#
# Registramos:
#     - tipo técnico da exceção;
#     - contexto da credencial;
#     - execução/Agent quando disponíveis;
#
# sem registrar o conteúdo do erro original.
# ============================================================

import logging


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# FALHA DE DESCRIPTOGRAFIA
# ============================================================

def registrar_falha_descriptografia_vault(
    *,
    error: Exception,
    credential_id: int,
    credential_name: str,
    resource_type: str,
    execution_id: int | None = None,
    agent_id: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
) -> None:
    """
    Registra uma falha ao abrir um segredo armazenado no Vault.

    Segurança
    ---------
    Esta função nunca recebe:

        password
        ciphertext
        Master Key

    error_message é propositalmente genérico.

    O objeto ``error`` é utilizado SOMENTE para identificar
    sua classe técnica através de type(error).__name__.
    """

    extra = {
        "event": "vault.decryption.failed",
        "category": "SYSTEM",
        "component": "vault",
        "ui_visible": True,

        "status": "failed",
        "action": "decrypt_secret",
        "reason": "decryption_failed",

        # Credencial afetada.
        "resource_type": resource_type,
        "resource_id": credential_id,
        "resource_name": credential_name,

        # Somente a classe técnica da exceção.
        #
        # NÃO utilizar str(error) aqui.
        "error_type": type(error).__name__,
        "error_message": (
            "Falha criptográfica ao descriptografar "
            "segredo do Vault."
        ),
    }

    # Contexto de execução existe apenas em alguns fluxos.
    if execution_id is not None:
        extra["execution_id"] = execution_id

    if agent_id is not None:
        extra["agent_id"] = agent_id

    if user_id is not None:
        extra["user_id"] = user_id

    if username is not None:
        extra["username"] = username

    logger.error(
        "Falha ao descriptografar segredo do Vault",
        extra=extra,
    )


# ============================================================
# AUDITORIA - CICLO DE VIDA DE CREDENCIAIS
# ============================================================

def registrar_evento_credencial_vault(
    *,
    event: str,
    action: str,
    message: str,
    credential_id: int,
    credential_name: str,
    usuario,
    resource_type: str = "vault_credential",
) -> None:
    """
    Registra alterações administrativas em credenciais do Vault.

    Segurança
    ---------
    Este evento registra somente:

    - quem realizou a ação;
    - qual credencial foi afetada;
    - qual operação foi executada.

    Nunca recebe ou registra:

    - valores de VaultField;
    - password;
    - tokens;
    - ciphertext;
    - Master Key.
    """

    logger.info(
        message,
        extra={
            "event": event,
            "category": "AUDIT",
            "component": "vault",
            "ui_visible": True,
            "status": "success",

            "actor_user_id": getattr(
                usuario,
                "id",
                None,
            ),
            "actor_username": getattr(
                usuario,
                "username",
                None,
            ),

            "action": action,

            "resource_type": resource_type,
            "resource_id": credential_id,
            "resource_name": credential_name,
        },
    )