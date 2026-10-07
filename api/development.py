# ============================================================
# DEVELOPMENT API
# ============================================================
#
# Router HTTP da área de Desenvolvimento do DUET CORE.
#
# RESPONSABILIDADE DESTE ARQUIVO:
#
# - declarar endpoints FastAPI;
# - receber parâmetros HTTP;
# - abrir sessão do banco;
# - aplicar autenticação/RBAC;
# - delegar regras de negócio aos services.
#
# As regras de negócio foram separadas no pacote:
#
#     development/
#
# IMPORTANTE:
#
# Este router deve permanecer fino.
# Regras de negócio novas devem ser implementadas nos
# respectivos services, e não diretamente neste arquivo.
# ============================================================
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    status,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from sqlalchemy.orm import Session

from auth.permissions import (
    require_permission,
)

from database import (
    SessionLocal,
)


# ============================================================
# SCHEMAS
# ============================================================

from schemas.development import (
    DevelopmentFolderCreate,
    AutomationProjectCreate,
    AutomationProjectCardUpdate,
    ProjectCommentCreate,
    ProjectActivityListResponse,
    ProjectCommentAttachmentCreateResponse,
    ProjectCommentCreateResponse,
    DevelopmentStageMove,
    DevelopmentPublishRequest,
    WorkspaceFileSave,
    WorkspaceItemCreate,
    WorkspaceItemRename,
    DevelopmentLibraryCreate,
)
from schemas.development_project_import import (
    DevelopmentProjectImportConfirmRequest,
)


# ============================================================
# FOLDERS SERVICE
# ============================================================

from development.folders_service import (
    listar_pastas_service,
    criar_pasta_service,
)


# ============================================================
# PROJECTS SERVICE
# ============================================================

from development.projects_service import (
    listar_projetos_service,
    criar_projeto_service,
    consultar_projeto_service,
)
# ============================================================

from development.project_import.service import (
    analisar_importacao_projeto_service,
    confirmar_importacao_projeto_service,
)


# ============================================================
# KANBAN SERVICE
# ============================================================

from development.kanban_service import (
    listar_usuarios_card_service,
    atualizar_detalhes_card_service,
    listar_comentarios_projeto_service,
    adicionar_comentario_projeto_service,
)
from development.comment_attachments_service import (
    criar_anexo_comentario_service,
    excluir_anexo_pendente_service,
    obter_anexo_comentario_service,
)


# ============================================================
# WORKFLOW SERVICE
# ============================================================

from development.workflow_service import (
    listar_estagios_workflow_service,
    consultar_quadro_workflow_service,
    consultar_historico_workflow_service,
    movimentar_projeto_workflow_service,
    publicar_projeto_workflow_service,
)


# ============================================================
# CHECKOUT SERVICE
# ============================================================

from development.checkout_service import (
    consultar_checkout_projeto_service,
    realizar_checkout_projeto_service,
    realizar_checkin_projeto_service,
    force_release_checkout_projeto_service,
)


# DUET_PROJECT_CHECKOUT_V22_20261002:CHECKOUT_OVERVIEW_API
from development.checkout_history_service import (
    listar_estados_checkout_service,
    listar_historico_checkout_service,
)


# ============================================================
# TRASH SERVICE
# ============================================================

from development.trash_service import (
    listar_lixeira_projetos_service,
    excluir_projeto_service,
    restaurar_projeto_service,
    excluir_projeto_permanentemente_service,
)


# ============================================================
# LIBRARIES SERVICE
# ============================================================

from development.libraries_service import (
    listar_bibliotecas_projeto_service,
    criar_biblioteca_projeto_service,
    excluir_biblioteca_projeto_service,
)


# ============================================================
# DEVELOPMENT - LIBRARY IMPORT SERVICE
# ============================================================

from development.library_import_service import (
    importar_biblioteca_projeto_service,
)

# ============================================================
# DEVELOPMENT - LIBRARY IMPORT SERVICE
# ============================================================

