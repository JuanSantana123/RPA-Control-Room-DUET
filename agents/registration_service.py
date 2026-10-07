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
from agents.token_security import (
    AgentTokenSecurityError,
    descriptografar_agent_token,
)

from agents.observability import (
    registrar_falha_registro_agent,
)

from schemas.agents import AgentRegisterRequest




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

        registrar_falha_registro_agent(
            reason="target_rejected",
            agent_id=agent_id,
            agent_host=str(host),
            agent_port=str(port),
            error=error,
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

        registrar_falha_registro_agent(
            reason="agent_not_found",
            agent_id=agent_id,
            agent_host=host,
            agent_port=port,
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

        registrar_falha_registro_agent(
            reason="agent_inactive",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
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
    #
    # Falhas de configuração da chave, ciphertext inválido ou
    # impossibilidade de descriptografia são tratadas como uma
    # falha operacional do registro do Agent.
    try:
        agent_token = descriptografar_agent_token(
            agent_existente.agent_token_encrypted
        )

    except AgentTokenSecurityError as error:

        registrar_falha_registro_agent(
            reason="token_decryption_failed",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
            error=error,
        )

        return {
            "status": "error",
            "message": (
                "Não foi possível recuperar a credencial "
                "técnica do Agent."
            ),
            "agent_id": agent_id,
        }

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

        registrar_falha_registro_agent(
            reason="health_connection_failed",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
            error=error,
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

        registrar_falha_registro_agent(
            reason="health_http_error",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
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

        registrar_falha_registro_agent(
            reason="health_invalid_json",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
        )

        return {
            "status": "error",
            "message": "Agent retornou JSON inválido no /health",
        }

    # ========================================================
    # 4. VALIDA STATUS DO AGENT
    # ========================================================

    if health.get("status") != "online":

        registrar_falha_registro_agent(
            reason="agent_not_online",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
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

        registrar_falha_registro_agent(
            reason="health_missing_agent_id",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
        )

        return {
            "status": "error",
            "message": "Agent não informou agent_id",
            "health": health,
        }

    if agent_id_agent != agent_id:

        registrar_falha_registro_agent(
            reason="health_agent_id_mismatch",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
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

        registrar_falha_registro_agent(
            reason="config_connection_failed",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
            error=error,
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

        registrar_falha_registro_agent(
            reason="config_http_error",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
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

        registrar_falha_registro_agent(
            reason="config_invalid_json",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
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

            registrar_falha_registro_agent(
                reason="config_missing_required_field",
                agent_id=agent_id,
                agent_name=agent_existente.name,
                agent_host=host,
                agent_port=port,
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

        registrar_falha_registro_agent(
            reason="config_agent_id_mismatch",
            agent_id=agent_id,
            agent_name=agent_existente.name,
            agent_host=host,
            agent_port=port,
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

        registrar_falha_registro_agent(
            reason="activation_connection_failed",
            agent_id=agent_id,
            agent_name=agent_validado["name"],
            agent_host=host,
            agent_port=port,
            error=error,
        )

        # A exceção completa já foi registrada pelo helper de
        # observabilidade.
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

        registrar_falha_registro_agent(
            reason="activation_http_error",
            agent_id=agent_id,
            agent_name=agent_validado["name"],
            agent_host=host,
            agent_port=port,
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

        registrar_falha_registro_agent(
            reason="activation_invalid_json",
            agent_id=agent_id,
            agent_name=agent_validado["name"],
            agent_host=host,
            agent_port=port,
        )

        return {
            "status": "error",
            "message": (
                "Agent retornou JSON inválido ao atualizar status"
            ),
            "agent_id": agent_id,
        }

    if status_response.get("status") != "success":

        registrar_falha_registro_agent(
            reason="activation_not_confirmed",
            agent_id=agent_id,
            agent_name=agent_validado["name"],
            agent_host=host,
            agent_port=port,
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

            registrar_falha_registro_agent(
                reason="database_record_missing",
                agent_id=agent_id,
                agent_name=agent_validado["name"],
                agent_host=host,
                agent_port=port,
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

        registrar_falha_registro_agent(
            reason="database_update_failed",
            agent_id=agent_id,
            agent_name=agent_validado["name"],
            agent_host=host,
            agent_port=port,
            error=error,
        )

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

    return {
        "status": "success",
        "message": "Agent validado, ativado e cadastrado",
        "agent": agent_validado,
    }