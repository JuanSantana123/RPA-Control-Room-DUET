# ============================================================
# DEVELOPMENT - KANBAN SERVICE
# ============================================================
#
# Responsável pelas regras de negócio dos dados de Kanban
# associados aos AutomationProjects.
#
# Este módulo concentra:
#
# - usuários disponíveis para responsabilidade;
# - atualização dos detalhes individuais do card;
# - validação dos responsáveis;
# - validação das datas de planejamento;
# - listagem de comentários;
# - criação de comentários.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - utiliza Depends;
# - realiza autenticação;
# - aplica RBAC;
# - exige Checkout para alterações de metadados do Kanban.
#
# A camada HTTP continua em:
#
#     api/development.py
# ============================================================


import logging

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from models import (
    AutomationProject,
    DevelopmentStage,
    ProjectComment,
    ProjectCommentAttachment,
    ProjectStageHistory,
    User,
)

from development.serializers import (
    serializar_comentario,
    serializar_projeto,
)

from schemas.development import (
    AutomationProjectCardUpdate,
    ProjectCommentCreate,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# USUÁRIOS DISPONÍVEIS PARA RESPONSABILIDADE
# ============================================================

def listar_usuarios_card_service(
    db: Session,
) -> dict:
    """
    Retorna os usuários ativos que podem ser escolhidos como:

    - responsável funcional;
    - responsável técnico.

    Nenhum dado sensível do usuário é retornado.
    """

    usuarios = (
        db.query(User)
        .filter(
            User.is_active == 1
        )
        .order_by(
            User.name.asc(),
            User.id.asc(),
        )
        .all()
    )

    return {
        "status": "success",
        "total": len(usuarios),

        "users": [
            {
                "id": item.id,
                "name": item.name,
            }

            for item in usuarios
        ],
    }


# ============================================================
# ATUALIZAR DETALHES DO CARD
# ============================================================

def atualizar_detalhes_card_service(
    project_id: int,
    request: AutomationProjectCardUpdate,
    db: Session,
    usuario,
) -> dict:
    """
    Atualiza os dados de planejamento pertencentes
    individualmente ao AutomationProject.

    Campos controlados:

    - responsável funcional;
    - responsável técnico;
    - data de início;
    - previsão de conclusão;
    - horas de esforço.

    IMPORTANTE:

    Esta operação não exige Checkout porque altera
    metadados do Kanban e não o código-fonte do Workspace.
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
    # CAMPOS REALMENTE ENVIADOS
    # ========================================================
    #
    # PATCH precisa diferenciar:
    #
    # campo ausente:
    #     mantém o valor atual.
    #
    # campo enviado como null:
    #     remove o valor atual.
    #
    # Mantemos compatibilidade com:
    #
    # - Pydantic 2 -> model_fields_set
    # - Pydantic 1 -> __fields_set__
    # ========================================================

    campos_enviados = (
        request.model_fields_set
        if hasattr(
            request,
            "model_fields_set",
        )
        else request.__fields_set__
    )

    # ========================================================
    # RESPONSÁVEL FUNCIONAL
    # ========================================================

    if (
        "functional_responsible_id"
        in campos_enviados
        and request.functional_responsible_id
            is not None
    ):

        # Busca somente pelo ID primeiro.
        #
        # A existência e o estado ativo são tratados como
        # validações distintas.
        responsavel_funcional = db.get(
            User,
            request.functional_responsible_id,
        )

        if not responsavel_funcional:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Responsável funcional não encontrado. "
                    f"ID recebido: "
                    f"{request.functional_responsible_id}"
                ),
            )

        if not bool(
            responsavel_funcional.is_active
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "O responsável funcional selecionado "
                    "está inativo."
                ),
            )

    # ========================================================
    # RESPONSÁVEL TÉCNICO
    # ========================================================

    if (
        "technical_responsible_id"
        in campos_enviados
        and request.technical_responsible_id
            is not None
    ):

        responsavel_tecnico = db.get(
            User,
            request.technical_responsible_id,
        )

        if not responsavel_tecnico:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Responsável técnico não encontrado. "
                    f"ID recebido: "
                    f"{request.technical_responsible_id}"
                ),
            )

        if not bool(
            responsavel_tecnico.is_active
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "O responsável técnico selecionado "
                    "está inativo."
                ),
            )

    # ========================================================
    # DATAS EFETIVAS
    # ========================================================
    #
    # Se somente uma das datas vier no PATCH, precisamos
    # comparar o novo valor com o valor já persistido da
    # outra data.
    # ========================================================

    inicio_final = (
        request.start_date
        if "start_date" in campos_enviados
        else projeto.start_date
    )

    previsao_final = (
        request.due_date
        if "due_date" in campos_enviados
        else projeto.due_date
    )

    if (
        inicio_final is not None
        and previsao_final is not None
        and previsao_final < inicio_final
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A previsão de conclusão não pode ser "
                "anterior à data de início."
            ),
        )

    # ========================================================
    # APLICA SOMENTE OS CAMPOS ENVIADOS
    # ========================================================

    if (
        "functional_responsible_id"
        in campos_enviados
    ):

        projeto.functional_responsible_id = (
            request.functional_responsible_id
        )

    if (
        "technical_responsible_id"
        in campos_enviados
    ):

        projeto.technical_responsible_id = (
            request.technical_responsible_id
        )

    if "start_date" in campos_enviados:

        projeto.start_date = (
            request.start_date
        )

    if "due_date" in campos_enviados:

        projeto.due_date = (
            request.due_date
        )

    if "effort_hours" in campos_enviados:

        projeto.effort_hours = (
            request.effort_hours
        )

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    try:

        db.commit()

        db.refresh(
            projeto
        )

        # ====================================================
        # NOMES AMIGÁVEIS DOS RESPONSÁVEIS
        # ====================================================

        functional_name = None
        technical_name = None

        if (
            projeto.functional_responsible_id
            is not None
        ):

            responsavel = (
                db.query(User)
                .filter(
                    User.id ==
                        projeto.functional_responsible_id
                )
                .first()
            )

            functional_name = (
                responsavel.name
                if responsavel
                else None
            )

        if (
            projeto.technical_responsible_id
            is not None
        ):

            responsavel = (
                db.query(User)
                .filter(
                    User.id ==
                        projeto.technical_responsible_id
                )
                .first()
            )

            technical_name = (
                responsavel.name
                if responsavel
                else None
            )

        # ====================================================
        # QUANTIDADE DE COMENTÁRIOS
        # ====================================================

        comments_count = (
            db.query(
                func.count(
                    ProjectComment.id
                )
            )
            .filter(
                ProjectComment.project_id ==
                    projeto.id
            )
            .scalar()
            or 0
        )

        # Serialização base do projeto.
        item = serializar_projeto(
            projeto
        )

        # Dados complementares utilizados pelo card.
        item["functional_responsible_name"] = (
            functional_name
        )

        item["technical_responsible_name"] = (
            technical_name
        )

        item["comments_count"] = int(
            comments_count
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Detalhes do card atualizados",
            extra={
                "event":
                    "development_card_details_updated",

                "user_id":
                    usuario.id,

                "project_id":
                    projeto.id,

                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Detalhes do card atualizados com sucesso."
            ),
            "project": item,
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao atualizar detalhes do card",
            extra={
                "event":
                    "development_card_details_update_failed",

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
                "Não foi possível atualizar os "
                "detalhes do card."
            ),
        )


# ============================================================
# LISTAR COMENTÁRIOS DO PROJETO
# ============================================================

def listar_comentarios_projeto_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Retorna todos os comentários do projeto em ordem
    cronológica.

    A leitura dos comentários não exige Checkout.
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
    # COMENTÁRIOS + NOME DO AUTOR
    # ========================================================

    registros = (
        db.query(
            ProjectComment,

            User.name.label(
                "user_name"
            ),
        )
        .join(
            User,
            User.id ==
                ProjectComment.user_id,
        )
        .filter(
            ProjectComment.project_id ==
                project_id
        )
        .order_by(
            ProjectComment.created_at.asc(),
            ProjectComment.id.asc(),
        )
        .all()
    )

    attachment_rows = (
        db.query(ProjectCommentAttachment)
        .filter(
            ProjectCommentAttachment.project_id == project_id,
            ProjectCommentAttachment.comment_id.is_not(None),
        )
        .order_by(ProjectCommentAttachment.created_at.asc(), ProjectCommentAttachment.id.asc())
        .all()
    )
    attachments_by_comment: dict[int, list[ProjectCommentAttachment]] = {}
    for attachment in attachment_rows:
        if attachment.comment_id is not None:
            attachments_by_comment.setdefault(attachment.comment_id, []).append(attachment)

    comentarios = [
        serializar_comentario(
            comentario,
            user_name,
            attachments_by_comment.get(comentario.id, []),
        )

        for comentario, user_name
        in registros
    ]

    from_stage = aliased(DevelopmentStage)
    to_stage = aliased(DevelopmentStage)
    movimentacoes = (
        db.query(
            ProjectStageHistory,
            User.name.label("user_name"),
            from_stage.id.label("from_id"),
            from_stage.code.label("from_code"),
            from_stage.name.label("from_name"),
            to_stage.id.label("to_id"),
            to_stage.code.label("to_code"),
            to_stage.name.label("to_name"),
        )
        .join(User, User.id == ProjectStageHistory.changed_by)
        .outerjoin(from_stage, from_stage.id == ProjectStageHistory.from_stage_id)
        .join(to_stage, to_stage.id == ProjectStageHistory.to_stage_id)
        .filter(ProjectStageHistory.project_id == project_id)
        .order_by(ProjectStageHistory.changed_at.asc(), ProjectStageHistory.id.asc())
        .all()
    )

    eventos_movimentacao = [
        {
            "id": historico.id,
            "event_key": f"stage-movement-{historico.id}",
            "kind": "stage_movement",
            "project_id": historico.project_id,
            "user_id": historico.changed_by,
            "user_name": user_name,
            "content": None,
            "attachments": [],
            "from_stage": (
                {"id": from_id, "code": from_code, "name": from_name}
                if from_id is not None
                else None
            ),
            "to_stage": {"id": to_id, "code": to_code, "name": to_name},
            "created_at": historico.changed_at.isoformat() if historico.changed_at else None,
            "updated_at": historico.changed_at.isoformat() if historico.changed_at else None,
        }
        for (
            historico,
            user_name,
            from_id,
            from_code,
            from_name,
            to_id,
            to_code,
            to_name,
        ) in movimentacoes
    ]

    linha_do_tempo = sorted(
        [*comentarios, *eventos_movimentacao],
        key=lambda item: (item.get("created_at") or "", item["event_key"]),
    )

    return {
        "status": "success",
        "project_id": project_id,
        "total": len(linha_do_tempo),
        "comments": linha_do_tempo,
    }


# ============================================================
# ADICIONAR COMENTÁRIO AO PROJETO
# ============================================================

def adicionar_comentario_projeto_service(
    project_id: int,
    request: ProjectCommentCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Adiciona um comentário livre ao card.

    O autor não é recebido do frontend.

    O user_id é obtido exclusivamente através do usuário
    autenticado recebido pela camada HTTP.
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
    # CONTEÚDO
    # ========================================================

    conteudo = (
        request.content.strip()
    )

    if not conteudo:

        raise HTTPException(
            status_code=400,
            detail=(
                "O comentário não pode ficar vazio."
            ),
        )

    # ========================================================
    # NOVO COMENTÁRIO
    # ========================================================

    comentario = ProjectComment(
        project_id=projeto.id,
        user_id=usuario.id,
        content=conteudo,
    )

    try:

        db.add(
            comentario
        )

        db.flush()

        attachment_ids = list(dict.fromkeys(request.attachment_ids))
        if len(attachment_ids) != len(request.attachment_ids):
            raise HTTPException(status_code=400, detail="A lista de anexos contém itens repetidos.")

        attachments: list[ProjectCommentAttachment] = []
        if attachment_ids:
            attachments = (
                db.query(ProjectCommentAttachment)
                .filter(
                    ProjectCommentAttachment.id.in_(attachment_ids),
                    ProjectCommentAttachment.project_id == projeto.id,
                    ProjectCommentAttachment.uploaded_by == usuario.id,
                    ProjectCommentAttachment.comment_id.is_(None),
                )
                .with_for_update()
                .all()
            )
            if len(attachments) != len(attachment_ids):
                raise HTTPException(
                    status_code=409,
                    detail="Um ou mais anexos não estão disponíveis para este comentário.",
                )
            for attachment in attachments:
                attachment.comment_id = comentario.id

        db.commit()

        db.refresh(
            comentario
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Comentário adicionado ao card",
            extra={
                "event":
                    "development_project_comment_created",

                "user_id":
                    usuario.id,

                "project_id":
                    projeto.id,

                "comment_id":
                    comentario.id,

                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Comentário adicionado com sucesso."
            ),
            "comment":
                serializar_comentario(
                    comentario,
                    usuario.name,
                    attachments,
                ),
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao adicionar comentário ao card",
            extra={
                "event":
                    "development_project_comment_create_failed",

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
                "Não foi possível adicionar o comentário."
            ),
        )
