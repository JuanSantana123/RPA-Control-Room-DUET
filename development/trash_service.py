# ============================================================
# DEVELOPMENT - TRASH SERVICE
# ============================================================
#
# Responsável pelo ciclo de vida dos AutomationProjects
# enviados para a Lixeira.
#
# Este módulo concentra:
#
# - listagem dos projetos excluídos;
# - exclusão lógica / envio para Lixeira;
# - restauração;
# - exclusão permanente;
# - proteção do Workspace durante exclusão permanente.
#
# IMPORTANTE:
#
# Enviar para a Lixeira NÃO remove o Workspace.
#
# Exclusão permanente:
#
#     1. move temporariamente o Workspace;
#     2. remove o registro do banco;
#     3. confirma a transação;
#     4. remove fisicamente o diretório temporário.
#
# Se o banco falhar, o Workspace é restaurado.
#
# Este módulo NÃO registra endpoints FastAPI, não utiliza
# Depends e não aplica RBAC.
# ============================================================

import logging

from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    DevelopmentFolder,
    ProjectCheckout,
    User,
)
from development.repository import (
    WORKSPACE_REPOSITORY,
    remover_workspace_controlado,
    validar_workspace_fisico,
)

from development.serializers import (
    serializar_projeto,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR PROJETOS DA LIXEIRA
# ============================================================
def listar_lixeira_projetos_service(
    db: Session,
) -> dict:
    """
    Retorna todos os AutomationProjects atualmente
    presentes na Lixeira.

    O nome histórico do Robot de origem já pertence ao próprio
    AutomationProject através de base_robot_name.

    Portanto, a listagem precisa resolver externamente apenas
    o nome do usuário responsável pela exclusão.
    """

    # ========================================================
    # CONSULTA
    # ========================================================
    #
    # O AutomationProject já contém:
    #
    #     base_robot_id
    #     base_robot_name
    #     base_version
    #
    # Portanto NÃO fazemos JOIN com Robot.
    #
    # O único LEFT JOIN necessário aqui é com User, porque
    # deleted_by pode ser NULL em registros antigos.
    # ========================================================

    registros = (
        db.query(
            AutomationProject,

            User.name.label(
                "deleted_by_name"
            ),
        )
        .outerjoin(
            User,
            User.id ==
                AutomationProject.deleted_by,
        )
        .filter(
            AutomationProject.is_active == 0
        )
        .order_by(
            AutomationProject
            .deleted_at
            .desc()
            .nullslast(),

            AutomationProject
            .updated_at
            .desc(),

            AutomationProject
            .id
            .desc(),
        )
        .all()
    )

    # ========================================================
    # SERIALIZAÇÃO
    # ========================================================

    resultado = []

    for (
        projeto,
        deleted_by_name,
    ) in registros:

        # serializar_projeto() lê base_robot_name diretamente
        # do AutomationProject.
        item = serializar_projeto(
            projeto
        )

        # Nome amigável do usuário que enviou o projeto
        # para a Lixeira.
        item["deleted_by_name"] = (
            deleted_by_name
        )

        resultado.append(
            item
        )

    return {
        "status": "success",
        "total": len(resultado),
        "projects": resultado,
    }

# ENVIAR PROJETO PARA A LIXEIRA
# ============================================================

def excluir_projeto_service(
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Envia um AutomationProject para a Lixeira.

    Esta é uma exclusão lógica.

    Banco:
        is_active = 0
        deleted_at = data/hora atual
        deleted_by = usuário autenticado

    Workspace:
        permanece intacto.

    Projetos com Checkout ativo não podem ser enviados
    para a Lixeira.
    """

    # ========================================================
    # PROJETO ATIVO
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
    # BLOQUEIA CHECKOUT ATIVO
    # ========================================================
    #
    # Mesmo o proprietário precisa executar Checkin.
    #
    # Para remoção administrativa existe Force Release.
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
                    "antes de enviá-lo para a Lixeira."
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
    # EXCLUSÃO LÓGICA
    # ========================================================

    try:

        projeto.is_active = 0

        projeto.deleted_at = (
            datetime.utcnow()
        )

        projeto.deleted_by = (
            usuario.id
        )

        db.commit()

        db.refresh(
            projeto
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Projeto enviado para a Lixeira",
            extra={
                "event":
                    "automation_project_trashed",

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
                "Projeto enviado para a Lixeira.",

            "project_id":
                project_id,

            "deleted_at": (
                projeto.deleted_at.isoformat()
                if projeto.deleted_at
                else None
            ),

            "deleted_by":
                projeto.deleted_by,
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao enviar projeto para a Lixeira",
            extra={
                "event":
                    "automation_project_trash_failed",

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
                "Não foi possível enviar "
                "o projeto para a Lixeira."
            ),
        )


# ============================================================
# RESTAURAR PROJETO
# ============================================================

def restaurar_projeto_service(
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Restaura um projeto atualmente presente na Lixeira.

    São preservados:

        - project_id;
        - Workspace;
        - código;
        - metadados;
        - estágio;
        - demais relacionamentos existentes.

    A pasta original precisa continuar disponível.
    """

    # ========================================================
    # PROJETO NA LIXEIRA
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id,

            AutomationProject.is_active == 0,
        )
        .with_for_update()
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail=(
                "Projeto não encontrado na Lixeira."
            ),
        )

    # ========================================================
    # VALIDA PASTA ORIGINAL
    # ========================================================
    #
    # Não movemos silenciosamente um projeto para outro
    # local caso sua pasta original deixe de existir.
    # ========================================================

    if projeto.folder_id is not None:

        pasta = (
            db.query(DevelopmentFolder)
            .filter(
                DevelopmentFolder.id ==
                    projeto.folder_id,

                DevelopmentFolder.is_active ==
                    1,
            )
            .first()
        )

        if not pasta:

            raise HTTPException(
                status_code=409,
                detail=(
                    "A pasta original deste projeto "
                    "não está mais disponível."
                ),
            )

    # ========================================================
    # EVITA DUPLICIDADE
    # ========================================================
    #
    # Exemplo:
    #
    #     Projeto "SAP" vai para a Lixeira.
    #
    #     Outro projeto "SAP" é criado no mesmo local.
    #
    #     O projeto antigo não pode ser restaurado enquanto
    #     o conflito existir.
    # ========================================================

    consulta_duplicada = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id !=
                project_id,

            AutomationProject.is_active ==
                1,

            func.lower(
                AutomationProject.name
            ) ==
                projeto.name.lower(),
        )
    )

    # --------------------------------------------------------
    # MESMO LOCAL DA ÁRVORE
    # --------------------------------------------------------

    if projeto.folder_id is None:

        consulta_duplicada = (
            consulta_duplicada
            .filter(
                AutomationProject
                .folder_id
                .is_(None)
            )
        )

    else:

        consulta_duplicada = (
            consulta_duplicada
            .filter(
                AutomationProject.folder_id ==
                    projeto.folder_id
            )
        )

    if consulta_duplicada.first():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um projeto ativo "
                "com esse nome neste local."
            ),
        )

    # ========================================================
    # RESTAURA
    # ========================================================

    try:

        projeto.is_active = 1

        projeto.deleted_at = None

        projeto.deleted_by = None

        db.commit()

        db.refresh(
            projeto
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Projeto restaurado da Lixeira",
            extra={
                "event":
                    "automation_project_restored",

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
                "Projeto restaurado com sucesso.",

            "project":
                serializar_projeto(
                    projeto
                ),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao restaurar projeto da Lixeira",
            extra={
                "event":
                    "automation_project_restore_failed",

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
                "Não foi possível restaurar "
                "o projeto."
            ),
        )


# ============================================================
# EXCLUIR PROJETO PERMANENTEMENTE
# ============================================================

def excluir_projeto_permanentemente_service(
    project_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Exclui definitivamente um AutomationProject.

    REGRA:

        somente projetos já presentes na Lixeira podem ser
        excluídos permanentemente.

    A operação remove:

        1. registro do banco;
        2. Workspace físico.

    Para reduzir o risco de inconsistência entre banco e
    filesystem, o Workspace é movido temporariamente antes
    do DELETE no banco.
    """

    # ========================================================
    # PROJETO NA LIXEIRA
    # ========================================================

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id,

            AutomationProject.is_active == 0,
        )
        .with_for_update()
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail=(
                "Projeto não encontrado na Lixeira."
            ),
        )

    # ========================================================
    # WORKSPACE
    # ========================================================
    #
    # NÃO utilizamos garantir_workspace().
    #
    # Uma exclusão nunca deve criar um diretório inexistente.
    # ========================================================

    # Obtém a raiz oficial sem criar nada.
    #
    # Se existir, ela precisa ser um diretório físico normal:
    # symlink/junction/reparse point não pode participar de
    # exclusão permanente.
    workspace_path = (
        validar_workspace_fisico(
            project_id,
            permitir_inexistente=True,
        )
    )

    # ========================================================
    # STAGING DO WORKSPACE
    # ========================================================
    #
    # Antes de remover o registro do banco, movemos o
    # Workspace para um nome temporário.
    #
    # Se o banco falhar, conseguimos renomeá-lo de volta.
    # ========================================================

    staged_workspace_path = None

    try:

        if workspace_path.exists():

            staged_workspace_path = (
                WORKSPACE_REPOSITORY /
                (
                    f".deleting_project_"
                    f"{project_id}_"
                    f"{uuid4().hex}"
                )
            )

            # UUID torna colisão extremamente improvável, mas a
            # operação de segurança não depende dessa suposição.
            if (
                staged_workspace_path.exists()
                or staged_workspace_path.is_symlink()
            ):
                raise RuntimeError(
                    "Diretório temporário de exclusão "
                    "já existe."
                )

            workspace_path.rename(
                staged_workspace_path
            )

        # ====================================================
        # REMOVE REGISTRO DO BANCO
        # ====================================================

        db.delete(
            projeto
        )

        db.commit()

    # ========================================================
    # FALHA NO BANCO
    # ========================================================

    except Exception as error:

        db.rollback()

        # ----------------------------------------------------
        # RESTAURA O WORKSPACE
        # ----------------------------------------------------

        if (
            staged_workspace_path
            and (
                staged_workspace_path.exists()
                or staged_workspace_path.is_symlink()
            )
            and not (
                workspace_path.exists()
                or workspace_path.is_symlink()
            )
        ):

            try:

                staged_workspace_path.rename(
                    workspace_path
                )

            except Exception:

                logger.exception(
                    (
                        "Falha ao restaurar workspace após "
                        "erro na exclusão permanente"
                    ),
                    extra={
                        "event":
                            "automation_project_permanent_delete_rollback_workspace_failed",

                        "project_id":
                            project_id,

                        "user_id":
                            usuario.id,

                        "status":
                            "error",
                    },
                )

        logger.exception(
            "Falha ao excluir projeto permanentemente",
            extra={
                "event":
                    "automation_project_permanent_delete_failed",

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
                "Não foi possível excluir "
                "o projeto permanentemente."
            ),
        )

    # ========================================================
    # LIMPEZA FÍSICA
    # ========================================================
    #
    # Neste ponto o DELETE já foi confirmado no banco.
    #
    # Agora podemos remover definitivamente o diretório
    # temporário.
    # ========================================================

    workspace_cleanup = (
        "not_found"
    )

    if (
        staged_workspace_path
        and (
            staged_workspace_path.exists()
            or staged_workspace_path.is_symlink()
        )
    ):

        try:

            remover_workspace_controlado(
                staged_workspace_path
            )

            workspace_cleanup = (
                "deleted"
            )

        except Exception as cleanup_error:

            # O registro já foi removido do banco.
            #
            # Portanto não fazemos rollback falso da operação.
            # A falha física é registrada explicitamente.
            workspace_cleanup = (
                "cleanup_failed"
            )

            logger.exception(
                (
                    "Registro do projeto foi removido, "
                    "mas houve falha ao limpar o workspace"
                ),
                extra={
                    "event":
                        "automation_project_workspace_cleanup_failed",

                    "user_id":
                        usuario.id,

                    "project_id":
                        project_id,

                    "workspace_path":
                        str(
                            staged_workspace_path
                        ),

                    "status":
                        "error",

                    "error_type":
                        type(
                            cleanup_error
                        ).__name__,

                    "error_message":
                        str(
                            cleanup_error
                        ),
                },
            )

    # ========================================================
    # AUDITORIA
    # ========================================================

    logger.info(
        "Projeto excluído permanentemente",
        extra={
            "event":
                "automation_project_permanently_deleted",

            "user_id":
                usuario.id,

            "project_id":
                project_id,

            "workspace_cleanup":
                workspace_cleanup,

            "status":
                "success",
        },
    )

    return {
        "status": "success",
        "message":
            "Projeto excluído permanentemente.",

        "project_id":
            project_id,

        "workspace_cleanup":
            workspace_cleanup,
    }