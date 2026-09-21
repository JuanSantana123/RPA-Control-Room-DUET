# ============================================================
# LIBRARIES - VERSIONS SERVICE
# ============================================================
#
# Regras de negócio das versões publicadas de Libraries.
#
# RESPONSABILIDADES:
#
# - listar LibraryVersions;
# - listar Robots cuja versão atual utiliza uma Library;
# - publicar uma LibraryVersion standalone através de ZIP;
# - promover a nova versão para Produção;
# - desativar versões antigas.
#
# IMPORTANTE:
#
# Este módulo NÃO registra endpoints FastAPI.
#
# O api/libraries.py continuará responsável por:
#
# - Depends();
# - RBAC;
# - Form();
# - File();
# - status_code HTTP do endpoint.
#
# O UploadFile continua chegando ao service porque o processamento
# físico do arquivo faz parte da regra de publicação.
# ============================================================


import logging
import os
import shutil
import tempfile

from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    LibraryVersion,
    Robot,
    RobotVersionLibraryDependency,
)

from libraries.repository import (
    BASE_DIRECTORY,
    LIBRARIES_REPOSITORY,
    MAX_LIBRARY_ZIP_SIZE,
    TEMP_REPOSITORY,
    UPLOAD_CHUNK_SIZE,
)

from libraries.serializers import (
    serializar_library,
    serializar_library_version,
)

from libraries.validators import (
    calcular_sha256,
    obter_library_or_404,
    validar_versao,
    validar_zip_biblioteca,
)


logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR VERSÕES
# ============================================================

def listar_versoes_service(
    library_id: int,
    include_inactive: bool,
    db: Session,
) -> dict:
    """
    Lista as versões publicadas de uma Library.

    include_inactive=False:
        retorna somente LibraryVersions ativas.

    O retorno também informa production_version_id para o
    frontend identificar a versão atualmente vigente.
    """

    library = obter_library_or_404(
        db,
        library_id,
    )

    consulta = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.library_id
            == library_id
        )
    )

    if not include_inactive:

        consulta = consulta.filter(
            LibraryVersion.is_active == 1
        )

    versions = (
        consulta
        .order_by(
            LibraryVersion.published_at.desc(),
            LibraryVersion.id.desc(),
        )
        .all()
    )

    return {
        "status": "success",
        "library_id": library_id,
        "production_version_id": (
            library.production_version_id
        ),
        "total": len(versions),
        "versions": [
            serializar_library_version(
                version,
                library.production_version_id,
            )
            for version in versions
        ],
    }


# ============================================================
# ROBOTS QUE UTILIZAM A LIBRARY
# ============================================================

def listar_robos_da_biblioteca_service(
    library_id: int,
    db: Session,
) -> dict:
    """
    Lista os Robots cuja versão ATUAL publicada utiliza esta
    Library.

    A fonte oficial é RobotVersionLibraryDependency.

    Não inferimos dependências lendo imports Python ou ZIPs.
    """

    # --------------------------------------------------------
    # 1. VALIDA A LIBRARY
    # --------------------------------------------------------

    library = obter_library_or_404(
        db,
        library_id,
    )

    # --------------------------------------------------------
    # 2. VERSÃO ATUAL DE PRODUÇÃO DA LIBRARY
    # --------------------------------------------------------
    #
    # Este valor é apenas contexto.
    #
    # A versão realmente usada por cada Robot vem do snapshot
    # RobotVersionLibraryDependency.
    # --------------------------------------------------------

    production_version = None

    if library.production_version_id is not None:

        production_version = (
            db.query(LibraryVersion)
            .filter(
                LibraryVersion.id
                == library.production_version_id,

                LibraryVersion.library_id
                == library.id,
            )
            .first()
        )

    # --------------------------------------------------------
    # 3. ROBOTS QUE USAM A LIBRARY
    # --------------------------------------------------------
    #
    # CRÍTICO:
    #
    # dependency.robot_version == Robot.version
    #
    # garante que somente o Release ATUAL do Robot apareça.
    # Releases históricos continuam preservados no banco.
    # --------------------------------------------------------

    usages = (
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

            RobotVersionLibraryDependency.robot_version
            == Robot.version,

            # Defesa adicional de integridade do snapshot.
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

    # --------------------------------------------------------
    # 4. RETORNO
    # --------------------------------------------------------

    return {
        "status": "success",

        "library": {
            "id":
                library.id,

            "name":
                library.name,

            "import_name":
                library.import_name,

            "production_version_id":
                library.production_version_id,

            "production_version": (
                production_version.version
                if production_version
                else None
            ),
        },

        "total_robots":
            len(usages),

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

                "uses_production_version": (
                    library.production_version_id
                    == library_version.id
                ),
            }

            for (
                dependency,
                robot,
                library_version,
            )
            in usages
        ],
    }


