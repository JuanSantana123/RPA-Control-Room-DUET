# ============================================================
# DUET CORE - API - EXTERNAL IDE
# ============================================================
#
# Router fino. Reutiliza integralmente os services oficiais do
# Workspace para manter Checkout, Libraries e proteções existentes.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.permissions import require_permission
from database import SessionLocal
from development.developer_ide_service import (
    DeveloperIdeContext,
    autenticar_sessao_ide_service,
    criar_abertura_ide_service,
    renovar_sessao_ide_service,
    resgatar_abertura_ide_service,
    revogar_sessao_ide_service,
)
from development.workspace_service import (
    abrir_arquivo_workspace_service,
    criar_arquivo_workspace_service,
    criar_pasta_workspace_service,
    excluir_item_workspace_service,
    listar_workspace_service,
    renomear_item_workspace_service,
    salvar_arquivo_workspace_service,
)
from schemas.developer_ide import DeveloperIdeRedeemRequest
from schemas.development import (
    WorkspaceFileSave,
    WorkspaceItemCreate,
    WorkspaceItemRename,
)


router = APIRouter(
    prefix="/development/external-ide",
    tags=["Development - External IDE"],
)

bridge_bearer = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_developer_ide_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bridge_bearer),
    db: Session = Depends(get_db),
) -> DeveloperIdeContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Sessão da IDE não informada.")

    return autenticar_sessao_ide_service(
        access_token=credentials.credentials,
        db=db,
    )


@router.post("/projects/{project_id}/launch")
def criar_abertura_ide(
    project_id: int,
    db: Session = Depends(get_db),
    _view=Depends(require_permission("Development", "view")),
    _checkout=Depends(require_permission("Development", "checkout")),
    usuario=Depends(require_permission("Development", "edit")),
):
    return criar_abertura_ide_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


@router.post("/redeem")
def resgatar_abertura_ide(
    request: DeveloperIdeRedeemRequest,
    db: Session = Depends(get_db),
):
    return resgatar_abertura_ide_service(
        launch_code=request.launch_code,
        db=db,
    )


@router.get("/workspace/tree")
def listar_workspace_ide(
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return listar_workspace_service(
        project_id=context.projeto.id,
        db=db,
    )


@router.get("/workspace/file")
def abrir_arquivo_workspace_ide(
    path: str = Query(..., min_length=1, max_length=1000),
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return abrir_arquivo_workspace_service(
        project_id=context.projeto.id,
        path=path,
        db=db,
    )


@router.put("/workspace/file")
def salvar_arquivo_workspace_ide(
    request: WorkspaceFileSave,
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return salvar_arquivo_workspace_service(
        project_id=context.projeto.id,
        request=request,
        db=db,
        usuario=context.usuario,
    )


@router.post("/workspace/files")
def criar_arquivo_workspace_ide(
    request: WorkspaceItemCreate,
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return criar_arquivo_workspace_service(
        project_id=context.projeto.id,
        request=request,
        db=db,
        usuario=context.usuario,
    )


@router.post("/workspace/folders")
def criar_pasta_workspace_ide(
    request: WorkspaceItemCreate,
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return criar_pasta_workspace_service(
        project_id=context.projeto.id,
        request=request,
        db=db,
        usuario=context.usuario,
    )


@router.patch("/workspace/item")
def renomear_item_workspace_ide(
    request: WorkspaceItemRename,
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return renomear_item_workspace_service(
        project_id=context.projeto.id,
        request=request,
        db=db,
        usuario=context.usuario,
    )


@router.delete("/workspace/item")
def excluir_item_workspace_ide(
    path: str = Query(..., min_length=1, max_length=1000),
    recursive: bool = Query(False),
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return excluir_item_workspace_service(
        project_id=context.projeto.id,
        path=path,
        recursive=recursive,
        db=db,
        usuario=context.usuario,
    )


@router.get("/session")
def consultar_sessao_ide(
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
):
    return {
        "status": "success",
        "project": {
            "id": context.projeto.id,
            "name": context.projeto.name,
        },
        "user": {
            "id": context.usuario.id,
            "name": context.usuario.name,
            "username": context.usuario.username,
        },
        "expires_at": (
            context.session.expires_at.isoformat()
            if context.session.expires_at
            else None
        ),
    }



@router.post("/session/renew")
def renovar_sessao_ide(
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    """
    Prolonga uma sessão válida do Developer Bridge.

    A própria dependência get_developer_ide_context garante que usuário,
    projeto, permissões e Checkout continuam válidos antes da renovação.
    """

    return renovar_sessao_ide_service(
        context=context,
        db=db,
    )


@router.delete("/session")
def revogar_sessao_ide(
    context: DeveloperIdeContext = Depends(get_developer_ide_context),
    db: Session = Depends(get_db),
):
    return revogar_sessao_ide_service(
        context=context,
        db=db,
    )
