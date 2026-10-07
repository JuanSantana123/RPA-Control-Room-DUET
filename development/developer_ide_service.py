# ============================================================
# DUET CORE - DEVELOPMENT - EXTERNAL IDE SERVICE
# ============================================================
#
# Responsabilidade:
# - emitir códigos temporários de abertura;
# - trocar o código por sessão restrita ao projeto;
# - autenticar o DUET Developer Bridge;
# - renovar sessões ativas sem interromper desenvolvimento longo;
# - preservar RBAC e Checkout existentes.
# ============================================================

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from auth.permissions import usuario_tem_permissao
from development.checkout_service import (
    exigir_checkout_workspace,
)
from models import AutomationProject, DeveloperIdeSession, User


LAUNCH_TTL_SECONDS = 90
SESSION_TTL_HOURS = 8
LAST_SEEN_WRITE_INTERVAL_SECONDS = 60


@dataclass(frozen=True)
class DeveloperIdeContext:
    """Contexto autenticado usado apenas pelas rotas do Bridge."""

    session: DeveloperIdeSession
    usuario: User
    projeto: AutomationProject


def _hash_secret(value: str) -> str:
    """Persiste somente SHA-256; o segredo original nunca vai ao banco."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_active_user(db: Session, user_id: int) -> User:
    usuario = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active == 1,
        )
        .first()
    )

    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Usuário da sessão de IDE não está ativo.",
        )

    return usuario


def _require_active_project(
    db: Session,
    project_id: int,
) -> AutomationProject:
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
            detail="Projeto de Desenvolvimento não encontrado.",
        )

    return projeto


def _require_external_ide_permissions(
    db: Session,
    usuario: User,
) -> None:
    """A IDE externa exige view + edit + checkout."""

    for action in ("view", "edit", "checkout"):
        if not usuario_tem_permissao(
            usuario,
            db,
            "Development",
            action,
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Usuário sem permissão para utilizar "
                    "a edição por IDE externa."
                ),
            )


def criar_abertura_ide_service(
    project_id: int,
    db: Session,
    usuario: User,
) -> dict:
    """Cria launch_code somente quando o usuário já possui o Checkout."""

    projeto = _require_active_project(db, project_id)
    _require_external_ide_permissions(db, usuario)

    # DUET_EXTERNAL_IDE_REQUIRE_OWN_CHECKOUT_V1
    # A IDE externa NÃO adquire Checkout automaticamente.
    # O usuário precisa reservar explicitamente o projeto antes
    # de abrir qualquer ambiente externo com capacidade de escrita.
    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    now = datetime.utcnow()

    # Revoga somente códigos ainda não resgatados do mesmo usuário/projeto.
    (
        db.query(DeveloperIdeSession)
        .filter(
            DeveloperIdeSession.project_id == project_id,
            DeveloperIdeSession.user_id == usuario.id,
            DeveloperIdeSession.redeemed_at.is_(None),
            DeveloperIdeSession.revoked.is_(False),
        )
        .update(
            {DeveloperIdeSession.revoked: True},
            synchronize_session=False,
        )
    )

    launch_code = secrets.token_urlsafe(48)

    sessao = DeveloperIdeSession(
        project_id=project_id,
        user_id=usuario.id,
        launch_code_hash=_hash_secret(launch_code),
        launch_expires_at=(
            now + timedelta(seconds=LAUNCH_TTL_SECONDS)
        ),
        revoked=False,
        created_at=now,
    )

    db.add(sessao)
    db.commit()

    return {
        "status": "success",
        "project": {
            "id": projeto.id,
            "name": projeto.name,
        },
        "launch_code": launch_code,
        "launch_expires_at": sessao.launch_expires_at.isoformat(),
    }


def resgatar_abertura_ide_service(
    launch_code: str,
    db: Session,
) -> dict:
    """Troca launch_code por token restrito ao projeto."""

    now = datetime.utcnow()

    sessao = (
        db.query(DeveloperIdeSession)
        .filter(
            DeveloperIdeSession.launch_code_hash
            == _hash_secret(launch_code)
        )
        .with_for_update()
        .first()
    )

    if not sessao:
        raise HTTPException(401, "Código de abertura da IDE inválido.")

    if sessao.revoked:
        raise HTTPException(401, "Código de abertura da IDE revogado.")

    if sessao.redeemed_at is not None:
        raise HTTPException(401, "Código de abertura da IDE já utilizado.")

    if sessao.launch_expires_at <= now:
        raise HTTPException(401, "Código de abertura da IDE expirou.")

    usuario = _require_active_user(db, sessao.user_id)
    projeto = _require_active_project(db, sessao.project_id)
    _require_external_ide_permissions(db, usuario)

    exigir_checkout_workspace(
        project_id=projeto.id,
        user_id=usuario.id,
        db=db,
    )

    access_token = secrets.token_urlsafe(64)

    sessao.access_token_hash = _hash_secret(access_token)
    sessao.redeemed_at = now
    sessao.expires_at = now + timedelta(hours=SESSION_TTL_HOURS)
    sessao.last_seen_at = now

    db.commit()

    return {
        "status": "success",
        "token_type": "bearer",
        "access_token": access_token,
        "expires_at": sessao.expires_at.isoformat(),
        "project": {
            "id": projeto.id,
            "name": projeto.name,
        },
    }


def autenticar_sessao_ide_service(
    access_token: str,
    db: Session,
) -> DeveloperIdeContext:
    """Autentica token exclusivo das rotas /development/external-ide."""

    if not access_token:
        raise HTTPException(401, "Token da IDE não informado.")

    now = datetime.utcnow()

    sessao = (
        db.query(DeveloperIdeSession)
        .filter(
            DeveloperIdeSession.access_token_hash
            == _hash_secret(access_token),
            DeveloperIdeSession.revoked.is_(False),
        )
        .first()
    )

    if not sessao:
        raise HTTPException(401, "Sessão da IDE inválida.")

    if sessao.expires_at is None or sessao.expires_at <= now:
        raise HTTPException(401, "Sessão da IDE expirada.")

    usuario = _require_active_user(db, sessao.user_id)
    projeto = _require_active_project(db, sessao.project_id)
    _require_external_ide_permissions(db, usuario)

    # Checkin/Force Release invalida imediatamente a capacidade de escrita.
    exigir_checkout_workspace(
        project_id=projeto.id,
        user_id=usuario.id,
        db=db,
    )

    should_touch = (
        sessao.last_seen_at is None
        or (now - sessao.last_seen_at).total_seconds()
        >= LAST_SEEN_WRITE_INTERVAL_SECONDS
    )

    if should_touch:
        sessao.last_seen_at = now
        db.commit()

    return DeveloperIdeContext(
        session=sessao,
        usuario=usuario,
        projeto=projeto,
    )



def renovar_sessao_ide_service(
    context: DeveloperIdeContext,
    db: Session,
) -> dict:
    """
    Renova a validade de uma sessão já autenticada da IDE externa.

    A renovação NÃO cria um token novo nesta etapa.

    Motivo:
        rotacionar o token sem um refresh token separado cria uma janela
        em que o servidor pode persistir o token novo, a resposta se perder
        na rede e o Bridge ficar apenas com o token antigo.

    Segurança preservada:
        - autenticar_sessao_ide_service já validou a sessão atual;
        - usuário ativo é revalidado;
        - permissões view/edit/checkout são revalidadas;
        - Checkout oficial do projeto é revalidado;
        - uma sessão revogada ou expirada não chega até este service.

    O resultado é um TTL deslizante: enquanto o Developer Bridge estiver
    ativo e autorizado, ele pode continuar trabalhando por muitas horas
    sem perder a sincronização por um timeout arbitrário.
    """

    now = datetime.utcnow()

    # Revalida explicitamente os requisitos de autorização porque este
    # ponto prolonga a vida útil da sessão.
    usuario = _require_active_user(
        db,
        context.usuario.id,
    )

    projeto = _require_active_project(
        db,
        context.projeto.id,
    )

    _require_external_ide_permissions(
        db,
        usuario,
    )

    exigir_checkout_workspace(
        project_id=projeto.id,
        user_id=usuario.id,
        db=db,
    )

    context.session.expires_at = (
        now
        + timedelta(
            hours=SESSION_TTL_HOURS,
        )
    )

    context.session.last_seen_at = now

    db.commit()
    db.refresh(
        context.session
    )

    return {
        "status": "success",
        "expires_at": (
            context.session.expires_at.isoformat()
            if context.session.expires_at
            else None
        ),
        "project": {
            "id": projeto.id,
            "name": projeto.name,
        },
    }


def revogar_sessao_ide_service(
    context: DeveloperIdeContext,
    db: Session,
) -> dict:
    context.session.revoked = True
    db.commit()

    return {
        "status": "success",
        "message": "Sessão da IDE revogada.",
    }
