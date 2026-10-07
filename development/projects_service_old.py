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
# - validação de nome duplicado;
# - definição do estágio inicial BACKLOG;
# - captura da versão do Robot de origem;
# - restauração do workspace de um Robot publicado;
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
) -> dict:
    """
    Cria um novo AutomationProject.

    Parâmetros:
        request:
            Dados validados pelo schema
            AutomationProjectCreate.

        db:
            Sessão SQLAlchemy da requisição.

        usuario:
            Usuário autenticado recebido pelo router.

    Regras preservadas:

        1. A publicação é serializada através de
           lock_publication(db).

        2. Todo projeto novo nasce com:

               status = "draft"

        3. Todo projeto novo nasce no estágio:

               BACKLOG

        4. Um projeto em andamento não pode reutilizar o
           mesmo nome dentro da mesma pasta.

        5. Projetos na Lixeira não bloqueiam reutilização
           do nome.

        6. Projetos no estágio PUBLISHED não bloqueiam
           reutilização do nome.

        7. Registros legados com current_stage_id=None
           continuam sendo considerados conflito.

        8. Quando base_robot_id for informado:

               - o Robot precisa existir;
               - sua versão atual é capturada;
               - o workspace publicado é restaurado;
               - a restauração acontece antes do commit.

        9. Se a criação falhar antes do commit, qualquer
           workspace restaurado nesta tentativa é removido.
    """

    # ========================================================
    # LOCK DE PUBLICAÇÃO
    # ========================================================
    #
    # Esta chamada já existe no fluxo atual e precisa ocorrer
    # antes das validações/criação.
    #
    # Ela protege a consistência entre Development, Robots,
    # Libraries e Release durante operações concorrentes.
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

    if not nome:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome do projeto não pode ficar vazio."
            ),
        )

    # ========================================================
    # VALIDA PASTA
    # ========================================================

    if request.folder_id is not None:

        pasta = (
            db.query(DevelopmentFolder)
            .filter(
                DevelopmentFolder.id ==
                    request.folder_id,

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
    # PUBLISHED possui uma função importante na validação
    # de duplicidade.
    #
    # Um projeto já publicado continua ativo no histórico
    # de Development, mas não deve reservar seu nome para
    # sempre.
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
    #
    # Inicialmente buscamos:
    #
    # - somente projetos ativos;
    # - com mesmo nome;
    # - ignorando diferenças entre maiúsculas/minúsculas.
    #
    # Depois restringimos:
    #
    # - estágio;
    # - localização na árvore.
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

    # --------------------------------------------------------
    # IGNORA PROJETOS JÁ PUBLICADOS
    # --------------------------------------------------------
    #
    # current_stage_id=None continua sendo considerado
    # conflito para preservar registros legados.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MESMO LOCAL DA ÁRVORE
    # --------------------------------------------------------

    if request.folder_id is None:

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
                    request.folder_id
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
    #
    # Essas variáveis também são utilizadas na estratégia
    # de rollback do workspace.
    # ========================================================

    # Versão e nome histórico do Robot utilizado como origem.
    #
    # Permanecem None quando o projeto é criado do zero.
    base_version = None
    base_robot_name = None

    restored_workspace = None

    project_committed = False

    # A variável somente será utilizada posteriormente quando
    # base_robot_id estiver preenchido.
    robot_base = None

    if request.base_robot_id is not None:

        robot_base = (
            db.query(Robot)
            .filter(
                Robot.id ==
                    request.base_robot_id
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

        # Captura a versão do Robot exatamente no momento
        # da criação do projeto.
        base_version = (
            robot_base.version
        )

        # Captura também o nome do Robot como snapshot histórico.
        #
        # Depois disso, a identificação visual da origem não depende
        # de o registro do Robot continuar existindo futuramente.
        base_robot_name = (
            robot_base.name
        )
        

    # ========================================================
    # ESTÁGIO INICIAL DO WORKFLOW
    # ========================================================
    #
    # Não utilizamos ID numérico fixo.
    #
    # BACKLOG é localizado através de seu code estável.
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
        folder_id=request.folder_id,

        # Todo projeto novo começa como draft.
        status="draft",

        # Todo projeto novo entra no BACKLOG.
        current_stage_id=backlog.id,

        # Proveniência do Robot publicado.
        #
        # base_robot_id:
        #     vínculo técnico enquanto o Robot existir.
        #
        # base_robot_name:
        #     snapshot histórico independente da existência futura
        #     do Robot.
        #
        # base_version:
        #     versão utilizada para criar o workspace.
        base_robot_id=request.base_robot_id,
        base_robot_name=base_robot_name,
        base_version=base_version,

        created_by=usuario.id,
        is_active=1,
    )

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    try:

        db.add(
            projeto
        )

        # ----------------------------------------------------
        # FLUSH ANTES DA RESTAURAÇÃO
        # ----------------------------------------------------
        #
        # O projeto precisa possuir ID antes que seu workspace
        # possa ser restaurado.
        #
        # flush envia o INSERT para o banco sem confirmar
        # definitivamente a transação.
        # ----------------------------------------------------

        db.flush()

        # ----------------------------------------------------
        # RESTAURA ROBOT PUBLICADO
        # ----------------------------------------------------
        #
        # Somente ocorre quando o projeto foi criado a partir
        # de um Robot existente.
        #
        # A restauração ocorre ANTES do commit para que banco
        # e filesystem façam parte do mesmo fluxo lógico.
        # ----------------------------------------------------

        if request.base_robot_id is not None:

            restored_workspace = (
                restore_project_from_robot(
                    db,
                    projeto,
                    robot_base,
                    usuario.id,
                )
            )
            # ------------------------------------------------
            # VALIDA WORKSPACE RESTAURADO
            # ------------------------------------------------
            #
            # Neste ponto:
            #
            # - o projeto já recebeu ID através do db.flush();
            # - o Robot de origem já foi restaurado;
            # - restored_workspace contém o caminho criado;
            # - a transação ainda não recebeu commit.
            #
            # Portanto, podemos validar com segurança que o
            # Workspace restaurado corresponde exatamente ao
            # Workspace oficial pertencente ao projeto.
            # ------------------------------------------------

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
        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        db.commit()

        # A partir daqui não podemos mais considerar o projeto
        # como uma criação não confirmada.
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
            "status": "success",
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
                # Não escondemos uma falha de limpeza, mas também
                # não substituímos a HTTPException funcional que
                # originou o rollback.
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

        # Preserva a HTTPException original.
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
        )


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