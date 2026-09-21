# ============================================================
# API - LIBRARIES
# ============================================================
#
# Router HTTP do domínio de Libraries.
#
# RESPONSABILIDADES DESTE ARQUIVO:
#
# - registrar URLs;
# - declarar métodos HTTP;
# - declarar status codes;
# - aplicar autenticação/RBAC;
# - receber Query / Body / Form / File;
# - delegar regras de negócio aos services.
#
# IMPORTANTE:
#
# Regras de negócio NÃO devem voltar para este arquivo.
#
# Estrutura:
#
# api/libraries.py
#       │
#       ├── libraries/dependencies_service.py
#       ├── libraries/folders_service.py
#       ├── libraries/catalog_service.py
#       ├── libraries/versions_service.py
#       └── libraries/snapshot_service.py
#
# A ordem das rotas é intencional.
# Rotas estáticas ficam antes de /{library_id}.
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
# DEPENDENCIES SERVICES
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
# FOLDERS SERVICES
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
# CATALOG SERVICES
# ============================================================

from libraries.catalog_service import (
    atualizar_biblioteca_service,
    consultar_biblioteca_service,
    criar_biblioteca_service,
    desativar_biblioteca_service,
    listar_bibliotecas_service,
)


# ============================================================
# VERSIONS SERVICES
# ============================================================

from libraries.versions_service import (
    desativar_versao_service,
    listar_robos_da_biblioteca_service,
    listar_versoes_service,
    publicar_versao_standalone_service,
)


# ============================================================
# SNAPSHOT SERVICES
# ============================================================

