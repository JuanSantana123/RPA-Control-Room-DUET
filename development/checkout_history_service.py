# ============================================================
# DEVELOPMENT - CHECKOUT HISTORY SERVICE
# ============================================================
#
# Responsabilidade:
#     manter a trilha funcional e imutável dos eventos de
#     Checkout dos AutomationProjects.
#
# IMPORTANTE:
# - ProjectCheckout representa somente o lock ATUAL;
# - ProjectCheckoutHistory representa o histórico permanente;
# - esta camada NÃO executa commit por conta própria ao registrar
#   eventos, para participar da mesma transação do Checkout/Checkin.
# ============================================================

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    ProjectCheckout,
    ProjectCheckoutHistory,
    User,
)


VALID_EVENT_TYPES = {
    "checkout",
    "checkin",
    "force_release",
}


def _nome_usuario_fallback(
    user_id: int | None,
    user_name: str | None,
) -> str:
    """Garante snapshot textual mesmo se o usuário for removido depois."""

    nome = (user_name or "").strip()
    if nome:
        return nome

    if user_id is not None:
        return f"Usuário #{user_id}"

    return "Usuário desconhecido"


def registrar_evento_checkout(
    *,
    db: Session,
    projeto: AutomationProject,
    event_type: str,
    actor_user_id: int | None,
    actor_user_name: str | None,
    checkout_owner_user_id: int | None,
    checkout_owner_user_name: str | None,
    checkout_started_at: datetime | None,
) -> ProjectCheckoutHistory:
    """
    Adiciona um evento de auditoria à transação atual.

    Não executa commit. O chamador decide quando a mudança do lock
    e o histórico serão confirmados de forma atômica.
    """

    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(
            f"Tipo de evento de Checkout inválido: {event_type}."
        )

    registro = ProjectCheckoutHistory(
        project_id=projeto.id,
        project_name=projeto.name,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_user_name=_nome_usuario_fallback(
            actor_user_id,
            actor_user_name,
        ),
        checkout_owner_user_id=checkout_owner_user_id,
        checkout_owner_user_name=_nome_usuario_fallback(
            checkout_owner_user_id,
            checkout_owner_user_name,
        ),
        checkout_started_at=checkout_started_at,
        occurred_at=datetime.utcnow(),
    )

    db.add(registro)
    return registro


def listar_estados_checkout_service(
    *,
    db: Session,
    usuario,
) -> dict:
    """
    Retorna, em uma única consulta, o estado de Checkout de todos
    os AutomationProjects ativos visíveis na área Desenvolvimento.

    O formato em mapa evita uma requisição HTTP por card.
    """

    registros = (
        db.query(
            AutomationProject,
            ProjectCheckout,
            User.name.label("checkout_user_name"),
        )
        .outerjoin(
            ProjectCheckout,
            ProjectCheckout.project_id == AutomationProject.id,
        )
        .outerjoin(
            User,
            User.id == ProjectCheckout.user_id,
        )
        .filter(
            AutomationProject.is_active == 1,
        )
        .order_by(
            AutomationProject.id.asc(),
        )
        .all()
    )

    projetos: dict[str, dict] = {}

    for projeto, checkout, checkout_user_name in registros:
        if checkout is None:
            projetos[str(projeto.id)] = {
                "project_id": projeto.id,
                "checked_out": False,
                "owns_checkout": False,
                "checkout": None,
            }
            continue

        projetos[str(projeto.id)] = {
            "project_id": projeto.id,
            "checked_out": True,
            "owns_checkout": checkout.user_id == usuario.id,
            "checkout": {
                "id": checkout.id,
                "project_id": checkout.project_id,
                "user_id": checkout.user_id,
                "user_name": checkout_user_name,
                "checked_out_at": (
                    checkout.checked_out_at.isoformat()
                    if checkout.checked_out_at
                    else None
                ),
            },
        }

    return {
        "status": "success",
        "projects": projetos,
    }


def listar_historico_checkout_service(
    *,
    project_id: int,
    db: Session,
) -> dict:
    """Retorna a trilha de Checkout de um AutomationProject ativo."""

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id == project_id,
            AutomationProject.is_active == 1,
        )
        .first()
    )

    if not projeto:
        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    eventos = (
        db.query(ProjectCheckoutHistory)
        .filter(
            ProjectCheckoutHistory.project_id == project_id,
        )
        .order_by(
            ProjectCheckoutHistory.occurred_at.desc(),
            ProjectCheckoutHistory.id.desc(),
        )
        .all()
    )

    return {
        "status": "success",
        "project": {
            "id": projeto.id,
            "name": projeto.name,
        },
        "total": len(eventos),
        "events": [
            {
                "id": evento.id,
                "project_id": evento.project_id,
                "project_name": evento.project_name,
                "event_type": evento.event_type,
                "actor_user_id": evento.actor_user_id,
                "actor_user_name": evento.actor_user_name,
                "checkout_owner_user_id": evento.checkout_owner_user_id,
                "checkout_owner_user_name": evento.checkout_owner_user_name,
                "checkout_started_at": (
                    evento.checkout_started_at.isoformat()
                    if evento.checkout_started_at
                    else None
                ),
                "occurred_at": (
                    evento.occurred_at.isoformat()
                    if evento.occurred_at
                    else None
                ),
            }
            for evento in eventos
        ],
    }
