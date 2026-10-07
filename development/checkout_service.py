# ============================================================
# DEVELOPMENT - CHECKOUT SERVICE
# ============================================================
#
# Responsável pelo controle de exclusividade de edição dos
# AutomationProjects.
#
# Este módulo concentra:
#
# - consulta do estado atual do Checkout;
# - aquisição de Checkout;
# - Checkin;
# - Force Release;
# - proteção de escrita do Workspace.
#
# REGRA CENTRAL:
#
# Um projeto pode possuir somente um Checkout ativo.
#
# O Checkout pertence ao usuário, e não à sessão, navegador
# ou máquina.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - utiliza Depends;
# - realiza autenticação;
# - aplica RBAC.
#
# A camada HTTP permanece em:
#
#     api/development.py
# ============================================================


import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    DeveloperIdeSession,
    ProjectCheckout,
    User,
)

from development.serializers import (
    serializar_checkout,
)


# DUET_PROJECT_CHECKOUT_V22_20261002:CHECKOUT_HISTORY
from development.checkout_history_service import (
    registrar_evento_checkout,
)

from development.checkout_observability import (
    registrar_checkout_ocupado,
    registrar_conflito_corrida_checkout,
    registrar_falha_checkout_projeto,
    registrar_falha_checkin_projeto,
    registrar_falha_force_release_checkout,
)
# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# SESSÕES DE IDE VINCULADAS AO CHECKOUT
# ============================================================

def _revogar_sessoes_ide_projeto(
    *,
    project_id: int,
    db: Session,
) -> int:
    """
    Revoga sessões do Developer Bridge vinculadas ao projeto.

    A sessão da IDE representa capacidade de escrita remota. Ela não
    pode sobreviver ao ciclo do Checkout que a autorizou.

    Esta função NÃO executa commit. A revogação participa da mesma
    transação da aquisição/liberação do Checkout.
    """

    return (
        db.query(DeveloperIdeSession)
        .filter(
            DeveloperIdeSession.project_id == project_id,
            DeveloperIdeSession.revoked.is_(False),
        )
        .update(
            {DeveloperIdeSession.revoked: True},
            synchronize_session=False,
        )
    )


# ============================================================
# PROTEÇÃO DE ESCRITA DO WORKSPACE
# ============================================================

def exigir_checkout_workspace(
    project_id: int,
    user_id: int,
    db: Session,
) -> ProjectCheckout:
    """
    Garante que o usuário atual possua o Checkout exclusivo
    do projeto antes de permitir alteração no Workspace.

    Parâmetros:
        project_id:
            ID do projeto que terá seu Workspace alterado.

        user_id:
            ID do usuário autenticado.

        db:
            Sessão SQLAlchemy.

    Retorno:
        ProjectCheckout pertencente ao usuário atual.

    Regras:
        - leitura do Workspace não passa por esta função;
        - projeto sem Checkout -> HTTP 423;
        - Checkout de outro usuário -> HTTP 423;
        - somente o proprietário pode escrever.
    """

    checkout = (
        db.query(ProjectCheckout)
        .filter(
            ProjectCheckout.project_id ==
                project_id
        )
        .first()
    )

    # ========================================================
    # PROJETO SEM CHECKOUT
    # ========================================================

    if not checkout:

        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "É necessário realizar Checkout "
                    "antes de alterar o Workspace."
                ),
                "checkout_user_id": None,
                "checkout_user_name": None,
            },
        )

    # ========================================================
    # CHECKOUT DE OUTRO USUÁRIO
    # ========================================================

    if checkout.user_id != user_id:

        checkout_user = (
            db.query(User)
            .filter(
                User.id ==
                    checkout.user_id
            )
            .first()
        )

        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "O projeto está em Checkout "
                    "por outro usuário."
                ),
                "checkout_user_id":
                    checkout.user_id,
                "checkout_user_name": (
                    checkout_user.name
                    if checkout_user
                    else None
                ),
            },
        )

    # O usuário autenticado é o proprietário.
    return checkout


# ============================================================
# CONSULTAR CHECKOUT
# ============================================================

