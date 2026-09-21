# ============================================================
# SCHEMAS - DEVELOPMENT
# ============================================================
#
# Contratos de entrada utilizados pela API de Desenvolvimento
# do DUET CORE.
#
# Este módulo contém somente estruturas Pydantic.
#
# Não possui:
#
# - acesso ao banco;
# - regras de negócio;
# - acesso ao filesystem;
# - autenticação;
# - RBAC;
# - endpoints FastAPI.
#
# Dessa forma, os mesmos contratos podem ser utilizados pelo
# router e pelos services sem criar dependência da camada HTTP.
# ============================================================


from datetime import date

from pydantic import BaseModel, Field

# O contrato de publicação já pertence ao domínio de Release.
#
# Development apenas reutiliza esse contrato para manter
# compatibilidade com a API atual.
from releases.service import ReleaseRequest


# ============================================================
# PASTAS
# ============================================================

class DevelopmentFolderCreate(BaseModel):
    """
    Dados necessários para criar uma pasta na área
    de Desenvolvimento.

    parent_id:
        None:
            cria uma pasta na raiz.

        ID preenchido:
            cria uma subpasta dentro da pasta informada.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    parent_id: int | None = None


# ============================================================
# PROJETOS
# ============================================================

class AutomationProjectCreate(BaseModel):
    """
    Dados necessários para criar um projeto de automação.

    folder_id:
        Pasta da área de Desenvolvimento onde o projeto
        será criado.

        Pode ser None para projetos na raiz.

    base_robot_id:
        Quando preenchido, indica que o projeto nasceu
        a partir de um Robot já publicado.

        A versão atual do Robot é capturada pelo backend
        e armazenada como base_version.

        Para automações novas deve permanecer None.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    folder_id: int | None = None

    base_robot_id: int | None = None


# ============================================================
# DETALHES DO CARD / KANBAN
# ============================================================

class AutomationProjectCardUpdate(BaseModel):
    """
    Atualiza os dados de planejamento pertencentes
    individualmente a um card/projeto.

    Todos os campos são opcionais porque:

    - projetos antigos podem não possuir planejamento;
    - um campo pode ser definido posteriormente;
    - enviar explicitamente None permite limpar o valor.
    """

    # Usuário do DUET responsável pela parte funcional.
    functional_responsible_id: int | None = None

    # Usuário do DUET responsável pela parte técnica.
    #
    # Este campo NÃO representa quem possui Checkout.
    technical_responsible_id: int | None = None

    # Data de início do trabalho.
    start_date: date | None = None

    # Previsão de conclusão.
    due_date: date | None = None

    # Horas de esforço deste card.
    #
    # Não existe cronômetro.
    # É apenas um valor informado manualmente.
    effort_hours: float | None = Field(
        default=None,
        ge=0,
        le=999999.99,
    )


class ProjectCommentCreate(BaseModel):
    """
    Dados necessários para adicionar um comentário
    livre ao card do Kanban.
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )


# ============================================================
# WORKFLOW / KANBAN
# ============================================================

class DevelopmentStageMove(BaseModel):
    """
    Dados necessários para movimentar um projeto entre
    estágios normais do Workflow.

    target_stage_id:
        ID do estágio de destino obtido através da API:

            /development/workflow/stages

    IMPORTANTE:
        O estágio PUBLISHED não pode ser alcançado através
        da movimentação normal.

        Publicação possui fluxo protegido próprio.
    """

    target_stage_id: int


# ============================================================
# RELEASE
# ============================================================

# Mantemos exatamente o nome utilizado atualmente pela API
# de Development.
#
# O contrato real continua pertencendo ao release_service,
# evitando duplicação do schema de publicação.
DevelopmentPublishRequest = ReleaseRequest


# ============================================================
# WORKSPACE - SALVAR ARQUIVO
# ============================================================

class WorkspaceFileSave(BaseModel):
    """
    Dados utilizados para salvar um arquivo existente
    dentro do workspace de um AutomationProject.

    path:
        Caminho relativo dentro do workspace.

        Exemplos:

            main.py
            src/processamento.py

    content:
        Conteúdo textual completo que será salvo.
    """

    path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )

    # O Studio é um editor de código/configuração textual.
    #
    # O limite evita que um único request faça o backend
    # materializar conteúdo textual arbitrariamente grande.
    # 5 MiB de caracteres é muito acima do necessário para
    # código-fonte normal e ainda preserva arquivos maiores.
    content: str = Field(
        ...,
        max_length=5 * 1024 * 1024,
    )


# ============================================================
# WORKSPACE - CRIAR ITEM
# ============================================================

class WorkspaceItemCreate(BaseModel):
    """
    Utilizado para criar arquivos ou pastas dentro
    de um workspace.

    O path é sempre relativo à raiz do projeto.

    Exemplos:

        utils.py
        src
        src/services
        src/processamento.py
    """

    path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )


# ============================================================
# WORKSPACE - RENOMEAR ITEM
# ============================================================

class WorkspaceItemRename(BaseModel):
    """
    Dados necessários para renomear um arquivo ou pasta
    dentro do workspace.

    path:
        Caminho atual relativo ao workspace.

        Exemplos:

            teste.py
            src/utils.py
            elements/botoes

    new_name:
        Novo nome do arquivo ou pasta.

    IMPORTANTE:
        O rename não move o item para outra pasta.

        Ele altera somente o nome dentro do mesmo diretório.
    """

    path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )

    new_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )


# ============================================================
# BIBLIOTECA NOVA DO PROJETO
# ============================================================

class DevelopmentLibraryCreate(BaseModel):
    """
    Cria uma biblioteca reutilizável dentro do projeto atual.

    A Library nasce como identidade reservada, porém ainda
    NÃO aparece no catálogo de Produção.

    Sua primeira versão será criada somente quando o projeto
    for publicado.
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