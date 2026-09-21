# ============================================================
# DEVELOPMENT - LIBRARIES SERVICE
# ============================================================
#
# Responsável pelas Libraries utilizadas dentro de um
# AutomationProject em Desenvolvimento.
#
# Este módulo concentra:
#
# - listagem das Libraries vinculadas ao projeto;
# - listagem das novas Working Copies ainda não publicadas;
# - detecção real de alterações nas Working Copies;
# - criação de uma nova Library dentro do projeto.
#
# IMPORTANTE:
#
# Este módulo NÃO representa o catálogo global de Libraries.
#
# O catálogo/versionamento global continua sendo tratado
# pelo domínio de Libraries existente no Control Room.
#
# Este módulo trabalha especificamente com a relação:
#
#     AutomationProject
#           +
#     Library / LibraryVersion
#           +
#     ProjectLibraryDependency
#           +
#     ProjectLibraryDraft
#
# Este arquivo NÃO registra endpoints FastAPI, não utiliza
# Depends e não aplica RBAC.
# ============================================================


import logging
import shutil

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    Library,
    LibraryVersion,
    ProjectLibraryDependency,
    ProjectLibraryDraft,
)

from development.workspace_core import (
    draft_has_changes,
    draft_path,
    draft_workspace_value,
)

from development.checkout_service import (
    exigir_checkout_workspace,
)

from development.repository import (
    garantir_workspace,
    montar_arvore_workspace,
)