from development.library_import_service import (
    importar_biblioteca_projeto_service,
)
# ============================================================
# WORKSPACE SERVICE
# ============================================================

from development.workspace_service import (
    listar_workspace_service,
    abrir_arquivo_workspace_service,
    salvar_arquivo_workspace_service,
    criar_arquivo_workspace_service,
    criar_pasta_workspace_service,
    renomear_item_workspace_service,
    excluir_item_workspace_service,
)

from development.workspace_asset_service import (
    enviar_asset_workspace_service,
    preparar_download_asset_workspace_service,
)


# ============================================================
# RELEASE SERVICE
# ============================================================

from development.release_service import (
    consultar_previa_release_service,
    listar_robos_origem_release_service,
)

# ============================================================
# TERMINAL DO DEVELOPMENT
# ============================================================
#
# O WebSocket não utiliza automaticamente o mesmo fluxo de
# Depends() das rotas HTTP. Por isso reutilizamos diretamente
# as primitivas de autenticação e RBAC já existentes no DUET.
# ============================================================

from auth.session import obter_usuario_da_sessao

from auth.permissions import (
    usuario_tem_permissao,
)

from auth.origin_security import (
    obter_origins_permitidos,
)

from database import SessionLocal

from development.terminal_service import (
    preparar_terminal_development,
    validar_checkout_terminal_development,
)

from development.terminal_observability import (
    registrar_falha_websocket_terminal,
    registrar_terminal_encerrado_por_perda_checkout,
)
import asyncio
import json
# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    """
    Abre uma sessão SQLAlchemy para a requisição e garante
    seu fechamento ao final.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/development",
    tags=["Development"],
)


# ============================================================
# FOLDERS
# ============================================================

