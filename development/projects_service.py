# ============================================================
# DEVELOPMENT - PROJECTS SERVICE
# ============================================================
#
# Responsável pelas regras de negócio centrais dos
# AutomationProjects da área de Desenvolvimento.
#
# Este módulo concentra:
#
# - listagem de projetos ativos;
# - criação de novos projetos;
# - criação de projeto a partir de Robot publicado;
# - criação de projeto a partir de Template versionado;
# - validação de nome duplicado;
# - definição do estágio inicial BACKLOG;
# - captura da versão do Robot de origem;
# - restauração do workspace de um Robot publicado;
# - cópia inicial do código de uma versão de Template;
# - consulta individual de projeto.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - utiliza Depends;
# - realiza autenticação;
# - aplica RBAC;
# - controla Kanban;
# - controla Checkout;
# - controla Lixeira;
# - controla Libraries;
# - edita arquivos do Workspace.
#
# Essas responsabilidades permanecem em seus respectivos
# services e no router HTTP.
# ============================================================


import logging
import shutil
import logging
from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    DevelopmentFolder,
    DevelopmentStage,
    Robot,
)

from releases.service import (
    lock_publication,
    restore_project_from_robot,
)

from development.serializers import (
    serializar_projeto,
)

from schemas.development import (
    AutomationProjectCreate,
)

from development.repository import (
    remover_workspace_controlado,
    validar_workspace_fisico,
)

from automation_templates.service import (
    instanciar_template_no_workspace,
    obter_template_version_or_404,
)
# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR PROJETOS
# ============================================================

def listar_projetos_service(
    folder_id: int | None,
    db: Session,
) -> dict:
    """
    Retorna os projetos ativos da área de Desenvolvimento.

    Parâmetros:
        folder_id:
            Quando informado, limita a consulta aos projetos
            pertencentes àquela pasta.

            Quando None, retorna todos os projetos ativos.

        db:
            Sessão SQLAlchemy fornecida pela camada HTTP.

    Retorno:
        Mantém o mesmo contrato utilizado atualmente por:

            GET /development/projects
    """

    # ========================================================
    # PROJETOS + ROBOT DE ORIGEM
    # ========================================================
    #
    # LEFT JOIN é utilizado porque um projeto pode ter sido
    # criado do zero e, portanto, não possuir base_robot_id.
    #
    # O nome do Robot já vem na mesma consulta, evitando uma
    # nova consulta ao banco para cada card.
    # ========================================================

    # O próprio AutomationProject mantém o snapshot histórico
    # do Robot que originou o projeto.
    consulta = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.is_active == 1
        )
    )

    # Quando folder_id é informado, mantemos exatamente o
    # comportamento atual: filtrar somente aquela pasta.
    if folder_id is not None:

        consulta = consulta.filter(
            AutomationProject.folder_id ==
                folder_id
        )

    projetos = (
        consulta
        .order_by(
            AutomationProject.updated_at.desc(),
            AutomationProject.id.desc(),
        )
        .all()
    )

    resultado = [
        serializar_projeto(
            projeto
        )
        for projeto in projetos
        ]

    return {
        "status": "success",
        "total": len(resultado),
        "projects": resultado,
    }


# ============================================================
# CRIAR PROJETO
# ============================================================