# ============================================================
# PUBLICAR VERSÃO STANDALONE
# ============================================================

async def publicar_versao_standalone_service(
    library_id: int,
    version: str,
    file: UploadFile,
    db: Session,
    usuario,
) -> dict:
    """
    Publica uma LibraryVersion standalone através de ZIP.

    Exemplo:

        Library.import_name = financeiro

        ZIP:
            financeiro/
                __init__.py
                pagamentos.py
                impostos.py

    FLUXO:

    1. valida Library;
    2. valida Semantic Version;
    3. recebe upload em arquivo temporário;
    4. aplica limite de 50 MB;
    5. valida estrutura do ZIP;
    6. calcula SHA-256;
    7. move snapshot para storage/libraries;
    8. cria LibraryVersion;
    9. promove a nova versão para Produção;
    10. confirma versão + promoção atomicamente no banco.
    """

    library = obter_library_or_404(
        db,
        library_id,
        somente_ativa=True,
    )

    versao = validar_versao(
        version
    )

    filename = (
        file.filename or ""
    ).strip()

    if not filename.lower().endswith(
        ".zip"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A versão da biblioteca precisa ser enviada em um arquivo ZIP."
            ),
        )

    # --------------------------------------------------------
    # VERSÃO JÁ EXISTE?
    # --------------------------------------------------------

    existente = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.library_id
            == library.id,

            LibraryVersion.version
            == versao,
        )
        .first()
    )

    if existente:

        raise HTTPException(
            status_code=409,
            detail=(
                f"A versão {versao} já existe para esta biblioteca."
            ),
        )

    # --------------------------------------------------------
    # DESTINO DEFINITIVO
    # --------------------------------------------------------
    #
    # storage/libraries/<library_id>/<version>/library.zip
    # --------------------------------------------------------

    destino_diretorio = (
        LIBRARIES_REPOSITORY
        / str(library.id)
        / versao
    )

    destino_arquivo = (
        destino_diretorio
        / "library.zip"
    )

    # Snapshot publicado nunca pode ser sobrescrito.
    if destino_diretorio.exists():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um artefato físico para esta versão. "
                "A publicação foi interrompida para evitar sobrescrita."
            ),
        )

    # --------------------------------------------------------
    # ARQUIVO TEMPORÁRIO
    # --------------------------------------------------------

    temp_fd, temp_name = tempfile.mkstemp(
        prefix="library_",
        suffix=".zip",
        dir=TEMP_REPOSITORY,
    )

    # mkstemp abre um descriptor; fechamos antes de manipular
    # através de Path.open().
    os.close(
        temp_fd
    )

    temp_path = Path(
        temp_name
    )

    total_bytes = 0
    artefato_movido = False

    try:

        # ====================================================
        # SALVA UPLOAD COM LIMITE DE TAMANHO
        # ====================================================

        with temp_path.open(
            "wb"
        ) as temp_file:

            while True:

                chunk = await file.read(
                    UPLOAD_CHUNK_SIZE
                )

                if not chunk:
                    break

                total_bytes += len(
                    chunk
                )

                if (
                    total_bytes
                    > MAX_LIBRARY_ZIP_SIZE
                ):

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "O ZIP da biblioteca ultrapassa o limite "
                            "de 50 MB."
                        ),
                    )

                temp_file.write(
                    chunk
                )

        if total_bytes == 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "O arquivo enviado está vazio."
                ),
            )

        # ====================================================
        # VALIDAÇÃO E HASH
        # ====================================================

        validar_zip_biblioteca(
            temp_path,
            library.import_name,
        )

        file_hash = calcular_sha256(
            temp_path
        )

        # ====================================================
        # PUBLICAÇÃO FÍSICA
        # ====================================================

        destino_diretorio.mkdir(
            parents=True,
            exist_ok=False,
        )

        # os.replace() publica o snapshot no destino definitivo.
        os.replace(
            temp_path,
            destino_arquivo,
        )

        artefato_movido = True

        # Persistimos caminho relativo ao BASE_DIRECTORY.
        relative_artifact_path = (
            destino_arquivo
            .relative_to(
                BASE_DIRECTORY
            )
            .as_posix()
        )

        # ====================================================
        # REGISTRA LIBRARY VERSION
        # ====================================================

        library_version = LibraryVersion(
            library_id=library.id,
            version=versao,
            source_type="standalone",
            source_robot_id=None,
            source_robot_version=None,
            source_path=None,
            artifact_path=relative_artifact_path,
            file_hash=file_hash,
            published_by=usuario.id,
            is_active=1,
        )

        db.add(
            library_version
        )

        # ====================================================
        # PROMOVE PARA PRODUÇÃO
        # ====================================================
        #
        # flush():
        #     obtém o ID da LibraryVersion sem commit.
        #
        # Depois:
        #     Library.production_version_id recebe esse ID.
        #
        # commit():
        #     confirma as duas alterações juntas no banco.
        #
        # A versão anterior continua intacta para histórico e
        # Releases antigos.
        # ====================================================

        db.flush()

        library.production_version_id = (
            library_version.id
        )

        db.commit()

        db.refresh(
            library_version
        )

        db.refresh(
            library
        )

        logger.info(
            "Versão de biblioteca publicada",
            extra={
                "event":
                    "library_version_published",
                "user_id":
                    usuario.id,
                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Versão da biblioteca publicada com sucesso."
            ),
            "library": serializar_library(
                library
            ),
            "version": serializar_library_version(
                library_version,
                library.production_version_id,
            ),
        }

    # ========================================================
    # CONFLITO DE INTEGRIDADE
    # ========================================================

    except IntegrityError:

        db.rollback()

        # Se o ZIP já tiver sido movido para o destino definitivo,
        # removemos o diretório físico porque a transação do banco
        # não foi concluída.
        if (
            artefato_movido
            and destino_diretorio.exists()
        ):

            shutil.rmtree(
                destino_diretorio,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=409,
            detail=(
                f"A versão {versao} já existe para esta biblioteca."
            ),
        )

    # ========================================================
    # ERRO HTTP CONTROLADO
    # ========================================================

    except HTTPException:

        db.rollback()

        if (
            artefato_movido
            and destino_diretorio.exists()
        ):

            shutil.rmtree(
                destino_diretorio,
                ignore_errors=True,
            )

        raise

    # ========================================================
    # ERRO NÃO PREVISTO
    # ========================================================

    except Exception as error:

        db.rollback()

        if (
            artefato_movido
            and destino_diretorio.exists()
        ):

            shutil.rmtree(
                destino_diretorio,
                ignore_errors=True,
            )

        logger.exception(
            "Falha ao publicar versão da biblioteca",
            extra={
                "event":
                    "library_version_publish_failed",
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
                "Não foi possível publicar a versão da biblioteca."
            ),
        )

    # ========================================================
    # LIMPEZA GARANTIDA
    # ========================================================

    finally:

        # Fecha o UploadFile independentemente do resultado.
        try:

            await file.close()

        except Exception:
            pass

        # Se o temporário ainda existir, remove.
        #
        # Quando os.replace() foi bem-sucedido, temp_path já não
        # existe e este bloco simplesmente não faz nada.
        if temp_path.exists():

            try:

                temp_path.unlink()

            except Exception:
                pass


