# ============================================================
# DUET CORE - API - DEVELOPMENT PROJECT ENTRYPOINT
# ============================================================
# Router fino: autenticação/RBAC HTTP e delegação ao service.
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.permissions import require_permission
from database import SessionLocal
from development.entrypoint_service import (
    atualizar_entrypoint_projeto_service,
    consultar_entrypoint_projeto_service,
)
from schemas.development_entrypoint import ProjectEntrypointUpdate


router = APIRouter(
    prefix="/development",
    tags=["Development - Project Entrypoint"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/projects/{project_id}/entrypoint")
def consultar_entrypoint_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_permission("Development", "view")),
):
    return consultar_entrypoint_projeto_service(
        project_id=project_id,
        db=db,
    )


@router.put("/projects/{project_id}/entrypoint")
def atualizar_entrypoint_projeto(
    project_id: int,
    request: ProjectEntrypointUpdate,
    db: Session = Depends(get_db),
    _checkout_permission=Depends(
        require_permission("Development", "checkout")
    ),
    usuario=Depends(require_permission("Development", "edit")),
):
    return atualizar_entrypoint_projeto_service(
        project_id=project_id,
        entrypoint_path=request.entrypoint_path,
        db=db,
        usuario=usuario,
    )