def criar_projeto_service(
    request: AutomationProjectCreate,
    db: Session,
    usuario,
    template_version_id: int | None = None,
) -> dict:
    """
    Cria um novo AutomationProject.

    O fluxo existente continua aceitando:

        - projeto vazio;
        - projeto baseado em Robot publicado.

    A nova origem opcional aceita:

        - projeto baseado em uma versão imutável de Template.

    Template e Robot são origens mutuamente exclusivas.

    IMPORTANTE:
        O Template é utilizado somente para copiar o código inicial.
        Depois da criação, o Workspace do projeto é independente.
    """

    # ========================================================
    # LOCK DE PUBLICAÇÃO
    # ========================================================
    #
    # Preserva o mesmo lock já utilizado pelo fluxo de criação.
    #
    # A criação baseada em Template também precisa participar do
    # mesmo fluxo transacional porque gera um Workspace de
    # Desenvolvimento antes do commit.
    # ========================================================

    lock_publication(
        db
    )

    # ========================================================
    # NORMALIZAÇÃO DOS DADOS
    # ========================================================

    nome = (
        request.name.strip()
    )

    descricao = (
        request.description.strip()
        if request.description
        else None
    )

    folder_id = (
        request.folder_id
    )

    # TemplateProjectCreate não possui base_robot_id.
    #
    # getattr preserva o contrato do endpoint antigo sem exigir
    # alteração em schemas.development.
    base_robot_id = getattr(
        request,
        "base_robot_id",
        None,
    )

    if not nome:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome do projeto não pode ficar vazio."
            ),
        )

    # Robot publicado e Template representam duas origens
    # diferentes. Um projeto novo não pode receber ambas.
    if (
        base_robot_id is not None
        and template_version_id is not None
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Informe somente uma origem para o projeto: "
                "Robot publicado ou Template."
            ),
        )

    # ========================================================
    # VALIDA PASTA
    # ========================================================

    if folder_id is not None:

        pasta = (
            db.query(DevelopmentFolder)
            .filter(
                DevelopmentFolder.id ==
                    folder_id,

                DevelopmentFolder.is_active == 1,
            )
            .first()
        )

        if not pasta:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Pasta de desenvolvimento "
                    "não encontrada."
                ),
            )

    # ========================================================
    # LOCALIZA ESTÁGIO PUBLISHED
    # ========================================================
    #
    # PUBLISHED continua sendo utilizado somente para a regra
    # atual de duplicidade de nomes.
    # ========================================================

    estagio_publicado = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.code ==
                "PUBLISHED"
        )
        .first()
    )

    # ========================================================
    # EVITA PROJETO EM ANDAMENTO DUPLICADO
    # ========================================================

    consulta_duplicada = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.is_active == 1,

            func.lower(
                AutomationProject.name
            ) == nome.lower(),
        )
    )

    # Registros legados com current_stage_id=None continuam
    # sendo considerados conflito.
    if estagio_publicado:

        consulta_duplicada = (
            consulta_duplicada
            .filter(
                or_(
                    AutomationProject
                    .current_stage_id
                    .is_(None),

                    AutomationProject.current_stage_id !=
                        estagio_publicado.id,
                )
            )
        )

    if folder_id is None:

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
                    folder_id
            )
        )

    projeto_existente = (
        consulta_duplicada.first()
    )

    if projeto_existente:

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um projeto em andamento "
                "com esse nome neste local."
            ),
        )

    # ========================================================
    # RESOLVE ROBOT DE ORIGEM
    # ========================================================

    base_version = None
    base_robot_name = None

    robot_base = None

    if base_robot_id is not None:

        robot_base = (
            db.query(Robot)
            .filter(
                Robot.id ==
                    base_robot_id
            )
            .first()
        )

        if not robot_base:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Robot de origem não encontrado."
                ),
            )

        # Snapshot histórico da origem.
        base_version = (
            robot_base.version
        )

        base_robot_name = (
            robot_base.name
        )

    # ========================================================
    # RESOLVE TEMPLATE DE ORIGEM
    # ========================================================
    #
    # Quando template_version_id é informado, validamos:
    #
    # - versão existente;
    # - Template proprietário existente;
    # - Template ativo para novas criações.
    #
    # Uma versão anterior continua válida quando escolhida
    # explicitamente pelo usuário.
    # ========================================================

    template_base = None
    template_version_base = None

    base_template_id = None
    base_template_name = None
    base_template_version = None

    if template_version_id is not None:

        (
            template_base,
            template_version_base,
        ) = obter_template_version_or_404(
            db,
            template_version_id,
            somente_template_ativo=True,
        )

        base_template_id = (
            template_base.id
        )

        base_template_name = (
            template_base.name
        )

        base_template_version = (
            template_version_base.version
        )

    # ========================================================
    # ESTÁGIO INICIAL DO WORKFLOW
    # ========================================================

    backlog = (
        db.query(DevelopmentStage)
        .filter(
            DevelopmentStage.code ==
                "BACKLOG",

            DevelopmentStage.is_active == 1,
        )
        .first()
    )

    if not backlog:

        raise HTTPException(
            status_code=500,
            detail=(
                "O estágio BACKLOG não está configurado "
                "no Workflow de Desenvolvimento."
            ),
        )

    # ========================================================
    # MONTA O NOVO PROJETO
    # ========================================================

    projeto = AutomationProject(
        name=nome,
        description=descricao,
        folder_id=folder_id,

        # Todo projeto novo começa como draft.
        status="draft",

        # Todo projeto novo entra no BACKLOG.
        current_stage_id=backlog.id,

        # ----------------------------------------------------
        # ROBOT DE ORIGEM
        # ----------------------------------------------------

        base_robot_id=
            base_robot_id,

        base_robot_name=
            base_robot_name,

        base_version=
            base_version,

        # ----------------------------------------------------
        # TEMPLATE DE ORIGEM
        # ----------------------------------------------------
        #
        # Estes campos são apenas proveniência histórica.
        # Nenhum vínculo operacional permanece depois que o
        # Workspace é criado.
        # ----------------------------------------------------

        base_template_id=
            base_template_id,

        base_template_name=
            base_template_name,

        base_template_version_id=(
            template_version_base.id
            if template_version_base
            else None
        ),

        base_template_version=
            base_template_version,

        created_by=
            usuario.id,

        is_active=1,
    )

    # Caminho criado a partir de Robot ou Template.
    #
    # É utilizado pela estratégia de rollback em caso de erro.
    restored_workspace = None

    project_committed = False

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    try:

        db.add(
            projeto
        )

        # O projeto precisa possuir ID antes da criação física
        # de seu Workspace.
        db.flush()

        # ====================================================
        # RESTAURA ORIGEM DO WORKSPACE
        # ====================================================

        if base_robot_id is not None:

            # Preserva integralmente o fluxo existente de
            # restauração de Robot publicado.
            restored_workspace = (
                restore_project_from_robot(
                    db,
                    projeto,
                    robot_base,
                    usuario.id,
                )
            )

        elif template_version_base is not None:

            # Template é uma cópia inicial.
            #
            # Nenhuma referência ao ZIP é necessária para a
            # execução futura do projeto.
            restored_workspace = (
                instanciar_template_no_workspace(
                    version=
                        template_version_base,
                    project_id=
                        projeto.id,
                )
            )

        # ====================================================
        # VALIDA WORKSPACE CRIADO/RESTAURADO
        # ====================================================

        if restored_workspace is not None:

            workspace_validado = (
                validar_workspace_fisico(
                    projeto.id,
                    permitir_inexistente=False,
                )
            )

            if (
                workspace_validado.resolve()
                != restored_workspace.resolve()
            ):
                raise RuntimeError(
                    "Workspace restaurado não corresponde "
                    "ao Workspace oficial do projeto."
                )

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        project_committed = True

        db.refresh(
            projeto
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Projeto de automação criado",
            extra={
                "event":
                    "automation_project_created",

                "user_id":
                    usuario.id,

                "status":
                    "success",
            },
        )

        return {
            "status":
                "success",

            "message": (
                "Projeto criado com sucesso."
            ),

            "project":
                serializar_projeto(
                    projeto
                ),
        }

    # ========================================================
    # ERRO FUNCIONAL / HTTP
    # ========================================================

    except HTTPException:

        db.rollback()

        if (
            restored_workspace is not None
            and not project_committed
        ):

            try:

                workspace_rollback = (
                    validar_workspace_fisico(
                        projeto.id,
                        permitir_inexistente=True,
                    )
                )

                remover_workspace_controlado(
                    workspace_rollback
                )

            except Exception:

                logger.exception(
                    "Falha ao limpar Workspace após "
                    "rollback da criação do projeto",
                    extra={
                        "event":
                            "automation_project_create_rollback_workspace_failed",

                        "project_id":
                            projeto.id,

                        "user_id":
                            usuario.id,

                        "status":
                            "error",
                    },
                )

        raise

    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception as error:

        db.rollback()

        if (
            restored_workspace is not None
            and not project_committed
        ):

            try:

                workspace_rollback = (
                    validar_workspace_fisico(
                        projeto.id,
                        permitir_inexistente=True,
                    )
                )

                remover_workspace_controlado(
                    workspace_rollback
                )

            except Exception:

                logger.exception(
                    "Falha ao limpar Workspace após "
                    "rollback da criação do projeto",
                    extra={
                        "event":
                            "automation_project_create_rollback_workspace_failed",

                        "project_id":
                            projeto.id,

                        "user_id":
                            usuario.id,

                        "status":
                            "error",
                    },
                )

        logger.exception(
            "Falha ao criar projeto de automação",
            extra={
                "event":
                    "automation_project_create_failed",

                "user_id":
                    usuario.id,

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
                "Não foi possível criar o projeto."
            ),
        ) from error


# ============================================================
# CONSULTAR PROJETO
# ============================================================

def consultar_projeto_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Retorna um único AutomationProject ativo pelo ID.

    Parâmetros:
        project_id:
            ID do projeto.

        db:
            Sessão SQLAlchemy.

    Este método será utilizado pelo Studio para recuperar
    os metadados do projeto.

    IMPORTANTE:

    Mantemos propositalmente o with_for_update() existente
    na implementação atual.

    Mesmo sendo uma consulta GET, não vamos alterar essa
    característica durante a modularização para evitar
    qualquer mudança comportamental.
    """

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
            detail=(
                "Projeto não encontrado."
            ),
        )

    return {
        "status": "success",
        "project":
            serializar_projeto(
                projeto
            ),
    }