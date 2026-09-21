# ============================================================
# LIBRARIES - CATALOG SERVICE
# ============================================================
#
# Regras de negócio do catálogo global de Libraries.
#
# RESPONSABILIDADES:
#
# - listar Libraries;
# - criar identidade de uma Library;
# - consultar Library;
# - atualizar metadados;
# - desativar Library com proteção de dependências em Produção.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints FastAPI.
# RBAC continuará no api/libraries.py.
#
# Nenhuma LibraryVersion é criada automaticamente ao cadastrar
# uma Library.
# ============================================================


import logging

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    Library,
    LibraryVersion,
    Robot,
    RobotVersionLibraryDependency,
)

from schemas.libraries import (
    LibraryCreate,
    LibraryUpdate,
)

from libraries.serializers import (
    serializar_library,
)

from libraries.validators import (
    obter_library_or_404,
    validar_destino_pasta,
    validar_import_name,
)


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR LIBRARIES
# ============================================================

def listar_bibliotecas_service(
    include_inactive: bool,
    db: Session,
) -> dict:
    """
    Lista Libraries cadastradas.

    include_inactive=False:
        retorna somente Libraries ativas.
    """

    consulta = (
        db.query(Library)
    )

    if not include_inactive:

        consulta = consulta.filter(
            Library.is_active == 1
        )

    libraries = (
        consulta
        .order_by(
            func.lower(
                Library.name
            ).asc(),
            Library.id.asc(),
        )
        .all()
    )

    return {
        "status": "success",
        "total": len(libraries),
        "libraries": [
            serializar_library(
                library
            )
            for library in libraries
        ],
    }


# ============================================================
# CRIAR LIBRARY
# ============================================================

