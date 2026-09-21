# ============================================================
# DEVELOPMENT - RELEASE SERVICE
# ============================================================
#
# Integra o domínio de Desenvolvimento com o mecanismo global
# de Release do DUET CORE.
#
# Este módulo concentra:
#
# - prévia de Release de um AutomationProject;
# - estrutura de Robots de Produção disponíveis como origem
#   para projetos de Desenvolvimento.
#
# IMPORTANTE:
#
# A publicação efetiva:
#
#     APPROVED -> PUBLISHED
#
# continua em:
#
#     development/workflow_service.py
#
# porque essa operação também altera o Workflow do projeto.
#
# O mecanismo global de montagem/publicação continua em:
#
#     release_service.py
#
# na raiz do projeto.
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - utiliza Depends;
# - realiza autenticação;
# - aplica RBAC.
#
# Essas responsabilidades permanecem em:
#
#     api/development.py
# ============================================================


import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    Robot,
    RobotFolder,
)

# ============================================================
# RELEASE SERVICE GLOBAL
# ============================================================
#
# ATENÇÃO:
#
# Este import aponta propositalmente para:
#
#     RPA-Control-Room/release_service.py
#
# e NÃO para este próprio arquivo.
#
# Como este módulo é:
#
#     development.release_service
#
# o import absoluto abaixo continua resolvendo o módulo global
# responsável pela infraestrutura real de Release.
# ============================================================

from releases.service import (
    lock_publication,
    preview_release,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# CONSULTAR PRÉVIA DE RELEASE
# ============================================================

def consultar_previa_release_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Calcula a prévia de Release de um AutomationProject.

    Esta operação NÃO cria:

    - Robot;
    - pasta de Robot;
    - nova versão de Robot;
    - nova LibraryVersion.

    O objetivo é validar e apresentar antecipadamente o que
    será produzido pela publicação.
    """

    # ========================================================
    # LOCK DE PUBLICAÇÃO
    # ========================================================
    #
    # Utilizamos a mesma trava global usada pelo fluxo real
    # de Release.
    #
    # Isso preserva o comportamento atual do backend e evita
    # que a prévia observe um estado intermediário de outra
    # publicação concorrente.
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
    # MONTA PRÉVIA
    # ========================================================

    try:

        return preview_release(
            db,
            projeto,
        )

    # ========================================================
    # ERROS FUNCIONAIS
    # ========================================================
    #
    # HTTPExceptions geradas pelo mecanismo de Release já
    # possuem status/detail apropriados e devem chegar ao
    # frontend sem alteração.
    # ========================================================

    except HTTPException:
        raise

    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception:

        logger.exception(
            "Falha ao preparar prévia de Release"
        )

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível montar o projeto. "
                "Confira o workspace, as Bibliotecas "
                "e o log do Control Room."
            ),
        )


# ============================================================
# LISTAR ROBOTS DISPONÍVEIS COMO ORIGEM
# ============================================================

def listar_robos_origem_release_service(
    db: Session,
) -> dict:
    """
    Retorna a estrutura de Produção necessária para seleção
    de um Robot como origem de um AutomationProject.

    A resposta contém:

        folders:
            árvore lógica das pastas de Robots.

        robots:
            Robots publicados com pasta e versão atual.

    O campo folder_label permanece temporariamente para
    compatibilidade com o frontend atual.
    """

    # ========================================================
    # PASTAS DE ROBOTS
    # ========================================================
    #
    # Carregamos os objetos completos para permitir que o
    # frontend reconstrua a mesma hierarquia utilizada pela
    # área de Robots.
    # ========================================================

    robot_folders = (
        db.query(RobotFolder)
        .order_by(
            RobotFolder.name.asc(),
            RobotFolder.id.asc(),
        )
        .all()
    )

    # ========================================================
    # MAPA DE PASTAS
    # ========================================================
    #
    # Utilizado para gerar o breadcrumb legado:
    #
    #     Financeiro / Faturamento
    #
    # Esse campo continua sendo devolvido enquanto o frontend
    # migra completamente para navegação pela árvore.
    # ========================================================

    folders_by_id = {
        folder.id: folder
        for folder in robot_folders
    }

    # ========================================================
    # BREADCRUMB DA PASTA
    # ========================================================

    def folder_label(
        folder_id: int | None,
    ) -> str:
        """
        Monta o caminho amigável de uma pasta.

        Exemplo:

            Financeiro / Faturamento

        O conjunto visited impede loop infinito caso existam
        dados inconsistentes na hierarquia de pastas.
        """

        parts: list[str] = []

        visited: set[int] = set()

        current_folder_id = (
            folder_id
        )

        while (
            current_folder_id is not None
            and current_folder_id not in visited
        ):

            visited.add(
                current_folder_id
            )

            folder = folders_by_id.get(
                current_folder_id
            )

            # Se houver referência para uma pasta inexistente,
            # interrompemos o breadcrumb sem derrubar toda a
            # resposta.
            if folder is None:
                break

            parts.insert(
                0,
                folder.name,
            )

            current_folder_id = (
                folder.parent_id
            )

        return (
            " / ".join(parts)
            or "Raiz de Robôs"
        )

    # ========================================================
    # ROBOTS DE PRODUÇÃO
    # ========================================================

    robots = (
        db.query(Robot)
        .order_by(
            Robot.name.asc(),
            Robot.id.asc(),
        )
        .all()
    )

    # ========================================================
    # RESPOSTA
    # ========================================================

    return {
        "status": "success",

        # ----------------------------------------------------
        # ESTRUTURA REAL DAS PASTAS
        # ----------------------------------------------------
        #
        # Exemplo:
        #
        # Raiz de Robôs
        #   └── Financeiro
        #       └── Faturamento
        # ----------------------------------------------------

        "folders": [
            {
                "id":
                    folder.id,

                "name":
                    folder.name,

                "parent_id":
                    folder.parent_id,
            }

            for folder in robot_folders
        ],

        # ----------------------------------------------------
        # ROBOTS
        # ----------------------------------------------------

        "robots": [
            {
                "id":
                    robot.id,

                "name":
                    robot.name,

                "version":
                    robot.version,

                # Permite ao frontend relacionar diretamente
                # o Robot ao nó correto da árvore.
                "folder_id":
                    robot.folder_id,

                # Compatibilidade temporária com o seletor
                # antigo do frontend.
                "folder_label":
                    folder_label(
                        robot.folder_id
                    ),
            }

            for robot in robots
        ],
    }