@router.get(
    "/folders"
)
def listar_pastas(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Lista as pastas ativas do Desenvolvimento."""

    return listar_pastas_service(
        db=db,
    )


@router.post(
    "/folders",
    status_code=status.HTTP_201_CREATED,
)
def criar_pasta(
    request: DevelopmentFolderCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "create",
        )
    ),
):
    """Cria uma pasta ou subpasta do Desenvolvimento."""

    return criar_pasta_service(
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# KANBAN - USUÁRIOS
# ============================================================

@router.get(
    "/card-users"
)
def listar_usuarios_card(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Lista usuários disponíveis para responsabilidade."""

    return listar_usuarios_card_service(
        db=db,
    )


# ============================================================
# PROJECTS
# ============================================================
#
# ATENÇÃO:
#
# /projects/trash precisa permanecer ANTES de
# /projects/{project_id}.
#
# Caso contrário, "trash" poderá ser interpretado como
# project_id.
# ============================================================

@router.get(
    "/projects"
)
def listar_projetos(
    folder_id: int | None = None,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Lista AutomationProjects ativos."""

    return listar_projetos_service(
        folder_id=folder_id,
        db=db,
    )


@router.get(
    "/projects/trash"
)
def listar_lixeira_projetos(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "trash_view",
        )
    ),
):
    """Lista AutomationProjects presentes na Lixeira."""

    return listar_lixeira_projetos_service(
        db=db,
    )


@router.post(
    "/projects",
    status_code=status.HTTP_201_CREATED,
)
def criar_projeto(
    request: AutomationProjectCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "create",
        )
    ),
):
    """Cria um AutomationProject."""

    return criar_projeto_service(
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJECT IMPORT
# ============================================================
#
# IMPORTANTE:
# Estas rotas permanecem antes de /projects/{project_id}.
# Caso contrário, o segmento estático "import" poderia ser
# interpretado como project_id pelo roteamento dinâmico.
# ============================================================

@router.post(
    "/projects/import/analyze",
)
async def analisar_importacao_projeto(
    file: UploadFile = File(...),
    usuario=Depends(
        require_permission(
            "Development",
            "create",
        )
    ),
):
    """Analisa um pacote antes da criação do AutomationProject."""

    return await analisar_importacao_projeto_service(
        file=file,
        usuario=usuario,
    )


@router.post(
    "/projects/import/confirm",
    status_code=status.HTTP_201_CREATED,
)
def confirmar_importacao_projeto(
    request: DevelopmentProjectImportConfirmRequest,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "create",
        )
    ),
):
    """Cria o AutomationProject somente após EntryPoint válido."""

    return confirmar_importacao_projeto_service(
        request=request,
        db=db,
        usuario=usuario,
    )


@router.get(
    "/projects/{project_id}"
)
def consultar_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Consulta um AutomationProject."""

    return consultar_projeto_service(
        project_id=project_id,
        db=db,
    )


# ============================================================
# KANBAN - CARD
# ============================================================

@router.patch(
    "/projects/{project_id}/card-details"
)
def atualizar_detalhes_card(
    project_id: int,
    request: AutomationProjectCardUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Atualiza os detalhes editáveis do card."""

    return atualizar_detalhes_card_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


@router.get(
    "/projects/{project_id}/comments",
    response_model=ProjectActivityListResponse,
)
def listar_comentarios_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Lista comentários do projeto."""

    return listar_comentarios_projeto_service(
        project_id=project_id,
        db=db,
    )


@router.post(
    "/projects/{project_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectCommentCreateResponse,
)
def adicionar_comentario_projeto(
    project_id: int,
    request: ProjectCommentCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Adiciona comentário ao projeto."""

    return adicionar_comentario_projeto_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# WORKFLOW
# ============================================================

@router.get(
    "/workflow/stages"
)
def listar_estagios_workflow(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Lista os estágios ativos do Workflow."""

    return listar_estagios_workflow_service(
        db=db,
    )


@router.get(
    "/workflow/board"
)
def consultar_quadro_workflow(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Retorna o quadro Kanban do Desenvolvimento."""

    return consultar_quadro_workflow_service(
        db=db,
    )


@router.get(
    "/projects/{project_id}/stage-history"
)
def consultar_historico_workflow(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Retorna o histórico de estágios do projeto."""

    return consultar_historico_workflow_service(
        project_id=project_id,
        db=db,
    )


@router.patch(
    "/projects/{project_id}/stage"
)
def movimentar_projeto_workflow(
    project_id: int,
    request: DevelopmentStageMove,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "move_stage",
        )
    ),
):
    """Move o projeto entre estágios normais."""

    return movimentar_projeto_workflow_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


@router.post(
    "/projects/{project_id}/publish"
)
def publicar_projeto_workflow(
    project_id: int,
    request: DevelopmentPublishRequest,
    db: Session = Depends(get_db),

    # Publicar o projeto também pode criar/publicar
    # recursos nos domínios de Robots e Libraries.
    _robots_create=Depends(
        require_permission(
            "Robots",
            "create",
        )
    ),

    _libraries_publish=Depends(
        require_permission(
            "Libraries",
            "publish",
        )
    ),

    _libraries_create=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),

    usuario=Depends(
        require_permission(
            "Development",
            "publish",
        )
    ),
):
    """Publica o projeto APPROVED -> PUBLISHED."""

    return publicar_projeto_workflow_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# DUET_PROJECT_CHECKOUT_V22_20261002:CHECKOUT_OVERVIEW_API
# CHECKOUT - VISIBILIDADE E RASTREABILIDADE
# ============================================================

@router.get(
    "/checkout/projects/states"
)
def listar_estados_checkout_projetos(
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission("Development", "view")
    ),
):
    return listar_estados_checkout_service(
        db=db,
        usuario=usuario,
    )


@router.get(
    "/checkout/projects/{project_id}/history"
)
def listar_historico_checkout_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission("Development", "view")
    ),
):
    return listar_historico_checkout_service(
        project_id=project_id,
        db=db,
    )


# ============================================================
# CHECKOUT
# ============================================================

