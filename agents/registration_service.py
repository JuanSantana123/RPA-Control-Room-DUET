# ============================================================
# SERVICE - REGISTRO DE AGENTS
# ============================================================
#
# Responsável pelo processo de registro de um Agent existente.
#
# Fluxo preservado:
#
# 1. Localiza o Agent previamente criado no Control Room.
# 2. Obtém o agent_token já existente.
# 3. Consulta /health.
# 4. Valida se o Agent está online.
# 5. Valida o agent_id retornado.
# 6. Consulta /config.
# 7. Valida a configuração.
# 8. Ativa o Agent através de /config/status.
# 9. Atualiza o cadastro no banco.
#
# IMPORTANTE:
# Nenhum novo token é criado durante o registro.
# ============================================================

import logging

import requests
from sqlalchemy.orm import Session

from agents.repository import (
    atualizar_agent_registrado,
    buscar_agent_por_id,
)

# Validação centralizada do destino de rede do Agent.
#
# Impede que host/porta controlados pelo request sejam usados
# diretamente em chamadas HTTP sem validação prévia.
from agents.network_security import (
    AGENT_REQUEST_TIMEOUT,
    AgentNetworkSecurityError,
    validar_destino_agent,
)
# Recupera a credencial original somente durante
# as chamadas Control Room -> Agent.
from agents.token_security import descriptografar_agent_token

from schemas.agents import AgentRegisterRequest


logger = logging.getLogger("control_room")


