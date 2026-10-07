# ============================================================
# DUET CORE - LIBRARY CHECKOUT API
# ============================================================
#
# Router fino para o Checkout/Check-in de Libraries realizado
# exclusivamente dentro do contexto de um AutomationProject.
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.permissions import require_permission
from database import SessionLocal

from libraries.checkout_service import (
    consultar_checkout_bibliotecas_projeto_service,
    consultar_historico_checkout_biblioteca_service,
    realizar_checkout_biblioteca_service,
    realizar_checkin_biblioteca_service,
)


router = APIRouter(
    prefix="/development/projects",
    tags=["Library Checkout"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{project_id}/libraries/checkout-overview")
def consultar_checkout_bibliotecas_projeto(
    project_id: int,
    db: Session = Depends(get_db),
    _libraries_view=Depends(
        require_permission("Libraries", "view")
    ),
    usuario=Depends(
        require_permission("Development", "view")
    ),
):
    return consultar_checkout_bibliotecas_projeto_service(
        project_id=project_id,
        db=db,
        usuario=usuario,
    )


@router.post("/{project_id}/libraries/{library_id}/checkout")
def realizar_checkout_biblioteca(
    project_id: int,
    library_id: int,
    db: Session = Depends(get_db),
    _libraries_use=Depends(
        require_permission("Libraries", "use")
    ),
    usuario=Depends(
        require_permission("Development", "edit")
    ),
):
    return realizar_checkout_biblioteca_service(
        project_id=project_id,
        library_id=library_id,
        db=db,
        usuario=usuario,
    )


@router.post("/{project_id}/libraries/{library_id}/checkin")
def realizar_checkin_biblioteca(
    project_id: int,
    library_id: int,
    db: Session = Depends(get_db),
    _libraries_use=Depends(
        require_permission("Libraries", "use")
    ),
    usuario=Depends(
        require_permission("Development", "edit")
    ),
):
    return realizar_checkin_biblioteca_service(
        project_id=project_id,
        library_id=library_id,
        db=db,
        usuario=usuario,
    )


@router.get("/{project_id}/libraries/{library_id}/checkout/history")
def consultar_historico_checkout_biblioteca(
    project_id: int,
    library_id: int,
    db: Session = Depends(get_db),
    _libraries_view=Depends(
        require_permission("Libraries", "view")
    ),
    usuario=Depends(
        require_permission("Development", "view")
    ),
):
    # usuario é exigido para autenticação/RBAC; o histórico em si
    # não precisa alterar dados nem depende de identidade do ator.
    _ = usuario
    return consultar_historico_checkout_biblioteca_service(
        project_id=project_id,
        library_id=library_id,
        db=db,
    )
