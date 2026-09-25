# ============================================================
# DUET CORE - WINDOWS SESSION SERVICE
# ============================================================
#
# Responsabilidade desta camada:
#
# - descobrir qual identidade Windows está associada ao Agent;
# - consultar a sessão Windows observada pelo Agent;
# - comparar a sessão observada com a identidade configurada;
# - descriptografar a senha SOMENTE quando autenticação for
#   realmente necessária;
# - chamar /session/authenticate do Agent;
# - revalidar a sessão após a autenticação.
#
# IMPORTANTE:
#
# - nenhuma senha é persistida neste módulo;
# - nenhuma senha é registrada em log;
# - nenhuma senha é retornada ao chamador;
# - se a sessão já estiver pronta para o usuário correto,
#   o password nem sequer é descriptografado.
# ============================================================

import requests

from database import SessionLocal

from vault.device_credentials_runtime import (
    DeviceExecutionCredentialError,
    resolver_credencial_windows_device,
    resolver_identidade_windows_device,
)


# ============================================================
# NORMALIZAÇÃO DA IDENTIDADE WINDOWS
# ============================================================

def _normalizar_identidade(
    valor: str | None,
) -> str:
    """
    Normaliza domínio/usuário para comparação.

    O Windows pode devolver diferenças apenas de capitalização,
    por exemplo:

        RPA
        rpa

    Essas duas representações devem ser consideradas iguais.
    """

    return (
        valor
        or ""
    ).strip().casefold()


# ============================================================
# COMPARAR IDENTIDADE WINDOWS
# ============================================================

def _sessao_corresponde_identidade(
    *,
    session_data: dict,
    expected_domain: str,
    expected_username: str,
) -> bool:
    """
    Retorna True somente quando:

    - a sessão está pronta;
    - existe usuário;
    - domínio corresponde ao configurado;
    - usuário corresponde ao configurado.
    """

    if session_data.get("status") != "ready":
        return False

    session_username = _normalizar_identidade(
        session_data.get("username")
    )

    session_domain = _normalizar_identidade(
        session_data.get("domain")
    )

    expected_username_normalized = _normalizar_identidade(
        expected_username
    )

    expected_domain_normalized = _normalizar_identidade(
        expected_domain
    )

    return (
        session_username
        == expected_username_normalized
        and
        session_domain
        == expected_domain_normalized
    )


# ============================================================
# CONSULTAR SESSÃO DO AGENT
# ============================================================

