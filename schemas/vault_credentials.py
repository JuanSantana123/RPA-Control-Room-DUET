# ============================================================
# SCHEMAS - VAULT CREDENTIALS
# ============================================================
#
# Contratos Pydantic utilizados pela API de credenciais do Vault.
#
# Este módulo contém SOMENTE estruturas de entrada/validação.
#
# Ele não deve:
#
# - acessar banco de dados;
# - criptografar ou descriptografar valores;
# - validar permissões;
# - executar regras de negócio.
#
# As regras de negócio permanecerão nos services do domínio Vault.
# ============================================================

from pydantic import BaseModel, Field


# ============================================================
# CAMPO DE CREDENCIAL
# ============================================================

class VaultFieldRequest(BaseModel):
    """
    Representa um campo pertencente a uma credencial do Vault.

    Cada campo pode ser público ou secreto.

    Durante uma edição:

    - id identifica um campo que já existe;
    - id=None representa um novo campo;
    - keep_existing=True permite preservar um segredo já armazenado
      sem que o frontend precise receber ou reenviar o valor original.
    """

    # --------------------------------------------------------
    # ID DO CAMPO
    # --------------------------------------------------------
    #
    # None:
    #     campo novo.
    #
    # ID:
    #     campo que já pertence à credencial sendo editada.
    # --------------------------------------------------------

    id: int | None = Field(
        default=None,
        description=(
            "ID do campo existente. "
            "Deixe como null ao criar um novo campo."
        ),
    )

    # --------------------------------------------------------
    # NOME
    # --------------------------------------------------------

    name: str = Field(
        ...,
        min_length=1,
        description=(
            "Nome do campo da credencial. "
            "Exemplo: username, password, empresa."
        ),
    )

    # --------------------------------------------------------
    # VALOR
    # --------------------------------------------------------
    #
    # Para campos secretos, o service será responsável por
    # criptografar este valor antes de persistir no banco.
    #
    # Durante edição, value="" pode ser utilizado junto com
    # keep_existing=True para preservar um segredo existente.
    # --------------------------------------------------------

    value: str = Field(
        default="",
        description=(
            "Valor do campo. "
            "Para campos secretos, o valor será criptografado "
            "antes de ser armazenado."
        ),
    )

    # --------------------------------------------------------
    # CAMPO SECRETO
    # --------------------------------------------------------

    is_secret: bool = Field(
        default=False,
        description=(
            "Define se o valor do campo deve ser tratado como secreto "
            "e armazenado de forma criptografada."
        ),
    )

    # --------------------------------------------------------
    # PRESERVAR SEGREDO EXISTENTE
    # --------------------------------------------------------
    #
    # Utilizado somente durante edição.
    #
    # Evita que o frontend precise conhecer o segredo atual.
    # --------------------------------------------------------

    keep_existing: bool = Field(
        default=False,
        description=(
            "Na edição, quando true, mantém o valor secreto "
            "já armazenado sem exigir o envio do novo valor."
        ),
    )


# ============================================================
# CRIAÇÃO DE CREDENCIAL
# ============================================================

class VaultCredentialCreateRequest(BaseModel):
    """
    Dados necessários para criar uma nova credencial no Vault.

    A credencial pertence obrigatoriamente a uma VaultFolder
    e possui uma lista de campos.
    """

    # Nome lógico utilizado para identificar a credencial.
    name: str = Field(
        ...,
        min_length=1,
        description=(
            "Nome da credencial. "
            "Deve ser único dentro da pasta."
        ),
    )

    # Pasta onde a credencial será armazenada.
    folder_id: int = Field(
        ...,
        description=(
            "ID da pasta do Vault onde a credencial será armazenada."
        ),
    )

    # Campos que compõem a credencial.
    fields: list[VaultFieldRequest] = Field(
        ...,
        description=(
            "Lista de campos da credencial. "
            "Cada campo possui nome, valor e indicação se é secreto."
        ),
    )


# ============================================================
# ATUALIZAÇÃO DE CREDENCIAL
# ============================================================

class VaultCredentialUpdateRequest(BaseModel):
    """
    Dados utilizados para atualizar uma credencial existente.

    IMPORTANTE:

    O nome da credencial é imutável.

    Portanto, a edição recebe somente a lista completa de campos
    que deverá permanecer associada à credencial.
    """

    fields: list[VaultFieldRequest]