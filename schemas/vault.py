# ============================================================
# SCHEMAS - VAULT
# ============================================================
#
# Responsabilidade:
#
#     Definir os contratos de entrada utilizados pelos
#     endpoints do domínio Vault.
#
# Este módulo NÃO contém:
#
#     - acesso ao banco;
#     - regras de negócio;
#     - autenticação;
#     - autorização;
#     - commit/rollback.
#
# ============================================================

from pydantic import BaseModel, Field


# ============================================================
# CRIAÇÃO DE PASTA
# ============================================================

class VaultFolderCreateRequest(BaseModel):
    """
    Contrato utilizado para criação de uma pasta no Vault.

    parent_id = None:
        cria a pasta na raiz.

    parent_id = <id>:
        cria a pasta dentro de outra pasta existente.
    """

    # Nome da nova pasta.
    name: str = Field(
        ...,
        min_length=1,
        description="Nome da nova pasta do Vault.",
    )

    # Pasta pai.
    # None representa a raiz do Vault.
    parent_id: int | None = Field(
        default=None,
        description=(
            "ID da pasta pai. "
            "Deixe como null para criar a pasta na raiz do Vault."
        ),
    )