def _consultar_sessao_agent(
    *,
    agent_host: str,
    agent_port: int,
    agent_token: str,
) -> dict:
    """
    Consulta /session/status do Agent.

    Nenhum dado secreto é enviado nesta operação.
    """

    response = requests.get(
        (
            f"http://{agent_host}:{agent_port}"
            "/session/status"
        ),
        headers={
            "Authorization": (
                f"Bearer {agent_token}"
            )
        },
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GARANTIR SESSÃO WINDOWS DO AGENT
# ============================================================

def garantir_sessao_windows_agent(
    *,
    agent_host: str,
    agent_port: int,
    agent_token: str,
    execution_credential_id: int | None,
    execution_id: int | None = None,
) -> dict:
    """
    Garante que o Agent possui uma sessão Windows pronta para
    a identidade configurada em execution_credential_id.

    Fluxo
    -----
    1. Resolve somente domain/username.
    2. Consulta /session/status.
    3. Se a identidade já está pronta, termina aqui.
    4. Caso contrário, resolve a senha em memória.
    5. Chama /session/authenticate.
    6. Consulta /session/status novamente.
    7. Confirma que a identidade correta ficou pronta.

    Retorno
    -------
    Nunca contém password.
    """

    # ========================================================
    # 1. AGENT PRECISA POSSUIR CREDENCIAL WINDOWS ASSOCIADA
    # ========================================================

    if execution_credential_id is None:

        return {
            "success": False,
            "status": "credential_not_configured",
            "message": (
                "Agent não possui Credencial Windows "
                "de execução configurada."
            ),
        }

    # ========================================================
    # 2. RESOLVE SOMENTE METADADOS NÃO SECRETOS
    # ========================================================

    db = SessionLocal()

    try:

        identidade = (
            resolver_identidade_windows_device(
                credential_id=execution_credential_id,
                db=db,
            )
        )

    except DeviceExecutionCredentialError as error:

        return {
            "success": False,
            "status": "credential_invalid",
            "message": str(error),
        }

    finally:

        db.close()

    # ========================================================
    # 3. CONSULTA A SESSÃO ATUAL
    # ========================================================

    try:

        session_data = _consultar_sessao_agent(
            agent_host=agent_host,
            agent_port=agent_port,
            agent_token=agent_token,
        )

    except (
        requests.RequestException,
        ValueError,
    ):

        return {
            "success": False,
            "status": "session_status_failed",
            "message": (
                "Não foi possível consultar a sessão "
                "Windows do Agent."
            ),
        }

    # ========================================================
    # 4. SESSÃO JÁ ESTÁ CORRETA
    # ========================================================
    #
    # Esse é o caminho normal e mais seguro.
    #
    # Nenhuma senha foi descriptografada até este ponto.
    # ========================================================

    if _sessao_corresponde_identidade(
        session_data=session_data,
        expected_domain=identidade.domain,
        expected_username=identidade.username,
    ):

        return {
            "success": True,
            "status": "ready",
            "action": "already_ready",
            "message": (
                "Sessão Windows já está pronta "
                "para a identidade configurada."
            ),
            "username": session_data.get(
                "username"
            ),
            "domain": session_data.get(
                "domain"
            ),
            "session_id": session_data.get(
                "session_id"
            ),
        }

    # ========================================================
    # 5. SOMENTE AGORA RESOLVE A SENHA
    # ========================================================

    db = SessionLocal()

    credencial = None

    try:

        credencial = (
            resolver_credencial_windows_device(
                credential_id=execution_credential_id,
                db=db,
            )
        )

    except DeviceExecutionCredentialError as error:

        return {
            "success": False,
            "status": "credential_resolution_failed",
            "message": str(error),
        }

    finally:

        db.close()

    # ========================================================
    # 6. SOLICITA AUTENTICAÇÃO AO AGENT
    # ========================================================

    authenticate_url = (
        f"http://{agent_host}:{agent_port}"
        "/session/authenticate"
    )

    try:

        authenticate_response = requests.post(
            authenticate_url,
            headers={
                "Authorization": (
                    f"Bearer {agent_token}"
                )
            },
            json={
                "username": credencial.username,
                "domain": credencial.domain,
                "password": credencial.password,
                "execution_id": execution_id,
            },
            timeout=45,
        )

        authenticate_response.raise_for_status()

        authentication_data = (
            authenticate_response.json()
        )

    except (
        requests.RequestException,
        ValueError,
    ):

        return {
            "success": False,
            "status": "authentication_request_failed",
            "message": (
                "Não foi possível autenticar a sessão "
                "Windows através do Agent."
            ),
        }

    finally:

        # ----------------------------------------------------
        # Remove nossa referência explícita ao plaintext assim
        # que a chamada ao Agent terminou.
        #
        # Strings Python são imutáveis e não existe garantia de
        # limpeza física imediata da memória, mas não mantemos
        # deliberadamente o segredo no objeto após o uso.
        # ----------------------------------------------------

        if credencial is not None:
            credencial.password = None

    # ========================================================
    # 7. AGENT INFORMOU FALHA
    # ========================================================

    if not authentication_data.get(
        "success"
    ):

        return {
            "success": False,
            "status": (
                authentication_data.get(
                    "status"
                )
                or
                "authentication_failed"
            ),
            "message": (
                authentication_data.get(
                    "message"
                )
                or
                "Agent não conseguiu autenticar "
                "a sessão Windows."
            ),
        }

    # ========================================================
    # 8. REVALIDA A SESSÃO REAL
    # ========================================================
    #
    # Não confiamos somente na resposta do endpoint de auth.
    # Consultamos novamente o estado WTS observado pelo Agent.
    # ========================================================

    try:

        session_data = _consultar_sessao_agent(
            agent_host=agent_host,
            agent_port=agent_port,
            agent_token=agent_token,
        )

    except (
        requests.RequestException,
        ValueError,
    ):

        return {
            "success": False,
            "status": "session_revalidation_failed",
            "message": (
                "A autenticação foi solicitada, mas "
                "não foi possível revalidar a sessão Windows."
            ),
        }

    # ========================================================
    # 9. CONFIRMA IDENTIDADE EXATA
    # ========================================================

    if not _sessao_corresponde_identidade(
        session_data=session_data,
        expected_domain=identidade.domain,
        expected_username=identidade.username,
    ):

        return {
            "success": False,
            "status": "wrong_windows_identity",
            "message": (
                "A sessão Windows disponível não corresponde "
                "à identidade configurada para o Agent."
            ),
            "username": session_data.get(
                "username"
            ),
            "domain": session_data.get(
                "domain"
            ),
            "connection_state": (
                session_data.get(
                    "connection_state"
                )
            ),
        }

    # ========================================================
    # 10. SUCESSO
    # ========================================================

    return {
        "success": True,
        "status": "ready",
        "action": (
            authentication_data.get(
                "action"
            )
            or
            "authenticated"
        ),
        "message": (
            "Sessão Windows autenticada e validada."
        ),
        "username": session_data.get(
            "username"
        ),
        "domain": session_data.get(
            "domain"
        ),
        "session_id": session_data.get(
            "session_id"
        ),
    }