def criar_biblioteca_service(
    request: LibraryCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Cria a identidade de uma Library.

    Nenhuma versão é publicada automaticamente.

    O import_name funciona como namespace Python estável e
    precisa ser único no catálogo.
    """

    nome = (
        request.name
        .strip()
    )

    import_name = validar_import_name(
        request.import_name
    )

    descricao = (
        request.description.strip()
        if request.description
        else None
    )

    # Confirma que a pasta organizacional existe e está ativa.
    #
    # None representa a raiz do catálogo.
    validar_destino_pasta(
        db,
        request.folder_id,
    )

    if not nome:

        raise HTTPException(
            status_code=400,
            detail=(
                "O nome da biblioteca não pode ficar vazio."
            ),
        )

    # O namespace Python é único independentemente de maiúsculas
    # e minúsculas.
    import_existente = (
        db.query(Library)
        .filter(
            func.lower(
                Library.import_name
            )
            == import_name.lower()
        )
        .first()
    )

    if import_existente:

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma biblioteca utilizando este import_name."
            ),
        )

    library = Library(
        name=nome,
        import_name=import_name,
        description=descricao,
        folder_id=request.folder_id,
        created_by=usuario.id,
        is_active=1,
    )

    try:

        db.add(
            library
        )

        db.commit()

        db.refresh(
            library
        )

        logger.info(
            "Biblioteca criada",
            extra={
                "event": "library_created",
                "user_id": usuario.id,
                "status": "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Biblioteca criada com sucesso."
            ),
            "library": serializar_library(
                library
            ),
        }

    # A consulta anterior melhora a mensagem para o usuário,
    # mas a constraint do banco continua sendo a proteção final
    # contra concorrência.
    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma biblioteca utilizando este import_name."
            ),
        )

    except HTTPException:
        raise

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao criar biblioteca",
            extra={
                "event": "library_create_failed",
                "user_id": usuario.id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível criar a biblioteca."
            ),
        )


# ============================================================
# CONSULTAR LIBRARY
# ============================================================

def consultar_biblioteca_service(
    library_id: int,
    db: Session,
) -> dict:
    """
    Consulta uma Library pelo ID.

    A Library é retornada mesmo quando está desativada para
    preservar auditoria e referências históricas.
    """

    library = obter_library_or_404(
        db,
        library_id,
    )

    total_versions = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.library_id
            == library.id
        )
        .count()
    )

    active_versions = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.library_id
            == library.id,
            LibraryVersion.is_active == 1,
        )
        .count()
    )

    return {
        "status": "success",
        "library": {
            **serializar_library(
                library
            ),
            "total_versions":
                total_versions,
            "active_versions":
                active_versions,
        },
    }


# ============================================================
# ATUALIZAR LIBRARY
# ============================================================

def atualizar_biblioteca_service(
    library_id: int,
    request: LibraryUpdate,
    db: Session,
    usuario,
) -> dict:
    """
    Atualiza somente os metadados amigáveis da Library.

    O import_name é propositalmente imutável nesta operação
    porque representa o contrato técnico dos imports Python.
    """

    library = obter_library_or_404(
        db,
        library_id,
    )

    dados = request.model_dump(
        exclude_unset=True
    )

    if not dados:

        raise HTTPException(
            status_code=400,
            detail=(
                "Nenhum campo foi informado para atualização."
            ),
        )

    if "name" in dados:

        nome = (
            dados["name"]
            .strip()
        )

        if not nome:

            raise HTTPException(
                status_code=400,
                detail=(
                    "O nome da biblioteca não pode ficar vazio."
                ),
            )

        library.name = nome

    if "description" in dados:

        descricao = dados[
            "description"
        ]

        library.description = (
            descricao.strip()
            if descricao
            else None
        )

    try:

        db.commit()

        db.refresh(
            library
        )

        logger.info(
            "Biblioteca atualizada",
            extra={
                "event": "library_updated",
                "user_id": usuario.id,
                "status": "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Biblioteca atualizada com sucesso."
            ),
            "library": serializar_library(
                library
            ),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao atualizar biblioteca",
            extra={
                "event": "library_update_failed",
                "user_id": usuario.id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível atualizar a biblioteca."
            ),
        )


# ============================================================
# DESATIVAR LIBRARY
# ============================================================

def desativar_biblioteca_service(
    library_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Desativa logicamente uma Library.

    Nenhum artefato ou dependência histórica é removido.

    REGRA CRÍTICA:

    A Library não pode ser desativada enquanto o Release ATUAL
    de algum Robot publicado depender dela.
    """

    library = obter_library_or_404(
        db,
        library_id,
    )

    # Operação idempotente.
    if not library.is_active:

        return {
            "status": "success",
            "message": (
                "A biblioteca já está desativada."
            ),
            "already_inactive": True,
            "library": serializar_library(
                library
            ),
        }

    # ========================================================
    # PROTEÇÃO DE PRODUÇÃO
    # ========================================================
    #
    # Apenas o Release ATUAL de cada Robot participa desta
    # validação.
    #
    # Releases históricos continuam preservados, mas não impedem
    # aposentadoria futura da Library.
    #
    # Para desativar:
    #
    # 1. remover a Library no Desenvolvimento do Robot;
    # 2. publicar uma nova versão do Robot;
    # 3. repetir para os demais Robots dependentes;
    # 4. quando nenhum Release atual depender dela, desativar.
    # ========================================================

    robots_em_uso = (
        db.query(
            RobotVersionLibraryDependency,
            Robot,
            LibraryVersion,
        )
        .join(
            Robot,
            Robot.id
            == RobotVersionLibraryDependency.robot_id,
        )
        .join(
            LibraryVersion,
            LibraryVersion.id
            == RobotVersionLibraryDependency.library_version_id,
        )
        .filter(
            RobotVersionLibraryDependency.library_id
            == library.id,

            # Considera somente a versão atual publicada do Robot.
            RobotVersionLibraryDependency.robot_version
            == Robot.version,

            # Defesa adicional para garantir consistência entre
            # dependency.library_id e LibraryVersion.library_id.
            LibraryVersion.library_id
            == library.id,
        )
        .order_by(
            func.lower(
                Robot.name
            ),
            Robot.id,
        )
        .all()
    )

    if robots_em_uso:

        # Texto amigável utilizado pela resposta visual.
        descricao_robots = ", ".join(
            (
                f"{robot.name} "
                f"v{dependency.robot_version} "
                f"(Library {library_version.version})"
            )
            for (
                dependency,
                robot,
                library_version,
            )
            in robots_em_uso
        )

        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "LIBRARY_IN_USE_BY_ROBOTS",

                "message": (
                    f'Não foi possível desativar a biblioteca '
                    f'"{library.name}". '
                    f'Ela é utilizada por '
                    f'{len(robots_em_uso)} Robot(s) em Produção: '
                    f'{descricao_robots}. '
                    f'Remova a dependência desses Robots '
                    f'antes de tentar novamente.'
                ),

                "library_id":
                    library.id,

                "library_name":
                    library.name,

                "total_robots":
                    len(robots_em_uso),

                # Dados estruturados para o frontend poder exibir
                # os Robots que estão bloqueando a operação.
                "robots": [
                    {
                        "robot_id":
                            robot.id,

                        "robot_name":
                            robot.name,

                        "robot_version":
                            dependency.robot_version,

                        "library_version_id":
                            library_version.id,

                        "library_version":
                            library_version.version,
                    }

                    for (
                        dependency,
                        robot,
                        library_version,
                    )
                    in robots_em_uso
                ],
            },
        )

    # Nenhum Release atual utiliza a Library.
    # A desativação lógica agora é segura.
    library.is_active = 0

    try:

        db.commit()

        db.refresh(
            library
        )

        logger.info(
            "Biblioteca desativada",
            extra={
                "event": "library_deactivated",
                "user_id": usuario.id,
                "status": "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Biblioteca desativada com sucesso."
            ),
            "already_inactive": False,
            "library": serializar_library(
                library
            ),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao desativar biblioteca",
            extra={
                "event": "library_deactivate_failed",
                "user_id": usuario.id,
                "status": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível desativar a biblioteca."
            ),
        )