from schemas.development import (
    DevelopmentLibraryCreate,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR BIBLIOTECAS DO PROJETO
# ============================================================

def listar_bibliotecas_projeto_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Lista Libraries publicadas vinculadas ao projeto e novas
    Working Copies ainda sem LibraryVersion.

    Uma Library nova pode existir somente como:

        ProjectLibraryDraft

    enquanto ainda não tiver sido publicada pela primeira vez.
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
    # DEPENDÊNCIAS PUBLICADAS
    # ========================================================
    #
    # Cada dependência aponta para uma LibraryVersion exata.
    #
    # Isso é importante porque a Working Copy precisa ser
    # comparada com a versão realmente utilizada pelo projeto,
    # e não simplesmente com a versão atual de Produção.
    # ========================================================

    dependencies = (
        db.query(
            ProjectLibraryDependency,
            Library,
            LibraryVersion,
        )
        .join(
            Library,
            Library.id ==
                ProjectLibraryDependency.library_id,
        )
        .join(
            LibraryVersion,
            LibraryVersion.id ==
                ProjectLibraryDependency.library_version_id,
        )
        .filter(
            ProjectLibraryDependency.project_id ==
                project_id
        )
        .order_by(
            Library.name.asc(),
            Library.id.asc(),
        )
        .all()
    )

    # ========================================================
    # WORKING COPIES
    # ========================================================

    drafts = (
        db.query(
            ProjectLibraryDraft,
            Library,
        )
        .join(
            Library,
            Library.id ==
                ProjectLibraryDraft.library_id,
        )
        .filter(
            ProjectLibraryDraft.project_id ==
                project_id
        )
        .all()
    )

    # Acesso rápido à Working Copy de cada Library.
    drafts_by_library = {
        library.id: draft
        for draft, library in drafts
    }

    result = []

    # IDs que já aparecem como dependência publicada.
    #
    # Depois utilizamos esse conjunto para identificar as
    # Libraries realmente novas, que possuem apenas Draft.
    linked_library_ids = set()

    # ========================================================
    # LIBRARIES VINCULADAS A VERSÕES PUBLICADAS
    # ========================================================

    for (
        dependency,
        library,
        version,
    ) in dependencies:

        linked_library_ids.add(
            library.id
        )

        draft = drafts_by_library.get(
            library.id
        )

        # ====================================================
        # ALTERAÇÃO REAL DA WORKING COPY
        # ====================================================
        #
        # Não confiamos somente em:
        #
        #     draft.is_modified
        #
        # porque essa flag pode ficar desatualizada.
        #
        # A fonte de verdade é:
        #
        #     conteúdo atual da Working Copy
        #               versus
        #     LibraryVersion exata do projeto
        # ====================================================

        try:

            is_modified = (
                draft_has_changes(
                    project_id,
                    library,
                    version,
                )
                if draft
                else False
            )

        except RuntimeError as error:

            # Uma versão publicada corrompida ou uma Working
            # Copy inválida não pode aparecer silenciosamente
            # como "sem alterações".
            raise HTTPException(
                status_code=409,
                detail=(
                    f'Não foi possível comparar a biblioteca '
                    f'"{library.name}" com a versão '
                    f'{version.version}: {error}'
                ),
            )

        result.append(
            {
                "library_id":
                    library.id,

                "name":
                    library.name,

                "import_name":
                    library.import_name,

                "description":
                    library.description,

                "state":
                    "linked",

                "is_new":
                    False,

                # Estado efetivo calculado a partir dos
                # arquivos físicos.
                "is_modified":
                    is_modified,

                "dependency_id":
                    dependency.id,

                "library_version_id":
                    version.id,

                "version":
                    version.version,

                "production_version_id":
                    library.production_version_id,

                "draft_id": (
                    draft.id
                    if draft
                    else None
                ),
            }
        )

    # ========================================================
    # LIBRARIES NOVAS
    # ========================================================
    #
    # Uma Library criada dentro do projeto ainda não possui
    # ProjectLibraryDependency nem LibraryVersion.
    #
    # Ela existe apenas como Library + ProjectLibraryDraft.
    # ========================================================

    for draft, library in drafts:

        if library.id in linked_library_ids:
            continue

        result.append(
            {
                "library_id":
                    library.id,

                "name":
                    library.name,

                "import_name":
                    library.import_name,

                "description":
                    library.description,

                "state":
                    "new",

                "is_new":
                    True,

                "is_modified":
                    True,

                "dependency_id":
                    None,

                "library_version_id":
                    None,

                "version":
                    None,

                "production_version_id":
                    library.production_version_id,

                "draft_id":
                    draft.id,
            }
        )

    # ========================================================
    # ORDENAÇÃO FINAL
    # ========================================================

    result.sort(
        key=lambda item: (
            item["name"].lower(),
            item["library_id"],
        )
    )

    return {
        "status": "success",
        "project_id": project_id,
        "total": len(result),
        "libraries": result,
    }


# ============================================================
# CRIAR NOVA BIBLIOTECA NO PROJETO
# ============================================================

def criar_biblioteca_projeto_service(
    project_id: int,
    request: DevelopmentLibraryCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Cria uma Library nova como Working Copy pertencente ao
    AutomationProject.

    Fluxo:

        Library
            is_active = 0
            production_version_id = NULL

                    +

        ProjectLibraryDraft
            base_library_version_id = NULL

                    +

        workspaces/{project_id}/
            _libraries/
                {import_name}/
                    __init__.py

    A Library somente passa a fazer parte do catálogo de
    Produção depois do primeiro Release.
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
    # CHECKOUT OBRIGATÓRIO
    # ========================================================
    #
    # Criar uma Library altera fisicamente o Workspace.
    # Portanto o usuário precisa possuir o Checkout.
    # ========================================================

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    # ========================================================
    # NOME
    # ========================================================

    nome = request.name.strip()

    if not nome:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome da biblioteca não pode ficar vazio."
            ),
        )

    # ========================================================
    # IMPORT NAME
    # ========================================================
    #
    # Reutilizamos a MESMA validação já utilizada pelo
    # domínio global de Libraries.
    #
    # O import permanece local para evitar dependência
    # circular durante a inicialização dos routers.
    # ========================================================

    # ============================================================
    # VALIDAÇÃO DO NAMESPACE DA LIBRARY
    # ============================================================
    #
    # A validação pertence ao domínio Libraries e não ao router HTTP.
    # Isso evita que Development dependa internamente de
    # api/libraries.py.
    # ============================================================

    from libraries.validators import validar_import_name

    import_name = validar_import_name(
        request.import_name
    )

    # ========================================================
    # DESCRIÇÃO
    # ========================================================

    descricao = (
        request.description.strip()
        if request.description
        else None
    )

    # ========================================================
    # IMPORT_NAME GLOBALMENTE ÚNICO
    # ========================================================

    existente = (
        db.query(Library)
        .filter(
            func.lower(
                Library.import_name
            ) ==
                import_name.lower()
        )
        .first()
    )

    if existente:

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma biblioteca utilizando este "
                "import_name. Adicione a biblioteca existente "
                "ao projeto em vez de criar outra."
            ),
        )

    # ========================================================
    # WORKSPACE DO PROJETO
    # ========================================================

    workspace_path = (
        garantir_workspace(
            project_id
        )
    )

    # ========================================================
    # COLISÃO COM CÓDIGO DO PRÓPRIO PROJETO
    # ========================================================
    #
    # Durante execução/publicação, o namespace da Library será
    # colocado na raiz do ZIP.
    #
    # Portanto:
    #
    #     import_name/
    #
    # ou:
    #
    #     import_name.py
    #
    # já existentes na raiz do projeto causariam colisão.
    # ========================================================

    if (
        (
            workspace_path /
            import_name
        ).exists()

        or

        (
            workspace_path /
            f"{import_name}.py"
        ).exists()
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe código do projeto utilizando este "
                "namespace na raiz. Renomeie-o antes de criar "
                "a biblioteca."
            ),
        )

    # ========================================================
    # WORKING COPY DA LIBRARY
    # ========================================================

    target = draft_path(
        project_id,
        import_name,
    )

    if target.exists():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma pasta de Working Copy "
                "com este namespace."
            ),
        )

    # ========================================================
    # REGISTRO DA LIBRARY
    # ========================================================

    library = Library(
        name=nome,
        import_name=import_name,
        description=descricao,
        folder_id=None,
        production_version_id=None,
        created_by=usuario.id,

        # ----------------------------------------------------
        # IMPORTANTE
        # ----------------------------------------------------
        #
        # Uma Library nova criada em Desenvolvimento ainda
        # NÃO pertence ao catálogo de Produção.
        #
        # O Release será responsável por ativá-la quando
        # criar sua primeira versão publicada.
        # ----------------------------------------------------
        is_active=0,
    )

    # Informa se esta tentativa chegou a criar fisicamente
    # a Working Copy.
    #
    # Em caso de erro posterior, somente então removemos
    # esse diretório.
    created_target = False

    try:

        # ====================================================
        # CRIA LIBRARY NO BANCO SEM COMMIT
        # ====================================================

        db.add(
            library
        )

        # Precisamos do library.id para criar o Draft.
        db.flush()

        # ====================================================
        # CRIA WORKING COPY
        # ====================================================

        target.mkdir(
            parents=True,
            exist_ok=False,
        )

        created_target = True

        # ----------------------------------------------------
        # __init__.py INICIAL
        # ----------------------------------------------------

        (
            target /
            "__init__.py"
        ).write_text(
            (
                "# ============================================================\n"
                "# DUET CORE - BIBLIOTECA\n"
                "# ============================================================\n"
                "\n"
            ),
            encoding="utf-8",
        )

        # ====================================================
        # DRAFT
        # ====================================================

        draft = ProjectLibraryDraft(
            project_id=project_id,
            library_id=library.id,

            # Library nova não possui versão-base.
            base_library_version_id=None,

            workspace_path=
                draft_workspace_value(
                    project_id,
                    import_name,
                ),

            is_modified=1,
            created_by=usuario.id,
            updated_by=usuario.id,
        )

        db.add(
            draft
        )

        # ====================================================
        # COMMIT ÚNICO
        # ====================================================

        db.commit()

        db.refresh(
            library
        )

        db.refresh(
            draft
        )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Biblioteca criada dentro do projeto",
            extra={
                "event":
                    "development_library_created",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "library_id":
                    library.id,

                "import_name":
                    library.import_name,

                "status":
                    "success",
            },
        )

        # ====================================================
        # RETORNO
        # ====================================================
        #
        # A árvore é devolvida imediatamente para o Studio
        # conseguir atualizar o Explorer sem F5.
        # ====================================================

        return {
            "status": "success",
            "message": (
                "Biblioteca criada no projeto com sucesso."
            ),

            "library": {
                "library_id":
                    library.id,

                "name":
                    library.name,

                "import_name":
                    library.import_name,

                "description":
                    library.description,

                "state":
                    "new",

                "is_new":
                    True,

                "is_modified":
                    True,

                "dependency_id":
                    None,

                "library_version_id":
                    None,

                "version":
                    None,

                "production_version_id":
                    None,

                "draft_id":
                    draft.id,
            },

            "tree":
                montar_arvore_workspace(
                    workspace_path,
                    workspace_path,
                ),
        }

    # ========================================================
    # HTTP EXCEPTION
    # ========================================================

    except HTTPException:

        db.rollback()

        if created_target:

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

        raise

    # ========================================================
    # CONFLITO DE INTEGRIDADE
    # ========================================================

    except IntegrityError:

        db.rollback()

        if created_target:

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma biblioteca utilizando "
                "este import_name."
            ),
        )

    # ========================================================
    # ERRO INESPERADO
    # ========================================================

    except Exception as error:

        db.rollback()

        if created_target:

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

        logger.exception(
            "Falha ao criar biblioteca dentro do projeto",
            extra={
                "event":
                    "development_library_create_failed",

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
                "Não foi possível criar a biblioteca "
                "no projeto."
            ),
        )