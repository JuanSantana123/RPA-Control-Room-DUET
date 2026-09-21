# ============================================================
# DEVELOPMENT - WORKFLOW SERVICE
# ============================================================
#
# Responsável pelas regras de negócio do Workflow/Kanban
# dos AutomationProjects.
#
# Este módulo concentra:
#
# - listagem dos estágios;
# - montagem do quadro Kanban;
# - histórico de movimentações;
# - movimentação normal entre estágios;
# - publicação APPROVED -> PUBLISHED.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints, não utiliza Depends
# e não aplica RBAC. Essas responsabilidades permanecem
# em api/development.py.
# ============================================================


import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from models import (
    AutomationProject,
    DevelopmentStage,
    ProjectCheckout,
    ProjectStageHistory,
    ProjectComment,
    User,
)

from releases.service import (
    lock_publication,
    prepare_release,
)

from development.serializers import (
    serializar_checkout,
    serializar_estagio,
    serializar_projeto,
)

from schemas.development import (
    DevelopmentPublishRequest,
    DevelopmentStageMove,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR ESTÁGIOS
# ============================================================

def listar_estagios_workflow_service(
    db: Session,
) -> dict:
    """
    Retorna os estágios ativos do Workflow na ordem em que
    devem aparecer no Kanban.
    """

    estagios = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.is_active == 1
        )
        .order_by(
            DevelopmentStage.position.asc()
        )
        .all()
    )

    return {
        "status": "success",
        "total": len(estagios),
        "stages": [
            serializar_estagio(estagio)
            for estagio in estagios
        ],
    }


# ============================================================
# CONSULTAR QUADRO DO WORKFLOW
# ============================================================

def consultar_quadro_workflow_service(
    db: Session,
) -> dict:
    """
    Retorna o quadro completo do Desenvolvimento.

    Cada estágio recebe somente projetos ativos atualmente
    posicionados naquela etapa.

    Projetos presentes na Lixeira não aparecem no Kanban.
    """

    # ========================================================
    # ESTÁGIOS
    # ========================================================

    estagios = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.is_active == 1
        )
        .order_by(
            DevelopmentStage.position.asc()
        )
        .all()
    )

    # ========================================================
    # ALIASES DE USERS
    # ========================================================
    #
    # A tabela users participa da consulta em três funções:
    #
    # - proprietário do Checkout;
    # - responsável funcional;
    # - responsável técnico.
    # ========================================================

    checkout_user = aliased(
        User
    )

    functional_user = aliased(
        User
    )

    technical_user = aliased(
        User
    )

    # ========================================================
    # QUANTIDADE DE COMENTÁRIOS POR PROJETO
    # ========================================================
    #
    # A agregação é feita antes da consulta principal para
    # evitar multiplicação das linhas do projeto.
    # ========================================================

    comentarios_por_projeto = (
        db.query(
            ProjectComment.project_id.label(
                "project_id"
            ),

            func.count(
                ProjectComment.id
            ).label(
                "comments_count"
            ),
        )
        .group_by(
            ProjectComment.project_id
        )
        .subquery()
    )

    # ========================================================
    # PROJETOS + CHECKOUT + RESPONSÁVEIS + COMENTÁRIOS
    # ========================================================

    projetos = (
        db.query(
            AutomationProject,

            ProjectCheckout,

            checkout_user.name.label(
                "checkout_user_name"
            ),

            functional_user.name.label(
                "functional_responsible_name"
            ),

            technical_user.name.label(
                "technical_responsible_name"
            ),

            func.coalesce(
                comentarios_por_projeto
                .c
                .comments_count,
                0,
            ).label(
                "comments_count"
            ),
        )

        # ----------------------------------------------------
        # CHECKOUT
        # ----------------------------------------------------

        .outerjoin(
            ProjectCheckout,
            ProjectCheckout.project_id ==
                AutomationProject.id,
        )

        .outerjoin(
            checkout_user,
            checkout_user.id ==
                ProjectCheckout.user_id,
        )

        # ----------------------------------------------------
        # RESPONSÁVEL FUNCIONAL
        # ----------------------------------------------------

        .outerjoin(
            functional_user,
            functional_user.id ==
                AutomationProject.functional_responsible_id,
        )

        # ----------------------------------------------------
        # RESPONSÁVEL TÉCNICO
        # ----------------------------------------------------

        .outerjoin(
            technical_user,
            technical_user.id ==
                AutomationProject.technical_responsible_id,
        )

        # ----------------------------------------------------
        # COMENTÁRIOS
        # ----------------------------------------------------

        .outerjoin(
            comentarios_por_projeto,

            comentarios_por_projeto
            .c
            .project_id ==
                AutomationProject.id,
        )

        .filter(
            AutomationProject.is_active == 1
        )

        .order_by(
            AutomationProject.updated_at.desc(),
            AutomationProject.id.desc(),
        )

        .all()
    )

    # ========================================================
    # ESTRUTURA DAS COLUNAS
    # ========================================================

    projetos_por_estagio = {
        estagio.id: []
        for estagio in estagios
    }

    # ========================================================
    # DISTRIBUI PROJETOS NAS COLUNAS
    # ========================================================

    for (
        projeto,
        checkout,
        checkout_user_name,
        functional_responsible_name,
        technical_responsible_name,
        comments_count,
    ) in projetos:

        # Projetos cujo estágio não faz parte do Workflow
        # ativo não entram em nenhuma coluna.
        if (
            projeto.current_stage_id
            not in projetos_por_estagio
        ):
            continue

        item = serializar_projeto(
            projeto
        )

        # ----------------------------------------------------
        # CHECKOUT
        # ----------------------------------------------------

        item["checkout"] = (
            serializar_checkout(
                checkout,
                checkout_user_name,
            )
            if checkout
            else None
        )

        # ----------------------------------------------------
        # RESPONSÁVEIS
        # ----------------------------------------------------

        item["functional_responsible_name"] = (
            functional_responsible_name
        )

        item["technical_responsible_name"] = (
            technical_responsible_name
        )

        # ----------------------------------------------------
        # COMENTÁRIOS
        # ----------------------------------------------------

        item["comments_count"] = int(
            comments_count or 0
        )

        projetos_por_estagio[
            projeto.current_stage_id
        ].append(
            item
        )

    # ========================================================
    # MONTA BOARD FINAL
    # ========================================================

    board = []

    for estagio in estagios:

        projetos_estagio = (
            projetos_por_estagio[
                estagio.id
            ]
        )

        board.append(
            {
                **serializar_estagio(
                    estagio
                ),
                "total_projects":
                    len(projetos_estagio),
                "projects":
                    projetos_estagio,
            }
        )

    return {
        "status": "success",
        "stages": board,
    }