# ============================================================
# DESATIVAR VERSÃO
# ============================================================

def desativar_versao_service(
    library_id: int,
    version_id: int,
    db: Session,
    usuario,
) -> dict:
    """
    Desativa uma LibraryVersion para NOVOS vínculos.

    Dependências existentes continuam intactas.
    O snapshot físico também permanece armazenado.

    A versão atualmente vigente em Produção não pode ser
    desativada.
    """

    library = obter_library_or_404(
        db,
        library_id,
    )

    version = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id
            == version_id,

            LibraryVersion.library_id
            == library_id,
        )
        .first()
    )

    if not version:

        raise HTTPException(
            status_code=404,
            detail=(
                "Versão da biblioteca não encontrada."
            ),
        )

    # --------------------------------------------------------
    # PROTEÇÃO DA VERSÃO DE PRODUÇÃO
    # --------------------------------------------------------

    if (
        library.production_version_id
        == version.id
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "A versão vigente em Produção não pode ser desativada. "
                "Publique ou promova outra versão primeiro."
            ),
        )

    # Operação idempotente.
    if not version.is_active:

        return {
            "status": "success",
            "message": (
                "A versão já está desativada."
            ),
            "already_inactive": True,
            "version": serializar_library_version(
                version,
                library.production_version_id,
            ),
        }

    version.is_active = 0

    try:

        db.commit()

        db.refresh(
            version
        )

        logger.info(
            "Versão de biblioteca desativada",
            extra={
                "event":
                    "library_version_deactivated",
                "user_id":
                    usuario.id,
                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message": (
                "Versão desativada com sucesso."
            ),
            "already_inactive": False,
            "version": serializar_library_version(
                version,
                library.production_version_id,
            ),
        }

    except Exception as error:

        db.rollback()

        logger.exception(
            "Falha ao desativar versão da biblioteca",
            extra={
                "event":
                    "library_version_deactivate_failed",
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
                "Não foi possível desativar a versão da biblioteca."
            ),
        )