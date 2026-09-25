# ============================================================
# SERVICE - BOOTSTRAP DE AGENTS
# ============================================================
#
# Centraliza a montagem da configuração necessária para
# instalar/configurar um Agent.
#
# ATENÇÃO:
# O bootstrap contém agent_token e portanto é informação
# sensível.
# ============================================================

import json
import os

from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from agents.repository import buscar_agent_por_id
# Recupera o token original somente quando o bootstrap
# precisa entregá-lo ao Agent.
from agents.token_security import descriptografar_agent_token

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CONFIG_PATH = os.path.join(
    BASE_DIR,
    "config.json",
)


with open(
    CONFIG_PATH,
    "r",
    encoding="utf-8",
) as arquivo:
    CONFIG = json.load(arquivo)


# ============================================================
# URL DO CONTROL ROOM ENTREGUE AOS AGENTS
# ============================================================
#
# A URL é definida no config.json do Control Room.
#
# Isso permite que a mesma aplicação trabalhe com:
#
#     http://control-room:9000
#
# ou, futuramente:
#
#     https://control-room.empresa.local
#
# O protocolo não é forçado pelo código. Dessa forma,
# habilitar HTTPS futuramente será uma alteração de
# configuração, e não uma alteração no Agent/installer.
#
# A validação abaixo impede protocolos inesperados como
# file://, ftp:// etc.
# ============================================================

CONTROL_ROOM_URL = str(
    CONFIG["control_room_url"]
).strip().rstrip("/")


if not CONTROL_ROOM_URL.lower().startswith(
    (
        "http://",
        "https://",
    )
):
    raise RuntimeError(
        "control_room_url deve utilizar http:// ou https://."
    )

def _montar_bootstrap(agent):
    """
    Monta a configuração técnica entregue ao Agent.

    O token não é mais lido de uma coluna plaintext.
    Ele é recuperado do ciphertext somente em memória.
    """

    agent_token = descriptografar_agent_token(
        agent.agent_token_encrypted
    )

    return {
        "agent_id": agent.agent_id,
        "agent_token": agent_token,
        "control_room_url": CONTROL_ROOM_URL,
        "port": agent.port,
        "rpa_directory": agent.rpa_directory,

        # Identidade Windows configurada no Control Room
        # para execução de automações Desktop.
        #
        # A senha NÃO faz parte do bootstrap.
        # Somente usuário e domínio são distribuídos ao Agent.
        "execution_username": agent.execution_username,
        "execution_domain": agent.execution_domain,
    }


def obter_installation_config_service(
    agent_id: str,
    db: Session,
):
    """
    Retorna o bootstrap como resposta JSON convencional.
    """

    agent = buscar_agent_por_id(
        db,
        agent_id,
    )

    if not agent:
        return {
            "status": "error",
            "message": "Agent não encontrado.",
        }

    # --------------------------------------------------------
    # BLOQUEIA BOOTSTRAP DE AGENT DESATIVADO
    # --------------------------------------------------------
    #
    # O bootstrap contém agent_token. Portanto, um Agent
    # removido logicamente não pode continuar tendo seu
    # material de autenticação disponibilizado.
    # --------------------------------------------------------

    if agent.is_active != 1:
        return {
            "status": "error",
            "message": "Agent não está ativo.",
        }

    return {
        "status": "success",
        "bootstrap": _montar_bootstrap(agent),
    }


def download_agent_bootstrap_service(
    agent_id: str,
    db: Session,
):
    """
    Retorna o bootstrap como arquivo JSON para download.
    """

    agent = buscar_agent_por_id(
        db,
        agent_id,
    )

    if not agent:
        return {
            "status": "error",
            "message": "Agent não encontrado.",
        }

    # --------------------------------------------------------
    # BLOQUEIA DOWNLOAD DE BOOTSTRAP DE AGENT DESATIVADO
    # --------------------------------------------------------
    #
    # O arquivo contém agent_token e não deve ser gerado para
    # um Agent que já foi removido logicamente.
    # --------------------------------------------------------

    if agent.is_active != 1:
        return {
            "status": "error",
            "message": "Agent não está ativo.",
        }

    bootstrap = _montar_bootstrap(agent)

    response = JSONResponse(
        content=bootstrap
    )

    response.headers[
        "Content-Disposition"
    ] = (
        f'attachment; filename="bootstrap_{agent.agent_id}.json"'
    )

    return response