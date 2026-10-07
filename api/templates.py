# ============================================================
# AUTOMATION TEMPLATES API
# ============================================================
#
# Endpoints responsáveis pelo catálogo versionado de Templates.
#
# Nesta primeira versão:
#
# - Templates recebem ZIP completo do projeto-base;
# - cada novo upload gera versão inteira e imutável;
# - a versão recém-publicada passa a ser a versão atual;
# - versões anteriores permanecem disponíveis para histórico;
# - novos projetos podem escolher uma versão específica;
# - projetos já criados nunca são sobrescritos por versões futuras.
# ============================================================

import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import ValidationError
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth.permissions import (
    require_permission,
)
from database import (
    SessionLocal,
)

from schemas.templates import (
    AutomationTemplateUpdate,
    TemplateLibrariesUpdate,
    TemplateProjectCreate,
)

from automation_templates.service import (
    atualizar_template_service,
    criar_template_service,
    definir_versao_atual_service,
    listar_templates_disponiveis_service,
    listar_templates_service,
    obter_download_template_version_service,
    publicar_nova_versao_template_service,
)

from automation_templates.template_libraries_service import (
    atualizar_bibliotecas_template_service,
    listar_bibliotecas_template_version_service,
)

from development.projects_service import (
    criar_projeto_service,
)


# ============================================================
# BANCO
# ============================================================