@router.get(
    "/projects/{project_id}/checkout"
)
def consultar_checkout_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Consulta o Checkout atual do projeto."""

    return consultar_checkout_projeto_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


@router.post(
    "/projects/{project_id}/checkout"
)
def realizar_checkout_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "checkout",
        )
    ),
):
    """Adquire Checkout exclusivo do projeto."""

    return realizar_checkout_projeto_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


@router.post(
    "/projects/{project_id}/checkin"
)
def realizar_checkin_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "checkout",
        )
    ),
):
    """Libera o Checkout pertencente ao próprio usuário."""

    return realizar_checkin_projeto_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


@router.post(
    "/projects/{project_id}/checkout/force-release"
)
def force_release_checkout_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "force_checkout_release",
        )
    ),
):
    """Libera administrativamente o Checkout atual."""

    return force_release_checkout_projeto_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


# ============================================================
# TRASH
# ============================================================

@router.delete(
    "/projects/{project_id}"
)
def excluir_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "delete",
        )
    ),
):
    """Envia o projeto para a Lixeira."""

    return excluir_projeto_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


@router.post(
    "/projects/{project_id}/restore"
)
def restaurar_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "restore",
        )
    ),
):
    """Restaura um projeto da Lixeira."""

    return restaurar_projeto_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


@router.delete(
    "/projects/{project_id}/permanent"
)
def excluir_projeto_permanentemente(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "permanent_delete",
        )
    ),
):
    """Exclui permanentemente um projeto da Lixeira."""

    return excluir_projeto_permanentemente_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJECT LIBRARIES
# ============================================================

@router.get(
    "/projects/{project_id}/libraries"
)
def listar_bibliotecas_projeto(
    project_id: int,
    db: Session = Depends(get_db),

    # Além de visualizar Development, o usuário precisa
    # possuir acesso ao domínio global de Libraries.
    _libraries_view=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),

    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Lista Libraries vinculadas/novas do projeto."""

    return listar_bibliotecas_projeto_service(
        project_id=project_id,
        db=db,
    )


@router.post(
    "/projects/{project_id}/libraries",
    status_code=status.HTTP_201_CREATED,
)
def criar_biblioteca_projeto(
    project_id: int,
    request: DevelopmentLibraryCreate,
    db: Session = Depends(get_db),

    _libraries_create=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),

    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Cria uma nova Library dentro do projeto."""

    return criar_biblioteca_projeto_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )

# ============================================================
# PROJECT LIBRARIES - IMPORTAR ZIP PARA DEVELOPMENT
# ============================================================

@router.post(
    "/projects/{project_id}/libraries/import",
    status_code=status.HTTP_201_CREATED,
)
async def importar_biblioteca_projeto(
    project_id: int,

    # --------------------------------------------------------
    # Metadados da Library enviados via multipart/form-data.
    # --------------------------------------------------------

    name: str = Form(...),

    import_name: str = Form(...),

    description: str | None = Form(None),

    # --------------------------------------------------------
    # Pacote ZIP que será materializado como Working Copy.
    # --------------------------------------------------------

    file: UploadFile = File(...),

    db: Session = Depends(
        get_db
    ),

    # --------------------------------------------------------
    # RBAC - LIBRARIES
    # --------------------------------------------------------
    #
    # A importação pode criar uma nova identidade global.
    # --------------------------------------------------------

    _libraries_create=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),

    # --------------------------------------------------------
    # Também pode reutilizar uma Library já publicada.
    # --------------------------------------------------------

    _libraries_use=Depends(
        require_permission(
            "Libraries",
            "use",
        )
    ),

    # --------------------------------------------------------
    # RBAC - DEVELOPMENT
    # --------------------------------------------------------
    #
    # A operação altera fisicamente o Workspace do projeto.
    # --------------------------------------------------------

    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """
    Importa um ZIP de Library diretamente para o Development.

    A operação cria/materializa uma Working Copy no projeto.

    IMPORTANTE:

    - não cria LibraryVersion;
    - não promove versão para Produção;
    - não executa publicação standalone;
    - a publicação continua ocorrendo somente no Release.
    """

    return await importar_biblioteca_projeto_service(
        project_id=project_id,
        name=name,
        import_name=import_name,
        description=description,
        file=file,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJECT LIBRARIES - EXCLUIR
# ============================================================

@router.delete(
    "/projects/{project_id}/libraries/{library_id}"
)
def excluir_biblioteca_projeto(
    project_id: int,
    library_id: int,
    db: Session = Depends(get_db),

    # A Library faz parte da composição reutilizável do projeto.
    # A permissão "use" mantém a mesma regra utilizada pela
    # gestão de dependências publicadas.
    _libraries_use=Depends(
        require_permission(
            "Libraries",
            "use",
        )
    ),

    # Como a operação altera o Workspace e a composição do
    # AutomationProject, Development:edit também é obrigatório.
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """
    Remove uma Library do AutomationProject.

    Para Library nova ainda não publicada, descarta também
    sua identidade global quando não existir histórico ou
    qualquer outra referência.

    Para Library já publicada, preserva todo o histórico global.
    """

    return excluir_biblioteca_projeto_service(
        project_id=project_id,
        library_id=library_id,
        db=db,
        usuario=usuario,
    )




# ============================================================
# WORKSPACE
# ============================================================

@router.get(
    "/projects/{project_id}/workspace/tree"
)
def listar_workspace(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Retorna a árvore do Workspace."""

    return listar_workspace_service(
        project_id=project_id,
        db=db,
    )


