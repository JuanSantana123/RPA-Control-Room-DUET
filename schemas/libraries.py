# ============================================================
# LIBRARIES - SCHEMAS
# ============================================================
#
# Contratos Pydantic utilizados pela API global de Libraries.
#
# RESPONSABILIDADE DESTE ARQUIVO:
#
# - definir os dados aceitos pelos endpoints de Libraries;
# - validar tipos, limites e campos obrigatórios;
# - manter os contratos HTTP separados das regras de negócio.
#
# IMPORTANTE:
#
# Este arquivo NÃO acessa banco de dados.
# Este arquivo NÃO manipula arquivos físicos.
# Este arquivo NÃO contém regras de negócio.
#
# As validações específicas do domínio, como:
#
# - import_name ser um identificador Python válido;
# - versão seguir Semantic Versioning;
# - existência de Library/LibraryVersion;
# - Checkout do AutomationProject;
#
# continuarão sendo responsabilidade dos services/validators.
# ============================================================


from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# LIBRARY
# ============================================================

class LibraryCreate(BaseModel):
    """
    Cria a identidade de uma Library no catálogo global.

    name:
        Nome amigável apresentado ao usuário.

    import_name:
        Namespace Python estável utilizado pelos Robots.

        Exemplo:

            name = "Financeiro"
            import_name = "financeiro"

        Uso:

            from financeiro.pagamentos import gerar_pagamento

    description:
        Descrição funcional/técnica opcional.

    folder_id:
        Pasta organizacional do catálogo.

        None:
            cria a Library diretamente na raiz.

        ID:
            cria a Library dentro da LibraryFolder informada.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    import_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    folder_id: int | None = Field(
        default=None,
        ge=1,
    )


# ============================================================
# LIBRARY FOLDER - CREATE
# ============================================================

class LibraryFolderCreate(BaseModel):
    """
    Cria uma pasta organizacional no catálogo global de Libraries.

    parent_id:
        None:
            cria a pasta na raiz.

        ID:
            cria como subpasta de outra LibraryFolder.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    parent_id: int | None = Field(
        default=None,
        ge=1,
    )


# ============================================================
# LIBRARY FOLDER - UPDATE
# ============================================================

class LibraryFolderUpdate(BaseModel):
    """
    Renomeia e/ou move uma LibraryFolder.

    O uso posterior de:

        model_dump(exclude_unset=True)

    permite diferenciar:

        parent_id não enviado
            -> mantém o parent_id atual;

        parent_id = None
            -> move explicitamente para a raiz.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    parent_id: int | None = Field(
        default=None,
        ge=1,
    )


# ============================================================
# LIBRARY - MOVE
# ============================================================

class LibraryMoveRequest(BaseModel):
    """
    Move uma Library entre pastas do catálogo.

    folder_id:
        None:
            move a Library para a raiz.

        ID:
            move a Library para a LibraryFolder informada.
    """

    folder_id: int | None = Field(
        default=None,
        ge=1,
    )


# ============================================================
# LIBRARY - UPDATE
# ============================================================

class LibraryUpdate(BaseModel):
    """
    Atualiza os metadados amigáveis de uma Library.

    IMPORTANTE:

    import_name não faz parte deste schema.

    O import_name representa o namespace Python utilizado pelos
    Robots e, portanto, faz parte do contrato técnico da Library.
    Ele não deve ser alterado por uma simples edição de metadados.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )


# ============================================================
# PROJECT LIBRARY DEPENDENCY - CREATE
# ============================================================

class ProjectLibraryDependencyCreate(BaseModel):
    """
    Adiciona uma LibraryVersion publicada a um AutomationProject.

    O frontend informa somente library_version_id.

    O library_id correspondente será descoberto pelo backend,
    evitando que o cliente consiga enviar uma combinação como:

        library_id = 10
        library_version_id = versão pertencente à Library 20
    """

    library_version_id: int


# ============================================================
# PROJECT LIBRARY DEPENDENCY - UPDATE
# ============================================================

class ProjectLibraryDependencyUpdate(BaseModel):
    """
    Troca explicitamente a versão de uma Library já utilizada
    pelo AutomationProject.

    O endpoint recebe library_id na própria URL.

    Portanto, a LibraryVersion informada precisa obrigatoriamente
    pertencer à mesma Library.
    """

    library_version_id: int


# ============================================================
# PROJECT LIBRARY DEPENDENCIES - BULK CREATE
# ============================================================

class ProjectLibraryDependenciesBulkCreate(BaseModel):
    """
    Adiciona uma ou várias Libraries publicadas ao mesmo
    AutomationProject em uma única operação.

    Cada item representa uma LibraryVersion EXATA.

    Exemplo:

        {
            "library_version_ids": [10, 21, 35]
        }

    O backend será responsável por:

    - localizar cada LibraryVersion;
    - descobrir a Library correspondente;
    - validar versões ativas;
    - impedir duas versões da mesma Library;
    - impedir Libraries já adicionadas;
    - validar namespaces;
    - validar os snapshots físicos;
    - garantir Checkout;
    - realizar a alteração de forma atômica.
    """

    library_version_ids: list[int]