def get_db():
    """
    Abre uma sessão SQLAlchemy por requisição.
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
    prefix="/templates",
    tags=["Templates"],
)


# ============================================================
# PARSER DE LIBRARIES EM MULTIPART/FORM-DATA
# ============================================================

def _parse_template_libraries_form(
    raw_libraries: str | None,
) -> list[dict] | None:
    """
    Converte o campo opcional `libraries` recebido em multipart/form-data.

    Contrato do campo:

        libraries = JSON.stringify([
            {
                "library_id": 16,
                "library_version_id": 14,
            }
        ])

    Semântica importante:

    - campo ausente -> None;
    - [] explícito -> composição vazia;
    - lista preenchida -> composição exata solicitada.

    A validação estrutural reutiliza TemplateLibrariesUpdate para não
    duplicar o contrato Pydantic já utilizado pelo endpoint JSON.
    """

    if raw_libraries is None:
        return None

    try:
        decoded = json.loads(
            raw_libraries
        )
    except (TypeError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=422,
            detail=(
                "O campo libraries deve conter um JSON válido."
            ),
        ) from error

    try:
        request = (
            TemplateLibrariesUpdate.model_validate(
                {
                    "libraries": decoded,
                }
            )
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail=(
                "A composição de Libraries informada é inválida."
            ),
        ) from error

    return [
        item.model_dump()
        for item in request.libraries
    ]


# ============================================================
# DISPONÍVEIS PARA NOVOS PROJETOS
# ============================================================

@router.get(
    "/available",
)
def listar_templates_disponiveis(
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Development",
            "create",
        )
    ),
):
    """
    Retorna Templates ativos que possuem uma versão atual.

    O frontend utiliza esta rota somente na criação de um
    AutomationProject.
    """

    return (
        listar_templates_disponiveis_service(
            db
        )
    )


# ============================================================
# CRIAR PROJETO A PARTIR DE TEMPLATE
# ============================================================

@router.post(
    "/projects",
    status_code=
        status.HTTP_201_CREATED,
)
def criar_projeto_a_partir_template(
    request: TemplateProjectCreate,
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Development",
            "create",
        )
    ),
):
    """
    Cria um AutomationProject copiando uma versão exata do Template.

    O ZIP é utilizado somente durante a criação.
    Depois disso o Workspace do projeto é independente.
    """

    return criar_projeto_service(
        request=request,
        db=db,
        usuario=usuario,
        template_version_id=
            request.template_version_id,
    )


# ============================================================
# LISTAR CATÁLOGO
# ============================================================

@router.get(
    "",
)
@router.get(
    "/",
    include_in_schema=False,
)
def listar_templates(
    include_inactive: bool = False,
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "view",
        )
    ),
):
    """
    Lista Templates e histórico de versões.
    """

    return listar_templates_service(
        db,
        include_inactive=
            include_inactive,
    )


# ============================================================
# CRIAR TEMPLATE + VERSÃO 1
# ============================================================

@router.post(
    "",
    status_code=
        status.HTTP_201_CREATED,
)
@router.post(
    "/",
    status_code=
        status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def criar_template(
    name: str = Form(...),
    description: str | None = Form(
        default=None
    ),
    libraries: str | None = Form(
        default=None
    ),
    file: UploadFile = File(...),
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "create",
        )
    ),
):
    """
    Cadastra um novo Template.

    O primeiro ZIP enviado se torna automaticamente a versão v1
    e a versão atual.
    """

    library_selections = (
        _parse_template_libraries_form(
            libraries
        )
    )

    return await criar_template_service(
        name=name,
        description=description,
        file=file,
        libraries=library_selections,
        db=db,
        usuario=usuario,
    )


# ============================================================
# BIBLIOTECAS DO TEMPLATE
# ============================================================

@router.get(
    "/{template_id}/versions/"
    "{version_id}/libraries",
)
def listar_bibliotecas_template_version(
    template_id: int,
    version_id: int,
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "view",
        )
    ),
):
    """
    Lista o snapshot de Libraries de uma versão específica
    do Template.
    """

    return (
        listar_bibliotecas_template_version_service(
            template_id=
                template_id,
            version_id=
                version_id,
            db=db,
        )
    )


@router.put(
    "/{template_id}/libraries",
    status_code=
        status.HTTP_201_CREATED,
)
def atualizar_bibliotecas_template(
    template_id: int,
    request: TemplateLibrariesUpdate,
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "publish",
        )
    ),
):
    """
    Cria uma NOVA versão do Template com a composição completa
    de Libraries informada.

    A versão atual nunca é alterada.
    """

    return (
        atualizar_bibliotecas_template_service(
            template_id=
                template_id,
            libraries=[
                item.model_dump()
                for item in request.libraries
            ],
            db=db,
            usuario=usuario,
        )
    )


# ============================================================
# ATUALIZAR METADADOS
# ============================================================

@router.patch(
    "/{template_id}",
)
def atualizar_template(
    template_id: int,
    request: AutomationTemplateUpdate,
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "edit",
        )
    ),
):
    """
    Atualiza nome, descrição ou disponibilidade.

    O código do Template não é alterado aqui.
    """

    return atualizar_template_service(
        template_id=
            template_id,
        name=request.name,
        description=
            request.description,
        is_active=
            request.is_active,
        db=db,
        usuario=usuario,
    )


# ============================================================
# PUBLICAR NOVA VERSÃO
# ============================================================

@router.post(
    "/{template_id}/versions",
    status_code=
        status.HTTP_201_CREATED,
)
async def publicar_nova_versao(
    template_id: int,
    libraries: str | None = Form(
        default=None
    ),
    file: UploadFile = File(...),
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "publish",
        )
    ),
):
    """
    Publica o ZIP completo da próxima versão.

    O número é incrementado automaticamente e a nova versão passa
    a ser a versão atual do Template.
    """

    library_selections = (
        _parse_template_libraries_form(
            libraries
        )
    )

    return await (
        publicar_nova_versao_template_service(
            template_id=
                template_id,
            file=file,
            libraries=library_selections,
            db=db,
            usuario=usuario,
        )
    )


# ============================================================
# DEFINIR VERSÃO ATUAL
# ============================================================

@router.post(
    "/{template_id}/versions/"
    "{version_id}/set-current",
)
def definir_versao_atual(
    template_id: int,
    version_id: int,
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "set_current",
        )
    ),
):
    """
    Torna uma versão histórica novamente a versão atual.

    Nenhuma versão é apagada.
    """

    return definir_versao_atual_service(
        template_id=
            template_id,
        version_id=
            version_id,
        db=db,
        usuario=usuario,
    )


# ============================================================
# DOWNLOAD DE VERSÃO
# ============================================================

@router.get(
    "/{template_id}/versions/"
    "{version_id}/download",
)
def baixar_versao_template(
    template_id: int,
    version_id: int,
    db: Session = Depends(
        get_db
    ),
    usuario=Depends(
        require_permission(
            "Templates",
            "download",
        )
    ),
):
    """
    Baixa exatamente o ZIP de uma versão.

    Esta rota permite que quem for evoluir um Template parta
    explicitamente da versão publicada correta.
    """

    artifact_path, download_name = (
        obter_download_template_version_service(
            template_id=
                template_id,
            version_id=
                version_id,
            db=db,
        )
    )

    return FileResponse(
        path=
            str(
                artifact_path
            ),
        media_type=
            "application/zip",
        filename=
            download_name,
    )