def consultar_checkout_projeto_service(
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Retorna o estado atual do Checkout de um projeto.

    Retorna também owns_checkout para permitir ao Studio
    determinar se o usuário atual possui direito de edição.
    """

    # ========================================================
    # PROJETO
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id,

            AutomationProject.is_active == 1,
        )
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT ATUAL + NOME DO USUÁRIO
    # ========================================================

    registro = (
        db.query(
            ProjectCheckout,

            User.name.label(
                "checkout_user_name"
            ),
        )
        .join(
            User,
            User.id ==
                ProjectCheckout.user_id,
        )
        .filter(
            ProjectCheckout.project_id ==
                project_id
        )
        .first()
    )

    # ========================================================
    # PROJETO LIVRE
    # ========================================================

    if not registro:

        return {
            "status": "success",
            "project_id": project_id,
            "checked_out": False,
            "owns_checkout": False,
            "checkout": None,
        }

    checkout, checkout_user_name = (
        registro
    )

    # ========================================================
    # PROJETO COM CHECKOUT
    # ========================================================

    return {
        "status": "success",
        "project_id": project_id,
        "checked_out": True,

        "owns_checkout": (
            checkout.user_id ==
                usuario.id
        ),

        "checkout":
            serializar_checkout(
                checkout,
                checkout_user_name,
            ),
    }


# ============================================================
# REALIZAR CHECKOUT
# ============================================================

def realizar_checkout_projeto_service(
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Reserva exclusivamente um AutomationProject para o
    usuário autenticado.

    A operação é idempotente para o proprietário atual.

    Se duas requisições concorrentes tentarem adquirir o
    projeto, a restrição UNIQUE(project_id) do banco decide
    qual requisição vence.
    """

    # ========================================================
    # PROJETO
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id,

            AutomationProject.is_active == 1,
        )
        .with_for_update()
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT EXISTENTE
    # ========================================================

    checkout_existente = (
        db.query(ProjectCheckout)
        .filter(
            ProjectCheckout.project_id ==
                project_id
        )
        .first()
    )

    if checkout_existente:

        # ----------------------------------------------------
        # IDEMPOTÊNCIA
        # ----------------------------------------------------
        #
        # Se o próprio usuário já possui o Checkout, repetir
        # a operação continua sendo sucesso.
        # ----------------------------------------------------

        if (
            checkout_existente.user_id ==
                usuario.id
        ):

            return {
                "status": "success",
                "message": (
                    "Você já possui o Checkout "
                    "deste projeto."
                ),
                "already_owned": True,
                "checkout":
                    serializar_checkout(
                        checkout_existente,
                        usuario.name,
                    ),
            }

        # ----------------------------------------------------
        # CHECKOUT DE OUTRO USUÁRIO
        # ----------------------------------------------------

        checkout_user = (
            db.query(User)
            .filter(
                User.id ==
                    checkout_existente.user_id
            )
            .first()
        )
        registrar_checkout_ocupado(
            project_id=project_id,
            actor_user_id=usuario.id,
            owner_user_id=checkout_existente.user_id,
        )

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "O projeto já possui "
                    "um Checkout ativo."
                ),
                "checkout_user_id":
                    checkout_existente.user_id,
                "checkout_user_name": (
                    checkout_user.name
                    if checkout_user
                    else None
                ),
            },
        )

    # ========================================================
    # CRIA CHECKOUT
    # ========================================================

    checkout = ProjectCheckout(
        project_id=project_id,
        user_id=usuario.id,

        # Mantemos explicitamente o instante da aquisição.
        checked_out_at=datetime.utcnow(),
    )

    try:

        # Um novo Checkout inicia um novo ciclo de edição.
        # Sessões antigas da IDE não podem voltar a ganhar escrita
        # apenas porque o mesmo usuário adquiriu o projeto novamente.
        _revogar_sessoes_ide_projeto(
            project_id=project_id,
            db=db,
        )

        db.add(
            checkout
        )

        registrar_evento_checkout(
            db=db,
            projeto=projeto,
            event_type="checkout",
            actor_user_id=usuario.id,
            actor_user_name=usuario.name,
            checkout_owner_user_id=usuario.id,
            checkout_owner_user_name=usuario.name,
            checkout_started_at=checkout.checked_out_at,
        )

        db.commit()

        db.refresh(
            checkout
        )

    # ========================================================
    # CONCORRÊNCIA
    # ========================================================

    except IntegrityError:

        # Outra requisição pode ter criado o Checkout entre
        # nossa consulta inicial e o INSERT.
        db.rollback()

        checkout_atual = (
            db.query(ProjectCheckout)
            .filter(
                ProjectCheckout.project_id ==
                    project_id
            )
            .first()
        )

        # ----------------------------------------------------
        # O PRÓPRIO USUÁRIO VENCEU EM OUTRA REQUISIÇÃO
        # ----------------------------------------------------

        if (
            checkout_atual
            and checkout_atual.user_id ==
                usuario.id
        ):

            return {
                "status": "success",
                "message": (
                    "Você já possui o Checkout "
                    "deste projeto."
                ),
                "already_owned": True,
                "checkout":
                    serializar_checkout(
                        checkout_atual,
                        usuario.name,
                    ),
            }

        # ----------------------------------------------------
        # OUTRO USUÁRIO VENCEU
        # ----------------------------------------------------

        checkout_user = None

        if checkout_atual:

            checkout_user = (
                db.query(User)
                .filter(
                    User.id ==
                        checkout_atual.user_id
                )
                .first()
            )

        registrar_conflito_corrida_checkout(
            project_id=project_id,
            actor_user_id=usuario.id,
            owner_user_id=(
                checkout_atual.user_id
                if checkout_atual
                else None
            ),
        )

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Outro usuário adquiriu o "
                    "Checkout deste projeto."
                ),
                "checkout_user_id": (
                    checkout_atual.user_id
                    if checkout_atual
                    else None
                ),
                "checkout_user_name": (
                    checkout_user.name
                    if checkout_user
                    else None
                ),
            },
        )

    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception as error:

        db.rollback()

        registrar_falha_checkout_projeto(
            project_id=project_id,
            user_id=usuario.id,
            error=error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível realizar "
                "o Checkout do projeto."
            ),
        )

    # ========================================================
    # AUDITORIA
    # ========================================================

    logger.info(
        "Checkout de projeto realizado",
        extra={
            "event":
                "automation_project_checked_out",

            "user_id":
                usuario.id,

            "project_id":
                project_id,

            "status":
                "success",
        },
    )

    return {
        "status": "success",
        "message":
            "Checkout realizado com sucesso.",
        "already_owned": False,

        "checkout":
            serializar_checkout(
                checkout,
                usuario.name,
            ),
    }


