# ============================================================
# LIBRARIES API
# ============================================================
#
# Camada HTTP do domínio global de Libraries do DUET CORE.
#
# RESPONSABILIDADES DESTE ARQUIVO:
#
# - declarar endpoints FastAPI;
# - receber parâmetros HTTP;
# - abrir a sessão SQLAlchemy;
# - aplicar RBAC;
# - delegar cada operação ao service correto.
#
# IMPORTANTE:
#
# Regras de negócio NÃO devem voltar para este arquivo.
# O router deve permanecer fino.
#
# Domínios utilizados:
#
#     libraries/dependencies_service.py
#     libraries/folders_service.py
#     libraries/catalog_service.py
#     libraries/versions_service.py
#     libraries/snapshot_service.py
#     libraries/import_service.py
# ============================================================


from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    status,
)

from sqlalchemy.orm import Session

from auth.permissions import require_permission
from database import SessionLocal


# ============================================================
# SCHEMAS
# ============================================================

from schemas.libraries import (
    LibraryCreate,
    LibraryFolderCreate,
    LibraryFolderUpdate,
    LibraryMoveRequest,
    LibraryUpdate,
    ProjectLibraryDependenciesBulkCreate,
    ProjectLibraryDependencyCreate,
    ProjectLibraryDependencyUpdate,
)


# ============================================================
# SERVICES - DEPENDÊNCIAS DE PROJETO
# ============================================================

from libraries.dependencies_service import (
    adicionar_dependencia_projeto_service,
    adicionar_dependencias_projeto_em_lote_service,
    listar_bibliotecas_disponiveis_projeto_service,
    listar_dependencias_projeto_service,
    remover_dependencia_projeto_service,
    trocar_versao_projeto_service,
)


# ============================================================
# SERVICES - PASTAS / ORGANIZAÇÃO DO CATÁLOGO
# ============================================================

from libraries.folders_service import (
    atualizar_pasta_bibliotecas_service,
    criar_pasta_bibliotecas_service,
    excluir_pasta_bibliotecas_service,
    listar_pastas_bibliotecas_service,
    mover_biblioteca_service,
    obter_arvore_bibliotecas_service,
)


# ============================================================
# SERVICES - CATÁLOGO DE LIBRARIES
# ============================================================

from libraries.catalog_service import (
    atualizar_biblioteca_service,
    consultar_biblioteca_service,
    criar_biblioteca_service,
    desativar_biblioteca_service,
    listar_bibliotecas_service,
    reativar_biblioteca_service,
)


# ============================================================
# SERVICES - VERSÕES PUBLICADAS
# ============================================================

from libraries.versions_service import (
    desativar_versao_service,
    listar_robos_da_biblioteca_service,
    listar_versoes_service,
    publicar_versao_standalone_service,
)


# ============================================================
# SERVICES - SNAPSHOTS IMUTÁVEIS
# ============================================================

from libraries.snapshot_service import (
    baixar_versao_service,
    visualizar_arquivo_versao_service,
    visualizar_arvore_versao_service,
)


# ============================================================
# SERVICE - IMPORTAÇÃO DIRETA DE LIBRARY
# ============================================================