from libraries.snapshot_service import (
    baixar_versao_service,
    visualizar_arquivo_versao_service,
    visualizar_arvore_versao_service,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/libraries",
    tags=["Libraries"],
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    """
    Cria uma sessão SQLAlchemy por request.

    A sessão é sempre encerrada após o processamento da rota.
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
# IMPORTANTE:
#
# As rotas /projects/... aparecem antes de /{library_id}.
#
# Isso impede que "projects" seja interpretado como library_id.
# ============================================================

@router.get(
    "/projects/{project_id}/dependencies"
)
def listar_dependencias_projeto(
    project_id: int,

    db: Session = Depends(
        get_db
    ),

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
    Lista as LibraryVersions fixadas no projeto.

    Operação somente leitura.
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

    db: Session = Depends(
        get_db
    ),

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
    Retorna o catálogo de Libraries publicadas disponíveis
    para utilização no AutomationProject.
    """

    return listar_bibliotecas_disponiveis_projeto_service(
        project_id=project_id,
        db=db,
    )


# ============================================================
# PROJETOS - ADICIONAR DEPENDÊNCIAS EM LOTE
# ============================================================

@router.post(
    "/projects/{project_id}/dependencies/bulk",
    status_code=status.HTTP_201_CREATED,
)
def adicionar_dependencias_projeto_em_lote(
    project_id: int,

    request: ProjectLibraryDependenciesBulkCreate,

    db: Session = Depends(
        get_db
    ),

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
    Adiciona uma ou várias LibraryVersions ao projeto.

    A atomicidade da operação pertence ao service.
    """

    return adicionar_dependencias_projeto_em_lote_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJETOS - ADICIONAR UMA DEPENDÊNCIA
# ============================================================

@router.post(
    "/projects/{project_id}/dependencies",
    status_code=status.HTTP_201_CREATED,
)
def adicionar_dependencia_projeto(
    project_id: int,

    request: ProjectLibraryDependencyCreate,

    db: Session = Depends(
        get_db
    ),

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
    Adiciona uma versão exata de uma Library ao projeto.
    """

    return adicionar_dependencia_projeto_service(
        project_id=project_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJETOS - TROCAR VERSÃO
# ============================================================

@router.put(
    "/projects/{project_id}/dependencies/{library_id}"
)
def trocar_versao_projeto(
    project_id: int,
    library_id: int,

    request: ProjectLibraryDependencyUpdate,

    db: Session = Depends(
        get_db
    ),

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
    Troca explicitamente a LibraryVersion fixada no projeto.
    """

    return trocar_versao_projeto_service(
        project_id=project_id,
        library_id=library_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PROJETOS - REMOVER DEPENDÊNCIA
# ============================================================

@router.delete(
    "/projects/{project_id}/dependencies/{library_id}"
)
def remover_dependencia_projeto(
    project_id: int,
    library_id: int,

    db: Session = Depends(
        get_db
    ),

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
    Remove a Library da composição do projeto.
    """

    return remover_dependencia_projeto_service(
        project_id=project_id,
        library_id=library_id,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - ÁRVORE GLOBAL
# ============================================================
#
# Esta rota precisa permanecer antes de /{library_id}.
# ============================================================

@router.get(
    "/tree"
)
def obter_arvore_bibliotecas(
    include_inactive: bool = False,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Retorna a árvore organizacional de pastas e Libraries.
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

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Lista as LibraryFolders.
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

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),
):
    """
    Cria uma pasta organizacional no catálogo de Libraries.
    """

    return criar_pasta_bibliotecas_service(
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - ATUALIZAR PASTA
# ============================================================

@router.patch(
    "/folders/{folder_id}"
)
def atualizar_pasta_bibliotecas(
    folder_id: int,

    request: LibraryFolderUpdate,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "edit",
        )
    ),
):
    """
    Atualiza nome e/ou posição de uma LibraryFolder.
    """

    return atualizar_pasta_bibliotecas_service(
        folder_id=folder_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - EXCLUIR PASTA
# ============================================================

@router.delete(
    "/folders/{folder_id}"
)
def excluir_pasta_bibliotecas(
    folder_id: int,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "delete",
        )
    ),
):
    """
    Desativa logicamente uma LibraryFolder.
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

    db: Session = Depends(
        get_db
    ),

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
# CATÁLOGO - LISTAR LIBRARIES
# ============================================================
#
# As duas formas são preservadas:
#
#     GET /libraries
#     GET /libraries/
# ============================================================

@router.get("")
@router.get("/")
def listar_bibliotecas(
    include_inactive: bool = False,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Lista as Libraries cadastradas.
    """

    return listar_bibliotecas_service(
        include_inactive=include_inactive,
        db=db,
    )


# ============================================================
# CATÁLOGO - CRIAR LIBRARY
# ============================================================
#
# Também preservamos as duas formas.
#
# A versão "/" continua fora do OpenAPI.
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

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "create",
        )
    ),
):
    """
    Cria a identidade global de uma Library.
    """

    return criar_biblioteca_service(
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - CONSULTAR LIBRARY
# ============================================================

@router.get(
    "/{library_id}"
)
def consultar_biblioteca(
    library_id: int,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Consulta uma Library específica.
    """

    return consultar_biblioteca_service(
        library_id=library_id,
        db=db,
    )


# ============================================================
# CATÁLOGO - ATUALIZAR LIBRARY
# ============================================================

@router.patch(
    "/{library_id}"
)
def atualizar_biblioteca(
    library_id: int,

    request: LibraryUpdate,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "edit",
        )
    ),
):
    """
    Atualiza os metadados editáveis da Library.
    """

    return atualizar_biblioteca_service(
        library_id=library_id,
        request=request,
        db=db,
        usuario=usuario,
    )


# ============================================================
# CATÁLOGO - DESATIVAR LIBRARY
# ============================================================

@router.delete(
    "/{library_id}"
)
def desativar_biblioteca(
    library_id: int,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "delete",
        )
    ),
):
    """
    Desativa logicamente a Library.

    A proteção contra Robots em Produção está no service.
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

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Lista as LibraryVersions publicadas.
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
    description=(
        "Retorna os Robots atualmente publicados que possuem "
        "esta Library em sua versão atual."
    ),
)
def listar_robos_da_biblioteca(
    library_id: int,

    db: Session = Depends(
        get_db
    ),

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
# VERSÕES - PUBLICAR STANDALONE
# ============================================================

@router.post(
    "/{library_id}/versions/upload",
    status_code=status.HTTP_201_CREATED,
)
async def publicar_versao_standalone(
    library_id: int,

    # A versão continua sendo recebida como multipart/form-data.
    version: str = Form(...),

    # O ZIP continua sendo recebido como UploadFile.
    file: UploadFile = File(...),

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "publish",
        )
    ),
):
    """
    Publica uma nova LibraryVersion standalone.

    O processamento físico e a promoção para Produção pertencem
    ao versions_service.
    """

    return await publicar_versao_standalone_service(
        library_id=library_id,
        version=version,
        file=file,
        db=db,
        usuario=usuario,
    )


# ============================================================
# SNAPSHOT - VISUALIZAR ÁRVORE
# ============================================================

@router.get(
    "/{library_id}/versions/{version_id}/tree"
)
def visualizar_arvore_versao(
    library_id: int,
    version_id: int,

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Retorna a árvore do snapshot imutável publicado.
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

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Retorna o conteúdo textual UTF-8 de um arquivo do snapshot.
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

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "view",
        )
    ),
):
    """
    Baixa o ZIP imutável da LibraryVersion.
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

    db: Session = Depends(
        get_db
    ),

    usuario=Depends(
        require_permission(
            "Libraries",
            "delete",
        )
    ),
):
    """
    Desativa uma LibraryVersion para novos vínculos.

    A versão atualmente vigente em Produção continua protegida
    pelo versions_service.
    """

    return desativar_versao_service(
        library_id=library_id,
        version_id=version_id,
        db=db,
        usuario=usuario,
    )