# ============================================================
# HISTÓRICO DO WORKFLOW
# ============================================================

def consultar_historico_workflow_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Retorna o histórico de movimentações de um projeto.

    O backfill inicial para BACKLOG não gera histórico
    artificial porque não representa ação de usuário.
    """

    # ========================================================
    # PROJETO
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id
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
    # HISTÓRICOS
    # ========================================================

    historicos = (
        db.query(ProjectStageHistory)
        .filter(
            ProjectStageHistory.project_id ==
                project_id
        )
        .order_by(
            ProjectStageHistory.changed_at.desc(),
            ProjectStageHistory.id.desc(),
        )
        .all()
    )

    resultado = []

    for historico in historicos:

        estagio_origem = None

        # ----------------------------------------------------
        # ESTÁGIO DE ORIGEM
        # ----------------------------------------------------

        if historico.from_stage_id is not None:

            estagio_origem = (
                db.query(DevelopmentStage)
                .filter(
                    DevelopmentStage.id ==
                        historico.from_stage_id
                )
                .first()
            )

        # ----------------------------------------------------
        # ESTÁGIO DE DESTINO
        # ----------------------------------------------------

        estagio_destino = (
            db.query(DevelopmentStage)
            .filter(
                DevelopmentStage.id ==
                    historico.to_stage_id
            )
            .first()
        )

        # ----------------------------------------------------
        # USUÁRIO RESPONSÁVEL PELA ALTERAÇÃO
        # ----------------------------------------------------

        usuario_alteracao = (
            db.query(User)
            .filter(
                User.id ==
                    historico.changed_by
            )
            .first()
        )

        resultado.append(
            {
                "id":
                    historico.id,

                "project_id":
                    historico.project_id,

                "from_stage": (
                    serializar_estagio(
                        estagio_origem
                    )
                    if estagio_origem
                    else None
                ),

                "to_stage": (
                    serializar_estagio(
                        estagio_destino
                    )
                    if estagio_destino
                    else None
                ),

                "changed_by":
                    historico.changed_by,

                "changed_by_name": (
                    usuario_alteracao.name
                    if usuario_alteracao
                    else None
                ),

                "changed_at": (
                    historico.changed_at.isoformat()
                    if historico.changed_at
                    else None
                ),
            }
        )

    return {
        "status": "success",
        "project_id": project_id,
        "total": len(resultado),
        "history": resultado,
    }


# ============================================================
# MOVIMENTAR PROJETO NO WORKFLOW
# ============================================================

def movimentar_projeto_workflow_service(
    project_id: int,
    request: DevelopmentStageMove,
    db: Session,
    usuario,
) -> dict:
    """
    Move um projeto entre etapas normais do Workflow.

    Esta operação NÃO publica projetos.

    PUBLISHED somente pode ser alcançado pela operação
    específica de publicação.
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
    # ESTÁGIO ATUAL
    # ========================================================

    estagio_atual = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.id ==
                projeto.current_stage_id
        )
        .first()
    )

    if not estagio_atual:

        raise HTTPException(
            status_code=409,
            detail=(
                "O projeto não possui um estágio atual "
                "válido no Workflow."
            ),
        )

    # ========================================================
    # ESTÁGIO DE DESTINO
    # ========================================================

    estagio_destino = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.id ==
                request.target_stage_id,

            DevelopmentStage.is_active == 1,
        )
        .first()
    )

    if not estagio_destino:

        raise HTTPException(
            status_code=404,
            detail=(
                "Estágio de destino não encontrado."
            ),
        )

    # ========================================================
    # PROTEÇÃO DE PUBLISHED
    # ========================================================

    if estagio_destino.code == "PUBLISHED":

        raise HTTPException(
            status_code=409,
            detail=(
                "O estágio PUBLICADO exige a operação "
                "de publicação protegida."
            ),
        )

    # Um projeto publicado também não pode ser retirado
    # silenciosamente do estágio por movimentação comum.
    if estagio_atual.code == "PUBLISHED":

        raise HTTPException(
            status_code=409,
            detail=(
                "Um projeto PUBLICADO não pode ser movido "
                "por uma movimentação comum do Kanban."
            ),
        )

    # ========================================================
    # MOVIMENTAÇÃO IDEMPOTENTE
    # ========================================================
    #
    # Mover para o próprio estágio não gera novo histórico.
    # ========================================================

    if estagio_atual.id == estagio_destino.id:

        return {
            "status": "success",
            "message":
                "O projeto já está neste estágio.",
            "already_in_stage": True,
            "project":
                serializar_projeto(
                    projeto
                ),
            "stage":
                serializar_estagio(
                    estagio_atual
                ),
        }

    # ========================================================
    # HISTÓRICO
    # ========================================================

    historico = ProjectStageHistory(
        project_id=projeto.id,
        from_stage_id=estagio_atual.id,
        to_stage_id=estagio_destino.id,
        changed_by=usuario.id,
        changed_at=datetime.utcnow(),
    )

    try:

        projeto.current_stage_id = (
            estagio_destino.id
        )

        db.add(
            historico
        )

        db.commit()

        db.refresh(
            projeto
        )

        db.refresh(
            historico
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Projeto movimentado no Workflow",
            extra={
                "event":
                    "automation_project_stage_changed",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "from_stage":
                    estagio_atual.code,

                "to_stage":
                    estagio_destino.code,

                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message":
                "Projeto movimentado com sucesso.",
            "already_in_stage": False,

            "project":
                serializar_projeto(
                    projeto
                ),

            "from_stage":
                serializar_estagio(
                    estagio_atual
                ),

            "to_stage":
                serializar_estagio(
                    estagio_destino
                ),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao movimentar projeto no Workflow",
            extra={
                "event":
                    "automation_project_stage_change_failed",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "status":
                    "error",

                "error_type":
                    type(error).__name__,

                "error_message":
                    str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível movimentar o projeto "
                "no Workflow."
            ),
        )


# ============================================================
# PUBLICAR PROJETO
# ============================================================

def publicar_projeto_workflow_service(
    project_id: int,
    request: DevelopmentPublishRequest,
    db: Session,
    usuario,
) -> dict:
    """
    Publica Robot/Bibliotecas e confirma:

        APPROVED -> PUBLISHED

    As permissões HTTP continuam sendo verificadas pelo
    router antes da chamada deste service.

    Regras:

        1. projeto precisa estar em APPROVED;

        2. não pode existir Checkout ativo;

        3. usuário precisa confirmar digitando exatamente
           o nome atual do projeto;

        4. Release físico, LibraryVersions e Workflow são
           confirmados na mesma transação;

        5. em falha, arquivos exclusivos desta tentativa
           são removidos.
    """

    # ========================================================
    # LOCK GLOBAL DE PUBLICAÇÃO
    # ========================================================

    lock_publication(
        db
    )

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
    # EXIGE APPROVED
    # ========================================================

    estagio_atual = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.id ==
                projeto.current_stage_id
        )
        .first()
    )

    if (
        not estagio_atual
        or estagio_atual.code != "APPROVED"
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "Somente projetos no estágio APROVADO "
                "podem ser publicados."
            ),
        )

    # ========================================================
    # CONFIRMAÇÃO FORTE PELO NOME
    # ========================================================

    confirmation_name = (
        request.confirmation_name.strip()
    )

    if confirmation_name != projeto.name:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome informado não corresponde exatamente "
                "ao nome do projeto."
            ),
        )

    # ========================================================
    # CHECKOUT ATIVO
    # ========================================================

    checkout_ativo = (
        db.query(ProjectCheckout)
        .filter(
            ProjectCheckout.project_id ==
                project_id
        )
        .first()
    )

    if checkout_ativo:

        checkout_user = (
            db.query(User)
            .filter(
                User.id ==
                    checkout_ativo.user_id
            )
            .first()
        )

        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "O projeto possui Checkout ativo. "
                    "Realize o Checkin ou Force Release "
                    "antes da publicação."
                ),

                "checkout_user_id":
                    checkout_ativo.user_id,

                "checkout_user_name": (
                    checkout_user.name
                    if checkout_user
                    else None
                ),
            },
        )

    # ========================================================
    # ESTÁGIO PUBLISHED
    # ========================================================

    estagio_publicado = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.code ==
                "PUBLISHED",

            DevelopmentStage.is_active == 1,
        )
        .first()
    )

    if not estagio_publicado:

        raise HTTPException(
            status_code=500,
            detail=(
                "O estágio PUBLISHED não está configurado "
                "no Workflow de Desenvolvimento."
            ),
        )

    # ========================================================
    # PUBLICAÇÃO ATÔMICA
    # ========================================================

    created_paths = []

    committed = False

    try:

        # ----------------------------------------------------
        # PREPARA RELEASE
        # ----------------------------------------------------
        #
        # O Release físico e novas LibraryVersions são
        # preparados antes de alterar o estágio para
        # PUBLISHED.
        #
        # Não existe commit intermediário.
        # ----------------------------------------------------

        release = prepare_release(
            db,
            projeto,
            request,
            usuario.id,
            created_paths,
        )

        # ----------------------------------------------------
        # HISTÓRICO APPROVED -> PUBLISHED
        # ----------------------------------------------------

        historico = ProjectStageHistory(
            project_id=projeto.id,
            from_stage_id=estagio_atual.id,
            to_stage_id=estagio_publicado.id,
            changed_by=usuario.id,
            changed_at=datetime.utcnow(),
        )

        projeto.current_stage_id = (
            estagio_publicado.id
        )

        db.add(
            historico
        )

        # ----------------------------------------------------
        # FLUSH SEM COMMIT
        # ----------------------------------------------------

        db.flush()

        # ----------------------------------------------------
        # SERIALIZA ANTES DO COMMIT
        # ----------------------------------------------------
        #
        # Essa ordem é intencional.
        #
        # Nenhuma leitura posterior ao commit deve transformar
        # um Release já confirmado em uma falsa resposta de
        # erro para o cliente.
        # ----------------------------------------------------

        response = {
            "status": "success",
            "message":
                "Release publicado em Robôs.",

            "project":
                serializar_projeto(
                    projeto
                ),

            "release":
                release,

            "from_stage":
                serializar_estagio(
                    estagio_atual
                ),

            "to_stage":
                serializar_estagio(
                    estagio_publicado
                ),
        }

        # ----------------------------------------------------
        # COMMIT ÚNICO
        # ----------------------------------------------------

        db.commit()

        committed = True

        return response

    # ========================================================
    # ERRO FUNCIONAL
    # ========================================================

    except HTTPException:

        db.rollback()

        raise

    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception:

        db.rollback()

        logger.exception(
            "Falha ao publicar Release",
            extra={
                "event":
                    "automation_project_release_failed",

                "project_id":
                    project_id,

                "user_id":
                    usuario.id,
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível publicar o Release. "
                "Confira o log do Control Room."
            ),
        )

    # ========================================================
    # LIMPEZA DE ARTEFATOS NÃO COMMITADOS
    # ========================================================

    finally:

        if not committed:

            # Remove somente arquivos exclusivos desta
            # tentativa de publicação.
            #
            # Nunca removemos o pacote atualmente publicado
            # nem versões pertencentes a outro projeto.
            for path in created_paths:

                path.unlink(
                    missing_ok=True
                )

                # Remove diretórios vazios criados pelo build.
                #
                # A subida para ao chegar em "storage" ou
                # quando encontra um diretório não vazio.
                parent = (
                    path.parent
                )

                while (
                    parent.name != "storage"
                    and parent != parent.parent
                ):

                    try:

                        parent.rmdir()

                    except OSError:

                        break

                    parent = (
                        parent.parent
                    )