from libraries.import_service import (
    importar_biblioteca_standalone_service,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/libraries",
    tags=["Libraries"],
)


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    """
    Abre uma sessão SQLAlchemy por requisição e garante o
    fechamento ao final.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# PROJETOS - LISTAR DEPENDÊNCIAS
# ============================================================
#
# Estas rotas aparecem antes de /{library_id} para que palavras
# estáticas como "projects" nunca concorram com a rota dinâmica.
# ============================================================

@router.get(
    "/projects/{project_id}/dependencies"
)
def listar_dependencias_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
    _development_view=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """
    Lista as versões exatas de Libraries fixadas no projeto.
    """

    return listar_dependencias_projeto_service(
        project_id=project_id,
        db=db,
    )


# ============================================================
# PROJETOS - LIBRARIES DISPONÍVEIS
# ============================================================

@router.get(
    "/projects/{project_id}/available"
)
def listar_bibliotecas_disponiveis_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
    _development_view=Depends(
        require_permission(
            "Development",
            "view",
        )
    ),
):
    """
    Lista as Libraries publicadas que podem ser adicionadas ao
    AutomationProject, incluindo a versão vigente em Produção.
    """

    return listar_bibliotecas_disponiveis_projeto_service(
        project_id=project_id,
        db=db,
    )


# ============================================================
# PROJETOS - ADICIONAR UMA LIBRARY
# ============================================================

@router.post(
    "/projects/{project_id}/dependencies",
    status_code=status.HTTP_201_CREATED,
)
def adicionar_dependencia_projeto(
    project_id: int,
    request: ProjectLibraryDependencyCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "use",
        )
    ),
    _development_edit=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """
    Adiciona uma LibraryVersion exata ao projeto.
    """

    return adicionar_dependencia_projeto_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJETOS - ADICIONAR LIBRARIES EM LOTE
# ============================================================

@router.post(
    "/projects/{project_id}/dependencies/bulk",
    status_code=status.HTTP_201_CREATED,
)
def adicionar_dependencias_projeto_em_lote(
    project_id: int,
    request: ProjectLibraryDependenciesBulkCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "use",
        )
    ),
    _development_edit=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """
    Adiciona uma ou várias Libraries ao projeto em uma única
    operação atômica.
    """

    return adicionar_dependencias_projeto_em_lote_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJETOS - TROCAR VERSÃO DA LIBRARY
# ============================================================

@router.put(
    "/projects/{project_id}/dependencies/{library_id}"
)
def trocar_versao_projeto(
    project_id: int,
    library_id: int,
    request: ProjectLibraryDependencyUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "use",
        )
    ),
    _development_edit=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """
    Troca explicitamente a LibraryVersion utilizada pelo projeto.
    """

    return trocar_versao_projeto_service(
        project_id=project_id,
        library_id=library_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJETOS - REMOVER LIBRARY
# ============================================================

@router.delete(
    "/projects/{project_id}/dependencies/{library_id}"
)
def remover_dependencia_projeto(
    project_id: int,
    library_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "use",
        )
    ),
    _development_edit=Depends(
        require_permission(
            "Development",
            "edit",
        )
    ),
):
    """
    Remove o vínculo entre o projeto e a Library.
    """

    return remover_dependencia_projeto_service(
        project_id=project_id,
        library_id=library_id,
        db=db,
        usuario=usuario,
    )

# ============================================================
# LIBRARIES - REATIVAR
# ============================================================

@router.post(
    "/{library_id}/reactivate"
)
def reativar_biblioteca(
    library_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "edit",
        )
    ),
):
    """
    Reativa uma Library previamente desativada.

    A operação preserva identidade, versões e histórico.
    """

    return reativar_biblioteca_service(
        library_id=library_id,
        db=db,
        usuario=usuario,
    )
# ============================================================
# CATÁLOGO - ÁRVORE
# ============================================================

@router.get(
    "/tree"
)
def obter_arvore_bibliotecas(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Retorna a árvore organizacional Folder -> Library.
    """

    return obter_arvore_bibliotecas_service(
        include_inactive=include_inactive,
        db=db,
    )


# ============================================================
# CATÁLOGO - LISTAR PASTAS
# ============================================================

@router.get(
    "/folders"
)
def listar_pastas_bibliotecas(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Retorna a lista plana das pastas do catálogo.
    """

    return listar_pastas_bibliotecas_service(
        include_inactive=include_inactive,
        db=db,
    )


# ============================================================
# CATÁLOGO - CRIAR PASTA
# ============================================================

@router.post(
    "/folders",
    status_code=status.HTTP_201_CREATED,
)
def criar_pasta_bibliotecas(
    request: LibraryFolderCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),
):
    """
    Cria uma pasta ou subpasta no catálogo de Libraries.
    """

    return criar_pasta_bibliotecas_service(
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - RENOMEAR / MOVER PASTA
# ============================================================

@router.patch(
    "/folders/{folder_id}"
)
def atualizar_pasta_bibliotecas(
    folder_id: int,
    request: LibraryFolderUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "edit",
        )
    ),
):
    """
    Renomeia e/ou move uma pasta do catálogo.
    """

    return atualizar_pasta_bibliotecas_service(
        folder_id=folder_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - EXCLUIR / DESATIVAR PASTA
# ============================================================

@router.delete(
    "/folders/{folder_id}"
)
def excluir_pasta_bibliotecas(
    folder_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "delete",
        )
    ),
):
    """
    Desativa uma pasta vazia do catálogo.
    """

    return excluir_pasta_bibliotecas_service(
        folder_id=folder_id,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - MOVER LIBRARY
# ============================================================

@router.patch(
    "/{library_id}/folder"
)
def mover_biblioteca(
    library_id: int,
    request: LibraryMoveRequest,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "edit",
        )
    ),
):
    """
    Move uma Library entre pastas ou para a raiz.
    """

    return mover_biblioteca_service(
        library_id=library_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# LIBRARIES - LISTAR
# ============================================================

@router.get("")
@router.get(
    "/",
    include_in_schema=False,
)
def listar_bibliotecas(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Lista as Libraries do catálogo global.
    """

    return listar_bibliotecas_service(
        include_inactive=include_inactive,
        db=db,
    )


# ============================================================
# LIBRARIES - CRIAR IDENTIDADE
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def criar_biblioteca(
    request: LibraryCreate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),
):
    """
    Cria somente a identidade de uma Library.

    Nenhuma versão é publicada automaticamente por esta rota.
    """

    return criar_biblioteca_service(
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# LIBRARIES - IMPORTAÇÃO DIRETA
# ============================================================
#
# Esta é a única operação nova desta correção.
#
# A rota recebe HTTP/multipart e delega TODO o processamento ao
# libraries/import_service.py. Nenhuma regra de persistência ou
# manipulação do ZIP fica no router.
# ============================================================

@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
async def importar_biblioteca_standalone(
    name: str = Form(...),
    import_name: str = Form(...),
    version: str = Form(...),
    description: str | None = Form(None),
    folder_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),
    _publish_permission=Depends(
        require_permission(
            "Libraries",
            "publish",
        )
    ),
):
    """
    Importa uma Library pronta sem criar AutomationProject.

    Como a operação cria a Library e já publica sua primeira versão,
    exige simultaneamente Libraries:create e Libraries:publish.
    """

    return await importar_biblioteca_standalone_service(
        name=name,
        import_name=import_name,
        version=version,
        description=description,
        folder_id=folder_id,
        file=file,
        db=db,
        usuario=usuario,
    )