@router.get(
    "/projects/{project_id}/workspace/file"
)
def abrir_arquivo_workspace(
    project_id: int,
    path: str,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Abre um arquivo textual do Workspace."""

    return abrir_arquivo_workspace_service(
        project_id=project_id,
        path=path,
        db=db,
    )


# ============================================================
# WORKSPACE - ASSETS DE LIBRARY
# ============================================================

@router.post(
    "/projects/{project_id}/workspace/assets",
    status_code=status.HTTP_201_CREATED,
)
async def enviar_asset_workspace(
    project_id: int,
    target_path: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Envia arquivo para uma pasta de Library do Workspace."""

    return await enviar_asset_workspace_service(
        project_id=project_id,
        target_path=target_path,
        file=file,
        db=db,
        usuario=usuario,
    )


@router.get(
    "/projects/{project_id}/workspace/assets"
)
def baixar_asset_workspace(
    project_id: int,
    path: str,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """Baixa arquivo ou pasta de Library; pastas são entregues em ZIP."""

    download = (
        preparar_download_asset_workspace_service(
            project_id=project_id,
            path=path,
            db=db,
        )
    )

    background = (
        BackgroundTask(
            download.cleanup
        )
        if download.temporary
        else None
    )

    return FileResponse(
        path=str(download.path),
        filename=download.filename,
        media_type=download.media_type,
        background=background,
    )


@router.put(
    "/projects/{project_id}/workspace/file"
)
def salvar_arquivo_workspace(
    project_id: int,
    request: WorkspaceFileSave,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Salva um arquivo textual do Workspace."""

    return salvar_arquivo_workspace_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


@router.post(
    "/projects/{project_id}/workspace/files",
    status_code=status.HTTP_201_CREATED,
)
def criar_arquivo_workspace(
    project_id: int,
    request: WorkspaceItemCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Cria um arquivo vazio no Workspace."""

    return criar_arquivo_workspace_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


@router.post(
    "/projects/{project_id}/workspace/folders",
    status_code=status.HTTP_201_CREATED,
)
def criar_pasta_workspace(
    project_id: int,
    request: WorkspaceItemCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Cria uma pasta no Workspace."""

    return criar_pasta_workspace_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


@router.patch(
    "/projects/{project_id}/workspace/item"
)
def renomear_item_workspace(
    project_id: int,
    request: WorkspaceItemRename,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Renomeia arquivo ou pasta do Workspace."""

    return renomear_item_workspace_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


@router.delete(
    "/projects/{project_id}/workspace/item"
)
def excluir_item_workspace(
    project_id: int,
    path: str,
    recursive: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """Exclui arquivo ou pasta do Workspace."""

    return excluir_item_workspace_service(
        project_id=project_id,
        path=path,
        recursive=recursive,
        db=db,
        usuario=usuario,
    )

# ============================================================
# TERMINAL INTERATIVO DO STUDIO
# ============================================================
#
# O terminal utiliza WebSocket porque precisamos manter uma
# conexão bidirecional persistente:
#
#     navegador -> stdin do cmd.exe
#     stdout     -> navegador
#
# SEGURANÇA:
#
# Antes de iniciar qualquer processo:
#
# 1. valida Origin;
# 2. exige cookie session_id;
# 3. valida a sessão;
# 4. exige Development:edit;
# 5. exige Checkout do próprio usuário;
# 6. somente então inicia o terminal.
#
# O Checkout é validado novamente pelo terminal_service.
# ============================================================

@router.websocket(
    "/projects/{project_id}/terminal"
)
async def terminal_development_websocket(
    websocket: WebSocket,
    project_id: int,
):
    """
    Abre uma sessão de terminal persistente para o projeto.

    Cada conexão WebSocket corresponde a um processo cmd.exe
    executado dentro do Workspace oficial do AutomationProject.
    """

    db = None
    usuario = None
    terminal = None
    output_task = None
    checkout_guard_task = None


    try:

        # ====================================================
        # 1. VALIDAR ORIGIN
        # ====================================================
        #
        # WebSocket autenticado por cookie também precisa de
        # proteção contra conexões iniciadas por sites externos.
        #
        # Não reutilizamos validar_origin_cookie() porque aquela
        # função foi criada especificamente para Request HTTP.
        # A fonte da configuração, entretanto, é exatamente a
        # mesma: obter_origins_permitidos().
        # ====================================================

        origin = websocket.headers.get(
            "origin"
        )

        if not origin:

            await websocket.close(
                code=1008,
                reason="Origin não informado.",
            )

            return

        origin_normalizado = (
            origin.strip().rstrip("/")
        )

        if (
            origin_normalizado
            not in obter_origins_permitidos()
        ):

            await websocket.close(
                code=1008,
                reason="Origin não permitido.",
            )

            return


        # ====================================================
        # 2. AUTENTICAÇÃO
        # ====================================================
        #
        # O frontend do DUET já utiliza session_id.
        # O navegador envia esse cookie automaticamente durante
        # o handshake WebSocket quando aplicável ao host.
        # ====================================================

        session_id = websocket.cookies.get(
            "session_id"
        )

        if not session_id:

            await websocket.close(
                code=1008,
                reason="Usuário não autenticado.",
            )

            return

        usuario = obter_usuario_da_sessao(
            session_id
        )

        if not usuario:

            await websocket.close(
                code=1008,
                reason="Sessão inválida ou expirada.",
            )

            return


        # ====================================================
        # 3. BANCO DE DADOS
        # ====================================================

        db = SessionLocal()


        # ====================================================
        # 4. RBAC
        # ====================================================
        #
        # Terminal possui capacidade de modificar o Workspace.
        # Portanto utilizamos a mesma permissão das operações
        # mutáveis do Studio:
        #
        #     Development:edit
        # ====================================================

        permitido = usuario_tem_permissao(
            usuario=usuario,
            db=db,
            resource="Development",
            action="edit",
        )

        if not permitido:

            await websocket.close(
                code=1008,
                reason=(
                    "Usuário não possui "
                    "Development:edit."
                ),
            )

            return


        # ====================================================
        # 5. PREPARAR TERMINAL
        # ====================================================
        #
        # Esta chamada também valida:
        #
        # - projeto ativo;
        # - Checkout pertencente ao usuário;
        # - Workspace físico.
        # ====================================================

        terminal = preparar_terminal_development(
            project_id=project_id,
            db=db,
            usuario=usuario,
        )


        # ====================================================
        # 6. ACEITAR WEBSOCKET
        # ====================================================
        #
        # Somente aceitamos a conexão DEPOIS das validações.
        # ====================================================

        await websocket.accept()


        # ====================================================
        # 7. INICIAR CMD.EXE
        # ====================================================

        try:

            await terminal.start()

        except Exception:

            # start() possui observabilidade própria.
            # Aqui a camada WebSocket apenas encerra a conexão.
            try:

                await websocket.close(
                    code=1011,
                    reason="Não foi possível iniciar o terminal.",
                )

            except Exception:
                pass

            return


        # ====================================================
        # 8. GUARDA CONTÍNUA DO CHECKOUT
        # ====================================================
        #
        # O Checkout pode ser encerrado em outra aba, outro navegador
        # ou por Force Release administrativo enquanto o cmd.exe está
        # aberto. Portanto, a autorização não pode ser validada apenas
        # no handshake do WebSocket.
        #
        # Quando o lock deixa de pertencer ao usuário:
        # - o terminal é encerrado;
        # - o WebSocket é fechado;
        # - nenhum processo já aberto continua alterando o Workspace.
        # ====================================================

        async def monitorar_checkout():

            while terminal.running:

                await asyncio.sleep(2)

                guard_db = SessionLocal()

                try:

                    validar_checkout_terminal_development(
                        project_id=project_id,
                        user_id=usuario.id,
                        db=guard_db,
                    )

                except HTTPException:

                    registrar_terminal_encerrado_por_perda_checkout(
                        project_id=project_id,
                        user_id=usuario.id,
                    )

                    await terminal.close()

                    try:

                        await websocket.close(
                            code=1008,
                            reason=(
                                "Checkout do projeto foi liberado. "
                                "Terminal encerrado."
                            ),
                        )

                    except Exception:
                        pass

                    return

                finally:

                    guard_db.close()


        checkout_guard_task = asyncio.create_task(
            monitorar_checkout()
        )


        # ====================================================
        # 9. ENVIO DE OUTPUT
        # ====================================================

        async def enviar_output():
            """
            Transmite stdout/stderr do terminal para o navegador.
            """

            while terminal.running:

                data = await terminal.read()

                if not data:
                    break

                # O Windows pode produzir saída usando encoding
                # diferente de UTF-8.
                #
                # Primeiro tentamos UTF-8. Se não for possível,
                # usamos o encoding tradicional do Windows.
                try:

                    texto = data.decode(
                        "utf-8"
                    )

                except UnicodeDecodeError:

                    texto = data.decode(
                        "cp1252",
                        errors="replace",
                    )

                await websocket.send_text(
                    texto
                )


        output_task = asyncio.create_task(
            enviar_output()
        )


        # ====================================================
        # 10. INPUT DO USUÁRIO
        # ====================================================
        #
        # Mantemos a conexão viva enquanto o navegador estiver
        # enviando caracteres/comandos.
        # ====================================================

        while True:

            mensagem = await websocket.receive_text()


            # ------------------------------------------------
            # PROTOCOLO DO TERMINAL
            # ------------------------------------------------
            #
            # O frontend envia mensagens JSON para distinguir:
            #
            # input  -> caracteres digitados pelo desenvolvedor
            # resize -> dimensões atuais do xterm
            #
            # Mantemos também compatibilidade temporária com
            # mensagens antigas em texto puro.
            # ------------------------------------------------

            try:

                evento = json.loads(
                    mensagem
                )

            except json.JSONDecodeError:

                # Compatibilidade com o frontend anterior.
                await terminal.write(
                    mensagem
                )

                continue


            if not isinstance(evento, dict):

                continue


            tipo = evento.get(
                "type"
            )


            # ------------------------------------------------
            # INPUT
            # ------------------------------------------------

            if tipo == "input":

                data = evento.get(
                    "data"
                )

                if isinstance(data, str):

                    await terminal.write(
                        data
                    )

                continue


            # ------------------------------------------------
            # RESIZE
            # ------------------------------------------------

            if tipo == "resize":

                rows = evento.get(
                    "rows"
                )

                cols = evento.get(
                    "cols"
                )

                if (
                    isinstance(rows, int)
                    and isinstance(cols, int)
                ):

                    await terminal.resize(
                        rows=rows,
                        cols=cols,
                    )

                continue


    # ========================================================
    # CLIENTE DESCONECTOU
    # ========================================================

    except WebSocketDisconnect:

        pass


    # ========================================================
    # ERRO DE REGRA HTTP ANTES DO ACCEPT
    # ========================================================
    #
    # preparar_terminal_development() utiliza HTTPException
    # porque também segue as regras existentes dos services.
    # Aqui transformamos isso em fechamento WebSocket.
    # ========================================================

    except HTTPException as erro:

        try:

            await websocket.close(
                code=1008,
                reason=str(
                    erro.detail
                )[:120],
            )

        except Exception:
            pass


    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception as error:

        registrar_falha_websocket_terminal(
                project_id=project_id,
                user_id=(
                    getattr(
                        usuario,
                        "id",
                        None,
                    )
                    if usuario is not None
                    else None
                ),
                error=error,
            )

        try:

            await websocket.close(
                code=1011,
                reason="Erro interno no terminal.",
            )

        except Exception:
            pass


    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        # Encerra o monitor de Checkout da sessão.
        if (
            checkout_guard_task is not None
            and not checkout_guard_task.done()
        ):

            checkout_guard_task.cancel()

            try:

                await checkout_guard_task

            except asyncio.CancelledError:
                pass

            except Exception:
                pass


        # Cancela a tarefa responsável pela transmissão do
        # stdout caso ela ainda esteja aguardando dados.
        if (
            output_task is not None
            and not output_task.done()
        ):

            output_task.cancel()

            try:

                await output_task

            except asyncio.CancelledError:
                pass

            except Exception:
                pass


        # Encerra cmd.exe.
        if terminal is not None:

            await terminal.close()


        # Libera a sessão SQLAlchemy criada especificamente
        # para esta conexão.
        if db is not None:

            db.close()
# ============================================================
# RELEASE
# ============================================================

@router.get(
    "/projects/{project_id}/release/preview"
)
def consultar_previa_release(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Development",
            "publish",
        )
    ),
):
    """Calcula a prévia do Release."""

    return consultar_previa_release_service(
        project_id=project_id,
        db=db,
    )


@router.get(
    "/release/robots"
)
def listar_robos_origem_release(
    db: Session = Depends(get_db),

    usuario=Depends(
        require_permission(
            "Development",
            "create",
        )
    ),

    _robots_view=Depends(
        require_permission(
            "Robots",
            "view",
        )
    ),
):
    """Lista a estrutura de Robots disponível como origem."""

    return listar_robos_origem_release_service(
        db=db,
    )


@router.post(
    "/projects/{project_id}/comment-attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectCommentAttachmentCreateResponse,
)
async def anexar_imagem_comentario(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario=Depends(require_permission("Development", "edit")),
):
    """Recebe uma imagem pendente e a vincula ao usuário e projeto."""

    return await criar_anexo_comentario_service(
        project_id=project_id,
        file=file,
        db=db,
        usuario=usuario,
    )


@router.delete(
    "/projects/{project_id}/comment-attachments/{attachment_id}",
)
def excluir_imagem_pendente_comentario(
    project_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(require_permission("Development", "edit")),
):
    """Remove somente imagens ainda não associadas a um comentário."""

    return excluir_anexo_pendente_service(
        project_id=project_id,
        attachment_id=attachment_id,
        db=db,
        usuario=usuario,
    )


@router.get(
    "/projects/{project_id}/comment-attachments/{attachment_id}",
    response_class=FileResponse,
)
def obter_imagem_comentario(
    project_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(require_permission("Development", "view")),
):
    """Entrega uma imagem vinculada sem revelar seu caminho físico."""

    path, media_type, filename = obter_anexo_comentario_service(
        project_id=project_id,
        attachment_id=attachment_id,
        db=db,
    )
    return FileResponse(
        path=path,
        media_type=media_type,
        filename=filename,
        headers={"Cache-Control": "private, max-age=300", "X-Content-Type-Options": "nosniff"},
    )