def registrar_agent_service(
    request: AgentRegisterRequest,
    db: Session,
):
    """
    Registra e valida um Agent previamente criado.

    Parâmetros:
        request:
            Dados de conexão informados para o Agent.

        db:
            Sessão SQLAlchemy controlada pelo endpoint.

    Retorno:
        Mantém o contrato utilizado atualmente por
        POST /agents/register.
    """

    # ========================================================
    # IDENTIFICAÇÃO DO AGENT
    # ========================================================

    agent_id = request.agent_id
    host = request.host
    port = request.port

    # ========================================================
    # VALIDA DESTINO DE REDE
    # ========================================================
    #
    # host e port vêm da requisição HTTP e, portanto, não podem
    # ser utilizados diretamente em requests.get/put.
    #
    # A validação ocorre ANTES de qualquer conexão de rede.
    # ========================================================

    try:

        destino = validar_destino_agent(
            host,
            port,
        )

    except AgentNetworkSecurityError as error:

        logger.warning(
            "Destino de rede recusado durante registro do Agent",
            extra={
                "event": "agent_registration_target_rejected",
                "agent_id": agent_id,
                "agent_host": str(host),
                "agent_port": str(port),
                "reason": str(error),
            },
        )

        return {
            "status": "error",
            "message": "Destino de rede do Agent inválido.",
            "agent_id": agent_id,
        }

    # A partir deste ponto usamos somente os valores que
    # passaram pela validação.
    host = destino.host
    port = destino.port
    base_url = destino.base_url

    # ========================================================
    # BUSCA O AGENT NO CONTROL ROOM
    # ========================================================

    agent_existente = buscar_agent_por_id(
        db,
        agent_id,
    )

    if not agent_existente:

        logger.warning(
            "Tentativa de registrar Agent inexistente no Control Room",
            extra={
                "event": "agent_registration_not_found",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": "Agent não encontrado no Control Room.",
            "agent_id": agent_id,
        }


    # ========================================================
    # AGENT DESATIVADO NÃO PODE SER REGISTRADO NOVAMENTE
    # ========================================================
    #
    # buscar_agent_por_id() também é utilizado por fluxos
    # administrativos e, por isso, não filtra is_active.
    #
    # Neste fluxo específico, entretanto, reativar um Agent
    # removido logicamente permitiria reutilizar sua credencial.
    # ========================================================

    if agent_existente.is_active != 1:

        logger.warning(
            "Tentativa de registrar Agent desativado",
            extra={
                "event": "agent_registration_inactive",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": "Agent não está ativo.",
            "agent_id": agent_id,
        }
    # ========================================================
    # TOKEN DO AGENT
    # ========================================================
    #
    # O token foi criado anteriormente pelo Control Room.
    # Não deve ser regenerado durante o registro.
    # ========================================================

    # O banco não fornece mais o token em plaintext.
    # A credencial é recuperada somente para esta operação.
    agent_token = descriptografar_agent_token(
        agent_existente.agent_token_encrypted
    )

    # ========================================================
    # 1. CONSULTA HEALTH DO AGENT
    # ========================================================

    health_url = f"{base_url}/health"

    try:

        response = requests.get(
            health_url,
            headers={
                "Authorization": f"Bearer {agent_token}",
            },
            # Redirect automático é proibido. O destino
            # validado não pode redirecionar o Control Room
            # para outro host não validado.
            allow_redirects=False,

            # Timeout separado para conexão e leitura.
            timeout=AGENT_REQUEST_TIMEOUT,
        )

    except requests.RequestException as error:

        logger.error(
            "Não foi possível consultar o health do Agent durante o registro",
            extra={
                "event": "agent_registration_health_request_failed",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        # Detalhes da exceção permanecem somente nos logs.
        return {
            "status": "error",
            "message": "Não foi possível conectar ao Agent",
            "host": host,
            "port": port,
        }

    # ========================================================
    # 2. VALIDA HTTP DO HEALTH
    # ========================================================

    if response.status_code != 200:

        logger.error(
            "Agent respondeu com erro HTTP durante validação de health",
            extra={
                "event": "agent_registration_health_http_error",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
                "http_status": response.status_code,
            },
        )

        return {
            "status": "error",
            "message": "Agent respondeu com erro no /health",
            "host": host,
            "port": port,
            "http_status": response.status_code,
        }

    # ========================================================
    # 3. LÊ HEALTH
    # ========================================================

    try:

        health = response.json()

    except ValueError:

        logger.error(
            "Agent retornou JSON inválido no health durante registro",
            extra={
                "event": "agent_registration_health_invalid_json",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no /health",
        }

    # ========================================================
    # 4. VALIDA STATUS DO AGENT
    # ========================================================

    if health.get("status") != "online":

        logger.warning(
            "Agent respondeu ao health, mas não está disponível",
            extra={
                "event": "agent_registration_not_online",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": "Agent não está online",
            "health": health,
        }

    # ========================================================
    # 5. VALIDA O ID INFORMADO PELO AGENT
    # ========================================================

    agent_id_agent = health.get("agent_id")

    if not agent_id_agent:

        logger.warning(
            "Agent não informou identificador no health",
            extra={
                "event": "agent_registration_missing_agent_id",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": "Agent não informou agent_id",
            "health": health,
        }

    if agent_id_agent != agent_id:

        logger.warning(
            "Identificador retornado pelo Agent não corresponde ao cadastro",
            extra={
                "event": "agent_registration_agent_id_mismatch",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
                "reason": f"received_agent_id={agent_id_agent}",
            },
        )

        return {
            "status": "error",
            "message": (
                "O agent_id informado pelo Agent "
                "não corresponde ao cadastro."
            ),
            "agent_id_cadastro": agent_id,
            "agent_id_agent": agent_id_agent,
        }

    # ========================================================
    # 6. CONSULTA CONFIGURAÇÃO DO AGENT
    # ========================================================

    config_url = f"{base_url}/config"

    try:

        response = requests.get(
            config_url,
            headers={
                "Authorization": f"Bearer {agent_token}",
            },
            allow_redirects=False,
            timeout=AGENT_REQUEST_TIMEOUT,
        )

    except requests.RequestException as error:

        logger.error(
            "Não foi possível consultar a configuração do Agent",
            extra={
                "event": "agent_registration_config_request_failed",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        # Detalhes técnicos permanecem somente nos logs.
        return {
            "status": "error",
            "message": "Não foi possível consultar a configuração do Agent",
            "agent_id": agent_id,
        }

    # ========================================================
    # 7. VALIDA HTTP DA CONFIGURAÇÃO
    # ========================================================

    if response.status_code != 200:

        logger.error(
            "Agent respondeu com erro HTTP ao consultar configuração",
            extra={
                "event": "agent_registration_config_http_error",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
                "http_status": response.status_code,
            },
        )

        return {
            "status": "error",
            "message": "Agent respondeu com erro no /config",
            "agent_id": agent_id,
            "http_status": response.status_code,
        }

    try:

        config = response.json()

    except ValueError:

        logger.error(
            "Agent retornou JSON inválido ao consultar configuração",
            extra={
                "event": "agent_registration_config_invalid_json",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no /config",
            "agent_id": agent_id,
        }

    # ========================================================
    # 8. VALIDA DADOS DA CONFIGURAÇÃO
    # ========================================================

    required_fields = [
        "agent_id",
        "name",
        "host",
        "port",
        "rpa_directory",
    ]

    for field in required_fields:

        if field not in config:

            logger.warning(
                "Configuração do Agent não contém campo obrigatório",
                extra={
                    "event": "agent_registration_config_missing_field",
                    "agent_id": agent_id,
                    "agent_host": host,
                    "agent_port": port,
                    "reason": f"missing_field={field}",
                },
            )

            return {
                "status": "error",
                "message": (
                    f"Agent não informou o campo '{field}' "
                    "na configuração."
                ),
                "agent_id": agent_id,
            }

    # ========================================================
    # 9. VALIDA AGENT_ID DA CONFIGURAÇÃO
    # ========================================================

    if config["agent_id"] != agent_id:

        logger.warning(
            "Identificador da configuração do Agent não corresponde ao cadastro",
            extra={
                "event": "agent_registration_config_agent_id_mismatch",
                "agent_id": agent_id,
                "agent_host": host,
                "agent_port": port,
                "reason": (
                    f"config_agent_id={config['agent_id']}"
                ),
            },
        )

        return {
            "status": "error",
            "message": (
                "O agent_id da configuração "
                "não corresponde ao cadastro."
            ),
            "agent_id_cadastro": agent_id,
            "agent_id_config": config["agent_id"],
        }

    # ========================================================
    # 10. MONTA AGENT VALIDADO
    # ========================================================

    agent_validado = {
        "agent_id": config["agent_id"],
        "name": config["name"],
        "host": config["host"],
        "port": int(config["port"]),
        "rpa_directory": config["rpa_directory"],
        "status": "online",
    }

    # ========================================================
    # 11. ATIVA O AGENT
    # ========================================================

    status_url = f"{base_url}/config/status"

    try:

        response = requests.put(
            status_url,
            json={
                "status": "online",
            },
            headers={
                "Authorization": f"Bearer {agent_token}",
            },
            allow_redirects=False,
            timeout=AGENT_REQUEST_TIMEOUT,
        )

    except requests.RequestException as error:

        logger.error(
            "Falha de comunicação ao ativar Agent",
            extra={
                "event": "agent_activation_request_failed",
                "agent_id": agent_id,
                "agent_name": agent_validado["name"],
                "agent_host": host,
                "agent_port": port,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        # A exceção completa já foi registrada pelo logger acima.
        # A resposta da API não expõe detalhes internos da
        # comunicação entre Control Room e Agent.
        return {
            "status": "error",
            "message": (
                "Agent validado, mas não foi possível ativá-lo"
            ),
            "agent_id": agent_id,
        }

    # ========================================================
    # 12. VALIDA ATIVAÇÃO
    # ========================================================

    if response.status_code != 200:

        logger.error(
            "Agent respondeu com erro HTTP durante ativação",
            extra={
                "event": "agent_activation_http_error",
                "agent_id": agent_id,
                "agent_name": agent_validado["name"],
                "agent_host": host,
                "agent_port": port,
                "http_status": response.status_code,
            },
        )

        # Não refletimos o corpo retornado pelo Agent.
        # O status HTTP é suficiente para diagnóstico funcional.
        return {
            "status": "error",
            "message": (
                "Não foi possível alterar o status "
                "do Agent para online"
            ),
            "agent_id": agent_id,
            "http_status": response.status_code,
        }

    try:

        status_response = response.json()

    except ValueError:

        logger.error(
            "Agent retornou JSON inválido durante ativação",
            extra={
                "event": "agent_activation_invalid_json",
                "agent_id": agent_id,
                "agent_name": agent_validado["name"],
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": (
                "Agent retornou JSON inválido ao atualizar status"
            ),
            "agent_id": agent_id,
        }

    if status_response.get("status") != "success":

        logger.warning(
            "Agent não confirmou a ativação",
            extra={
                "event": "agent_activation_not_confirmed",
                "agent_id": agent_id,
                "agent_name": agent_validado["name"],
                "agent_host": host,
                "agent_port": port,
            },
        )

        return {
            "status": "error",
            "message": "Agent não confirmou ativação",
            "agent_id": agent_id,
            "response": status_response,
        }

    # ========================================================
    # 13. ATUALIZA O CADASTRO NO BANCO
    # ========================================================

    try:

        # Reconsulta dentro da mesma sessão antes da alteração.
        db_agent = buscar_agent_por_id(
            db,
            agent_id,
        )

        if not db_agent:

            logger.error(
                "Agent não encontrado ao atualizar cadastro após validação",
                extra={
                    "event": (
                        "agent_registration_database_record_missing"
                    ),
                    "agent_id": agent_id,
                    "agent_name": agent_validado["name"],
                    "agent_host": host,
                    "agent_port": port,
                },
            )

            return {
                "status": "error",
                "message": "Agent não encontrado no Control Room.",
                "agent_id": agent_id,
            }

        atualizar_agent_registrado(
            db_agent,
            name=agent_validado["name"],
            host=agent_validado["host"],
            port=agent_validado["port"],
            rpa_directory=agent_validado["rpa_directory"],
        )

        db.commit()
        db.refresh(db_agent)

    except Exception as error:

        db.rollback()

        logger.exception(
            "Erro ao atualizar cadastro do Agent no banco",
            extra={
                "event": "agent_registration_database_update_failed",
                "agent_id": agent_id,
                "agent_name": agent_validado["name"],
                "agent_host": host,
                "agent_port": port,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        # A exceção completa já foi registrada pelo logger.
        return {
            "status": "error",
            "message": (
                "Não foi possível atualizar o Agent no Control Room."
            ),
            "agent_id": agent_id,
        }

    # ========================================================
    # 14. RETORNO
    # ========================================================

    logger.info(
        "Agent registrado e ativado com sucesso",
        extra={
            "event": "agent_registered",
            "agent_id": agent_id,
            "agent_name": agent_validado["name"],
            "agent_host": agent_validado["host"],
            "agent_port": agent_validado["port"],
        },
    )

    return {
        "status": "success",
        "message": "Agent validado, ativado e cadastrado",
        "agent": agent_validado,
    }