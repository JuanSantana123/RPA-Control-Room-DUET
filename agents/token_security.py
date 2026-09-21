# ============================================================
# SEGURANÇA DOS TOKENS DOS AGENTS
# ============================================================
#
# Centraliza toda a proteção aplicada ao agent_token.
#
# O token possui duas representações:
#
# 1. HASH SHA-256
#    Utilizado exclusivamente para localizar/autenticar o Agent.
#
#    Não é reversível.
#
# 2. TOKEN CRIPTOGRAFADO
#    Utilizado quando o Control Room precisa recuperar o token
#    original para bootstrap, installer ou comunicação com Agent.
#
# IMPORTANTE:
# O token em texto puro nunca deve ser persistido por este módulo.
# ============================================================

import hashlib
import os

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)


# ============================================================
# VARIÁVEL DE AMBIENTE
# ============================================================
#
# Esta chave NÃO deve ficar:
#
# - no código;
# - no banco;
# - no Git;
# - no config.json.
#
# Ela deve existir somente no ambiente do Control Room.
# ============================================================

AGENT_TOKEN_KEY_ENV = "DUET_AGENT_TOKEN_KEY"


class AgentTokenSecurityError(Exception):
    """
    Erro controlado relacionado à proteção do agent_token.
    """


def gerar_chave_agent_token() -> str:
    """
    Gera uma nova chave Fernet.

    Esta função é destinada somente à configuração inicial.

    A chave retornada deve ser armazenada de forma segura
    fora do banco de dados.
    """

    return Fernet.generate_key().decode("ascii")


def _obter_fernet() -> Fernet:
    """
    Carrega a chave de criptografia do ambiente.

    O processo falha explicitamente quando a chave não existe
    ou possui formato inválido.

    Não criamos uma chave automaticamente porque isso poderia
    tornar tokens existentes permanentemente irrecuperáveis após
    reinicialização do Control Room.
    """

    chave = os.getenv(
        AGENT_TOKEN_KEY_ENV
    )

    if not chave:
        raise AgentTokenSecurityError(
            "Chave de proteção dos tokens dos Agents "
            "não configurada."
        )

    try:
        return Fernet(
            chave.encode("ascii")
        )

    except Exception as error:
        raise AgentTokenSecurityError(
            "Chave de proteção dos tokens dos Agents "
            "possui formato inválido."
        ) from error


def calcular_hash_agent_token(
    agent_token: str,
) -> str:
    """
    Calcula o SHA-256 do token.

    O hash é utilizado para localizar rapidamente o Agent
    durante autenticação machine-to-machine.

    Como o agent_token possui alta entropia gerada por
    secrets.token_urlsafe(32), SHA-256 é adequado para
    indexação/verificação dessa credencial aleatória.
    """

    if not isinstance(agent_token, str):
        raise AgentTokenSecurityError(
            "agent_token inválido."
        )

    token_normalizado = agent_token.strip()

    if not token_normalizado:
        raise AgentTokenSecurityError(
            "agent_token vazio."
        )

    return hashlib.sha256(
        token_normalizado.encode("utf-8")
    ).hexdigest()


def criptografar_agent_token(
    agent_token: str,
) -> str:
    """
    Criptografa o token utilizando Fernet.

    Fernet fornece confidencialidade e autenticação do
    ciphertext, permitindo detectar adulteração.
    """

    if not isinstance(agent_token, str):
        raise AgentTokenSecurityError(
            "agent_token inválido."
        )

    token_normalizado = agent_token.strip()

    if not token_normalizado:
        raise AgentTokenSecurityError(
            "agent_token vazio."
        )

    fernet = _obter_fernet()

    return fernet.encrypt(
        token_normalizado.encode("utf-8")
    ).decode("ascii")


def descriptografar_agent_token(
    agent_token_encrypted: str,
) -> str:
    """
    Recupera o token original armazenado criptografado.

    Nunca registra o token em log.
    """

    if (
        not isinstance(
            agent_token_encrypted,
            str,
        )
        or not agent_token_encrypted
    ):
        raise AgentTokenSecurityError(
            "Token criptografado do Agent inválido."
        )

    fernet = _obter_fernet()

    try:
        token = fernet.decrypt(
            agent_token_encrypted.encode("ascii")
        )

    except InvalidToken as error:
        raise AgentTokenSecurityError(
            "Não foi possível descriptografar "
            "o token do Agent."
        ) from error

    return token.decode("utf-8")


def proteger_agent_token(
    agent_token: str,
) -> tuple[str, str]:
    """
    Produz as duas representações persistidas do token.

    Retorno:
        (
            agent_token_hash,
            agent_token_encrypted,
        )
    """

    return (
        calcular_hash_agent_token(
            agent_token
        ),
        criptografar_agent_token(
            agent_token
        ),
    )