# ============================================================
# LIBRARIES - CONSULTAR
# ============================================================
#
# Rotas estáticas como /import, /tree, /folders e /projects ficam
# acima desta rota dinâmica para preservar o roteamento correto.
# ============================================================

@router.get(
    "/{library_id}"
)
def consultar_biblioteca(
    library_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Consulta uma Library pelo ID.
    """

    return consultar_biblioteca_service(
        library_id=library_id,
        db=db,
    )


# ============================================================
# LIBRARIES - ATUALIZAR METADADOS
# ============================================================

@router.patch(
    "/{library_id}"
)
def atualizar_biblioteca(
    library_id: int,
    request: LibraryUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "edit",
        )
    ),
):
    """
    Atualiza os metadados amigáveis de uma Library.
    """

    return atualizar_biblioteca_service(
        library_id=library_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# LIBRARIES - DESATIVAR
# ============================================================

@router.delete(
    "/{library_id}"
)
def desativar_biblioteca(
    library_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "delete",
        )
    ),
):
    """
    Desativa uma Library respeitando as proteções do domínio.
    """

    return desativar_biblioteca_service(
        library_id=library_id,
        db=db,
        usuario=usuario,
    )


# ============================================================
# VERSÕES - LISTAR
# ============================================================

@router.get(
    "/{library_id}/versions"
)
def listar_versoes(
    library_id: int,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Lista as versões publicadas de uma Library.
    """

    return listar_versoes_service(
        library_id=library_id,
        include_inactive=include_inactive,
        db=db,
    )


# ============================================================
# VERSÕES - ROBOTS QUE UTILIZAM A LIBRARY
# ============================================================

@router.get(
    "/{library_id}/robots",
    summary="Listar robôs que utilizam a biblioteca",
)
def listar_robos_da_biblioteca(
    library_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Lista os Robots cuja versão atual utiliza esta Library.
    """

    return listar_robos_da_biblioteca_service(
        library_id=library_id,
        db=db,
    )


# ============================================================
# VERSÕES - PUBLICAR ZIP STANDALONE
# ============================================================

@router.post(
    "/{library_id}/versions/upload",
    status_code=status.HTTP_201_CREATED,
)
async def publicar_versao_standalone(
    library_id: int,
    version: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "publish",
        )
    ),
):
    """
    Publica uma nova versão standalone da Library.
    """

    return await publicar_versao_standalone_service(
        library_id=library_id,
        version=version,
        file=file,
        db=db,
        usuario=usuario,
    )


# ============================================================
# SNAPSHOT - ÁRVORE DE ARQUIVOS
# ============================================================

@router.get(
    "/{library_id}/versions/{version_id}/tree"
)
def visualizar_arvore_versao(
    library_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Retorna a árvore do snapshot imutável de uma LibraryVersion.
    """

    return visualizar_arvore_versao_service(
        library_id=library_id,
        version_id=version_id,
        db=db,
    )


# ============================================================
# SNAPSHOT - VISUALIZAR ARQUIVO
# ============================================================

@router.get(
    "/{library_id}/versions/{version_id}/file"
)
def visualizar_arquivo_versao(
    library_id: int,
    version_id: int,
    path: str,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Retorna o conteúdo textual de um arquivo do snapshot publicado.
    """

    return visualizar_arquivo_versao_service(
        library_id=library_id,
        version_id=version_id,
        path=path,
        db=db,
    )


# ============================================================
# SNAPSHOT - DOWNLOAD
# ============================================================

@router.get(
    "/{library_id}/versions/{version_id}/download"
)
def baixar_versao(
    library_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Faz download do ZIP imutável da versão publicada.
    """

    return baixar_versao_service(
        library_id=library_id,
        version_id=version_id,
        db=db,
    )


# ============================================================
# VERSÕES - DESATIVAR
# ============================================================

@router.delete(
    "/{library_id}/versions/{version_id}"
)
def desativar_versao(
    library_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(
        require_permission(
            "Libraries",
            "delete",
        )
    ),
):
    """
    Desativa uma LibraryVersion para novos vínculos.
    """

    return desativar_versao_service(
        library_id=library_id,
        version_id=version_id,
        db=db,
        usuario=usuario,
    )
