# ============================================================
# SCHEMAS - VAULT DEVICE CREDENTIALS
# ============================================================
#
# Contratos Pydantic utilizados pela API de credenciais
# de Device do DUET.
#
# RESPONSABILIDADE DESTE ARQUIVO:
#
# - definir estruturas de entrada da API;
# - validar presença/tipo dos dados recebidos;
# - documentar o contrato HTTP das credenciais de Device.
#
# ESTE MÓDULO NÃO DEVE:
#
# - acessar banco de dados;
# - criar ou consultar VaultCredential;
# - criptografar ou descriptografar senha;
# - associar credencial a Agent;
# - validar permissões RBAC;
# - registrar rotas FastAPI;
# - executar regras de negócio.
#
# As regras de negócio pertencem a:
#
#     vault/device_credentials_service.py
#
# As rotas HTTP pertencerão a:
#
#     api/vault_device_credentials.py
#
# A associação da credencial a um Agent pertence ao domínio
# de Agents e será tratada separadamente.
# ============================================================

from pydantic import BaseModel, Field


# ============================================================
# CRIAÇÃO DE CREDENCIAL DE DEVICE
# ============================================================

class DeviceCredentialCreateRequest(BaseModel):
    """
    Dados necessários para criar uma identidade Windows
    utilizada por um Device/Agent.

    IMPORTANTE:

    O frontend NÃO informa:

        scope
        credential_type
        folder_id
        is_secret

    Esses valores pertencem à regra de negócio do backend.

    O service deverá persistir internamente:

        scope = "device"
        credential_type = "windows"
        folder_id = None

    E deverá armazenar:

        domain
        username
        password

    sendo password obrigatoriamente secreto.
    """

    name: str = Field(
        ...,
        min_length=1,
        description="Nome lógico da credencial de Device.",
    )

    domain: str = Field(
        ...,
        min_length=1,
        description=(
            "Domínio ou nome da máquina associado "
            "à conta Windows."
        ),
    )

    username: str = Field(
        ...,
        min_length=1,
        description="Usuário Windows utilizado pelo Agent.",
    )

    password: str = Field(
        ...,
        min_length=1,
        description=(
            "Senha da conta Windows. "
            "Será criptografada pelo service antes da persistência."
        ),
    )


# ============================================================
# ATUALIZAÇÃO DE CREDENCIAL DE DEVICE
# ============================================================

class DeviceCredentialUpdateRequest(BaseModel):
    """
    Atualiza os dados operacionais de uma credencial de Device.

    O nome lógico da credencial permanece imutável nesta etapa.

    domain e username representam o novo estado desejado.

    password:
        senha nova quando preenchida.

    keep_existing_password:
        quando True, preserva o ciphertext já armazenado e
        nenhuma senha nova precisa ser enviada.

    O service será responsável por validar combinações inválidas,
    por exemplo:

        keep_existing_password = False
        password = ""

    Essa validação é regra de negócio e NÃO pertence ao schema.
    """

    domain: str = Field(
        ...,
        min_length=1,
        description=(
            "Domínio ou nome da máquina associado "
            "à conta Windows."
        ),
    )

    username: str = Field(
        ...,
        min_length=1,
        description="Usuário Windows utilizado pelo Agent.",
    )

    password: str = Field(
        default="",
        description=(
            "Nova senha da conta Windows. "
            "Pode permanecer vazia quando "
            "keep_existing_password=true."
        ),
    )

    keep_existing_password: bool = Field(
        default=True,
        description=(
            "Quando true, mantém a senha já armazenada "
            "sem expô-la ao frontend."
        ),
    )