# ============================================================
# REALIZAR CHECKIN
# ============================================================

def realizar_checkin_projeto_service(
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Libera o Checkout do próprio usuário.

    Somente o proprietário atual pode executar Checkin
    normal.

    A remoção administrativa do Checkout de outra pessoa
    pertence ao fluxo de Force Release.
    """

    # ========================================================
    # PROJETO
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id,

            AutomationProject.is_active == 1,
        )
        .with_for_update()
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT
    # ========================================================

    checkout = (
        db.query(ProjectCheckout)
        .filter(
            ProjectCheckout.project_id ==
                project_id
        )
        .first()
    )

    if not checkout:

        raise HTTPException(
            status_code=409,
            detail=(
                "O projeto não possui "
                "Checkout ativo."
            ),
        )

    # ========================================================
    # PROPRIEDADE
    # ========================================================

    if (
        checkout.user_id !=
            usuario.id
    ):

        raise HTTPException(
            status_code=423,
            detail=(
                "O Checkout pertence a outro usuário."
            ),
        )

    # Guardamos o instante antes de excluir o registro para
    # utilização na auditoria.
    # DUET_LIBRARY_CHECKOUT_V1:PROJECT_CHECKIN_GUARD
    # O projeto não pode liberar seu Checkout enquanto possuir
    # Checkout de Library ativo neste mesmo contexto.
    from libraries.checkout_service import (
        possui_checkout_biblioteca_ativo_no_projeto,
    )

    if possui_checkout_biblioteca_ativo_no_projeto(
        db=db,
        project_id=project_id,
        user_id=usuario.id,
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Faça Check-in das bibliotecas em edição antes "
                "de liberar o Checkout do projeto."
            ),
        )

    checked_out_at = (
        checkout.checked_out_at
    )

    try:

        # Checkin encerra também qualquer capacidade de escrita
        # concedida anteriormente ao Developer Bridge.
        _revogar_sessoes_ide_projeto(
            project_id=project_id,
            db=db,
        )

        registrar_evento_checkout(
            db=db,
            projeto=projeto,
            event_type="checkin",
            actor_user_id=usuario.id,
            actor_user_name=usuario.name,
            checkout_owner_user_id=checkout.user_id,
            checkout_owner_user_name=usuario.name,
            checkout_started_at=checked_out_at,
        )

        db.delete(
            checkout
        )

        db.commit()

    except Exception as error:

        db.rollback()

        registrar_falha_checkin_projeto(
            project_id=project_id,
            user_id=usuario.id,
            error=error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível realizar "
                "o Checkin do projeto."
            ),
        )

    # ========================================================
    # AUDITORIA
    # ========================================================

    logger.info(
        "Checkin de projeto realizado",
        extra={
            "event":
                "automation_project_checked_in",

            "user_id":
                usuario.id,

            "project_id":
                project_id,

            "checked_out_at": (
                checked_out_at.isoformat()
                if checked_out_at
                else None
            ),

            "status":
                "success",
        },
    )

    return {
        "status": "success",
        "message":
            "Checkin realizado com sucesso.",
        "project_id":
            project_id,
    }


# ============================================================
# FORCE RELEASE
# ============================================================

def force_release_checkout_projeto_service(
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Remove administrativamente o Checkout atual.

    A permissão:

        Development:force_checkout_release

    continua sendo exigida pela camada HTTP.

    Este evento é registrado separadamente de um Checkin
    normal para preservar a auditoria.
    """

    # ========================================================
    # PROJETO
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id,

            AutomationProject.is_active == 1,
        )
        .with_for_update()
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT ATUAL
    # ========================================================

    checkout = (
        db.query(ProjectCheckout)
        .filter(
            ProjectCheckout.project_id ==
                project_id
        )
        .first()
    )

    if not checkout:

        raise HTTPException(
            status_code=409,
            detail=(
                "O projeto não possui "
                "Checkout ativo."
            ),
        )

    # ========================================================
    # DADOS PARA RETORNO E AUDITORIA
    # ========================================================
    #
    # Precisamos capturá-los antes de excluir o registro.
    # ========================================================

    checkout_user_id = (
        checkout.user_id
    )

    checked_out_at = (
        checkout.checked_out_at
    )

    checkout_user = (
        db.query(User)
        .filter(
            User.id ==
                checkout_user_id
        )
        .first()
    )

    checkout_user_name = (
        checkout_user.name
        if checkout_user
        else None
    )

    # ========================================================
    # EXCLUSÃO DO CHECKOUT
    # ========================================================

    try:

        # Force Release precisa invalidar imediatamente qualquer
        # sessão externa ligada ao Checkout que está sendo removido.
        _revogar_sessoes_ide_projeto(
            project_id=project_id,
            db=db,
        )

        registrar_evento_checkout(
            db=db,
            projeto=projeto,
            event_type="force_release",
            actor_user_id=usuario.id,
            actor_user_name=usuario.name,
            checkout_owner_user_id=checkout_user_id,
            checkout_owner_user_name=checkout_user_name,
            checkout_started_at=checked_out_at,
        )

        db.delete(
            checkout
        )

        db.commit()

    except Exception as error:

        db.rollback()

        registrar_falha_force_release_checkout(
            project_id=project_id,
            user_id=usuario.id,
            error=error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível executar "
                "o Force Release."
            ),
        )

    # ========================================================
    # AUDITORIA
    # ========================================================
    #
    # O evento registra separadamente:
    #
    # - quem possuía o Checkout;
    # - quem executou o Force Release.
    # ========================================================

    logger.info(
        "Force Release de Checkout realizado",
        extra={
            "event":
                "automation_project_checkout_force_released",

            "user_id":
                usuario.id,

            "project_id":
                project_id,

            "checkout_user_id":
                checkout_user_id,

            "checkout_user_name":
                checkout_user_name,

            "checked_out_at": (
                checked_out_at.isoformat()
                if checked_out_at
                else None
            ),

            "status":
                "success",
        },
    )

    return {
        "status": "success",
        "message":
            "Checkout liberado por Force Release.",

        "project_id":
            project_id,

        "released_checkout": {
            "user_id":
                checkout_user_id,

            "user_name":
                checkout_user_name,

            "checked_out_at": (
                checked_out_at.isoformat()
                if checked_out_at
                else None
            ),
        },

        "released_by": {
            "user_id":
                usuario.id,

            "user_name":
                usuario.name,
        },
    }