"""
Cliente do Vault para automações DUET RPA.

Este módulo NÃO acessa diretamente o Control Room.

Fluxo:

    Robot
        ↓
    rpa.vault
        ↓
    RPA Agent /vault/get
        ↓
    VaultClient
        ↓
    Control Room
        ↓
    Vault

O RPA Agent injeta automaticamente no processo do Robot:

    RPA_AGENT_URL
    RPA_EXECUTION_ID
    RPA_VAULT_TOKEN

Dessa forma, o desenvolvedor não precisa conhecer tokens,
URLs internas ou detalhes de autenticação da plataforma.
"""
import json
import os
from urllib import error as urllib_error
from urllib import request as urllib_request

def get(credential_name: str) -> dict:
    """
    Obtém uma credencial armazenada no Vault do DUET.

    Parameters
    ----------
    credential_name:
        Caminho/nome da credencial cadastrada no Vault.

    Returns
    -------
    dict
        Campos da credencial solicitada.

    Raises
    ------
    ValueError
        Quando o nome da credencial não foi informado.

    RuntimeError
        Quando a execução não possui contexto DUET válido,
        o Agent rejeita a solicitação ou ocorre erro de comunicação.
    """

    # --------------------------------------------------------
    # Validação da entrada.
    # --------------------------------------------------------

    if not credential_name:
        raise ValueError(
            "O nome da credencial não pode ser vazio."
        )

    # --------------------------------------------------------
    # Recupera o contexto que o Agent injeta automaticamente
    # no processo de cada Robot.
    # --------------------------------------------------------

    agent_url = os.getenv("RPA_AGENT_URL")
    execution_id = os.getenv("RPA_EXECUTION_ID")
    vault_token = os.getenv("RPA_VAULT_TOKEN")

    # --------------------------------------------------------
    # Essas três informações são obrigatórias.
    #
    # Se não existirem, provavelmente o código está sendo
    # executado fora do DUET RPA Agent.
    # --------------------------------------------------------

    if not agent_url:
        raise RuntimeError(
            "RPA_AGENT_URL não foi disponibilizado pelo DUET Agent."
        )

    if not execution_id:
        raise RuntimeError(
            "RPA_EXECUTION_ID não foi disponibilizado pelo DUET Agent."
        )

    if not vault_token:
        raise RuntimeError(
            "RPA_VAULT_TOKEN não foi disponibilizado pelo DUET Agent."
        )

    # --------------------------------------------------------
    # O endpoint do Agent espera execution_id numérico.
    # --------------------------------------------------------

    try:
        execution_id = int(execution_id)

    except (TypeError, ValueError) as error:
        raise RuntimeError(
            "RPA_EXECUTION_ID recebido do DUET Agent é inválido."
        ) from error

    # --------------------------------------------------------
    # Endpoint LOCAL do Agent.
    #
    # O Robot não conversa diretamente com o Control Room.
    # --------------------------------------------------------

    url = (
        f"{agent_url.rstrip('/')}"
        "/vault/get"
    )

    # --------------------------------------------------------
    # Contrato esperado pelo VaultRequest do Agent.
    # --------------------------------------------------------

    payload = {
        "credential_name": credential_name,
        "execution_id": execution_id,
        "request_token": vault_token,
    }



    # --------------------------------------------------------
    # SERIALIZA O PAYLOAD PARA JSON
    # --------------------------------------------------------
    #
    # A SDK do DUET utiliza somente bibliotecas nativas do
    # Python. Dessa forma, funcionalidades da plataforma como
    # Vault não dependem de pacotes do requirements.txt do
    # Robot.
    # --------------------------------------------------------

    body = json.dumps(
        payload
    ).encode(
        "utf-8"
    )

    # --------------------------------------------------------
    # MONTA A REQUISIÇÃO HTTP LOCAL
    # --------------------------------------------------------
    #
    # O Robot se comunica somente com o Agent instalado na
    # própria Device.
    #
    # Content-Type:
    #     necessário porque o endpoint FastAPI espera JSON.
    # --------------------------------------------------------

    requisicao = urllib_request.Request(
        url=url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:

        # ----------------------------------------------------
        # ENVIA A SOLICITAÇÃO AO AGENT
        # ----------------------------------------------------

        with urllib_request.urlopen(
            requisicao,
            timeout=10,
        ) as response:

            status_code = response.getcode()

            response_body = response.read().decode(
                "utf-8"
            )

        # ----------------------------------------------------
        # CONVERTE A RESPOSTA DO AGENT PARA JSON
        # ----------------------------------------------------

        try:
            resposta = json.loads(
                response_body
            )

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Resposta inválida do DUET Agent: "
                "o conteúdo retornado não é JSON válido."
            ) from error

        # ----------------------------------------------------
        # Validação adicional do status HTTP.
        #
        # Normalmente urllib já transforma respostas 4xx/5xx
        # em HTTPError, mas mantemos esta proteção para deixar
        # explícito o contrato da SDK.
        # ----------------------------------------------------

        if not 200 <= status_code < 300:
            raise RuntimeError(
                f"DUET Agent retornou HTTP "
                f"{status_code}: {resposta}"
            )

    except urllib_error.HTTPError as error:

        # ----------------------------------------------------
        # O Agent respondeu, porém rejeitou a solicitação.
        #
        # Tentamos preservar o corpo retornado pelo FastAPI
        # para facilitar o diagnóstico.
        # ----------------------------------------------------

        try:
            detalhe_texto = error.read().decode(
                "utf-8"
            )

            try:
                detalhe = json.loads(
                    detalhe_texto
                )

            except json.JSONDecodeError:
                detalhe = detalhe_texto

        except Exception:
            detalhe = str(error)

        raise RuntimeError(
            f"DUET Agent retornou HTTP "
            f"{error.code}: {detalhe}"
        ) from error

    except urllib_error.URLError as error:

        # ----------------------------------------------------
        # Não foi possível estabelecer comunicação com o Agent.
        # ----------------------------------------------------

        raise RuntimeError(
            f"Erro ao comunicar com o DUET RPA Agent: "
            f"{error.reason}"
        ) from error

    except TimeoutError as error:

        raise RuntimeError(
            "Tempo limite excedido ao comunicar "
            "com o DUET RPA Agent."
        ) from error

        

    # --------------------------------------------------------
    # O endpoint /vault/get retorna:
    #
    # {
    #     "status": "success",
    #     "credential": {
    #         "name": "...",
    #         "fields": {...}
    #     }
    # }
    # --------------------------------------------------------

    if resposta.get("status") != "success":
        raise RuntimeError(
            resposta.get(
                "message",
                "O DUET Agent não retornou a credencial."
            )
        )

    credential = resposta.get("credential")

    if not isinstance(credential, dict):
        raise RuntimeError(
            "Resposta inválida do DUET Agent: "
            "'credential' não foi retornado."
        )

    fields = credential.get("fields")

    if not isinstance(fields, dict):
        raise RuntimeError(
            "Resposta inválida do DUET Agent: "
            "'credential.fields' não foi retornado."
        )

    return fields