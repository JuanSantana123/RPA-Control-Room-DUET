# ============================================================
# DUET CORE - ROBOTS - CONSULTAS DE VERSÃO
# ============================================================
#
# Contém operações de leitura ligadas às versões publicadas:
# download da RobotVersion vigente e snapshot exato de Libraries
# utilizado por uma versão específica do Robot.
#
# NÃO registra endpoints FastAPI.
# ============================================================

from fastapi import HTTPException
from fastapi.responses import FileResponse

from database import SessionLocal
from models import (
    Robot,
    RobotVersion,
    Library,
    LibraryVersion,
    RobotVersionLibraryDependency,
)
from releases.service import resolve_robot_version


def download_robot_service(
    robot_id: int
):
    """
    Baixa o artefato da versão atualmente vigente do Robot.

    O Robot continua indicando qual é a versão atual através de:

        Robot.version

    Porém o artefato oficial dessa versão é obtido através de:

        RobotVersion

    Dessa forma o download não depende diretamente do ponteiro
    operacional Robot.file_path utilizado por Agent/Scheduler.
    """

    db = SessionLocal()

    try:

        # ========================================================
        # 1. LOCALIZA O ROBOT
        # ========================================================

        robot = (
            db.query(Robot)
            .filter(
                Robot.id ==
                    robot_id
            )
            .first()
        )


        if not robot:

            raise HTTPException(
                status_code=404,
                detail={
                    "code":
                        "ROBOT_NOT_FOUND",

                    "message":
                        "Não foi possível baixar o Robot porque ele não existe.",

                    "robot_id":
                        robot_id,
                }
            )


        # ========================================================
        # 2. RESOLVE A ROBOTVERSION ATUAL
        # ========================================================
        #
        # Robot.version informa qual versão está vigente.
        #
        # resolve_robot_version() utiliza essa versão exata e
        # valida:
        #
        # - existência do registro RobotVersion;
        # - existência física do artefato;
        # - integridade SHA-256 do arquivo.
        #
        # Portanto o download passa a utilizar a mesma fonte
        # imutável usada pela arquitetura de versionamento.
        # ========================================================

        (
            robot_version,
            caminho_arquivo
        ) = resolve_robot_version(
            db,
            robot.id,
            robot.version
        )


        # ========================================================
        # 3. VALIDA ROBOT x ROBOTVERSION
        # ========================================================
        #
        # O Robot é o ponteiro lógico da versão vigente.
        #
        # A RobotVersion é o snapshot imutável dessa versão.
        #
        # Os hashes precisam representar exatamente os mesmos
        # bytes antes de disponibilizarmos o pacote ao usuário.
        # ========================================================

        if (
            robot.file_hash
            != robot_version.file_hash
        ):

            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "ROBOT_CURRENT_VERSION_HASH_MISMATCH",

                    "message": (
                        f'O Robot "{robot.name}" está inconsistente. '
                        f'O hash registrado no Robot não corresponde '
                        f'à RobotVersion v{robot.version}.'
                    ),

                    "robot_id":
                        robot.id,

                    "robot_version":
                        robot.version,

                    "robot_hash":
                        robot.file_hash,

                    "robot_version_hash":
                        robot_version.file_hash,
                }
            )


        # ========================================================
        # 4. RETORNA O ARTEFATO VALIDADO
        # ========================================================
        #
        # caminho_arquivo já foi validado fisicamente e por
        # SHA-256 dentro de resolve_robot_version().
        #
        # Preferimos também o filename armazenado na RobotVersion,
        # pois ele pertence exatamente ao snapshot baixado.
        # ========================================================

        return FileResponse(
            path=
                str(caminho_arquivo),

            filename=(
                robot_version.filename
                or robot.filename
                or caminho_arquivo.name
            ),

            media_type=
                "application/octet-stream"
        )


    finally:

        # A sessão é encerrada tanto no sucesso quanto em qualquer
        # HTTPException levantada durante as validações.
        db.close()


def list_robot_version_libraries_service(
    robot_id: int,
    robot_version: int
):
    """
    Retorna as bibliotecas e versões exatas utilizadas por um Release.

    Parâmetros:
        robot_id:
            ID do Robot publicado.

        robot_version:
            Versão específica do Robot que será consultada.

    Importante:
        A consulta NÃO utiliza Library.production_version_id
        para descobrir qual versão mostrar.

        O dado principal vem de RobotVersionLibraryDependency,
        garantindo que o resultado represente exatamente o
        snapshot daquele Release.
    """

    db = SessionLocal()

    try:

        # --------------------------------------------------------
        # 1. VALIDA O ROBOT
        # --------------------------------------------------------

        robot = (
            db.query(Robot)
            .filter(
                Robot.id == robot_id
            )
            .first()
        )

        if not robot:
            raise HTTPException(
                status_code=404,
                detail="Robô não encontrado."
            )

        # --------------------------------------------------------
        # --------------------------------------------------------
        # 2. VALIDA A ROBOTVERSION EXATA
        # --------------------------------------------------------
        #
        # Robot.version representa apenas a versão atualmente
        # vigente do Robot.
        #
        # O histórico oficial de versões agora pertence à tabela:
        #
        #     RobotVersion
        #
        # Portanto não inferimos mais que qualquer número entre
        # 1 e Robot.version necessariamente existiu.
        #
        # A versão solicitada precisa possuir um registro
        # RobotVersion real e imutável.
        # --------------------------------------------------------

        robot_version_record = (
            db.query(RobotVersion)
            .filter(
                RobotVersion.robot_id ==
                    robot.id,

                RobotVersion.version ==
                    robot_version
            )
            .first()
        )


        if not robot_version_record:

            raise HTTPException(
                status_code=404,
                detail={
                    "code":
                        "ROBOT_VERSION_NOT_FOUND",

                    "message": (
                        f'A versão v{robot_version} do Robot '
                        f'"{robot.name}" não existe.'
                    ),

                    "robot_id":
                        robot.id,

                    "robot_name":
                        robot.name,

                    "robot_version":
                        robot_version,
                }
            )

        # --------------------------------------------------------
        # 3. BUSCA O SNAPSHOT IMUTÁVEL DO RELEASE
        # --------------------------------------------------------
        #
        # Fazemos JOIN com:
        #
        # RobotVersionLibraryDependency
        #     -> Library
        #     -> LibraryVersion
        #
        # Isso permite devolver tanto o nome amigável da Library
        # quanto a versão exata utilizada pelo Robot.
        # --------------------------------------------------------

        dependencies = (
            db.query(
                RobotVersionLibraryDependency,
                Library,
                LibraryVersion
            )
            .join(
                Library,
                Library.id
                == RobotVersionLibraryDependency.library_id
            )
            .join(
                LibraryVersion,
                LibraryVersion.id
                == RobotVersionLibraryDependency.library_version_id
            )
            .filter(
                RobotVersionLibraryDependency.robot_id
                == robot_id,

                RobotVersionLibraryDependency.robot_version
                == robot_version,

                # Validação adicional de consistência:
                # a LibraryVersion precisa pertencer à mesma
                # Library registrada no snapshot.
                LibraryVersion.library_id
                == RobotVersionLibraryDependency.library_id
            )
            .order_by(
                Library.name
            )
            .all()
        )

        # --------------------------------------------------------
        # 4. RETORNO
        # --------------------------------------------------------

        return {
            "status": "success",

            "robot": {
                "id": robot.id,
                "name": robot.name,

                # Versão cuja composição estamos consultando.
                "version":
                    robot_version,

                # ID estrutural da RobotVersion consultada.
                "robot_version_id":
                    robot_version_record.id,

                # Hash imutável registrado para essa versão.
                "file_hash":
                    robot_version_record.file_hash,

                # Indica se essa é também a versão atualmente
                # vigente no ponteiro lógico Robot.
                "is_current_version": (
                    robot.version ==
                    robot_version
                )
            },

            "total": len(dependencies),

            "libraries": [
                {
                    "library_id": library.id,
                    "name": library.name,
                    "import_name": library.import_name,

                    # ID exato do snapshot imutável utilizado.
                    "library_version_id": library_version.id,

                    # Ex.: 1.0.0, 2.0.0...
                    "version": library_version.version,

                    # Permite futuramente o frontend informar se
                    # esta versão ainda é a vigente em Produção.
                    "is_current_production": (
                        library.production_version_id
                        == library_version.id
                    )
                }

                for (
                    dependency,
                    library,
                    library_version
                ) in dependencies
            ]
        }

    finally:

        # Garante o encerramento da sessão independentemente
        # do resultado da consulta.
        db.close()
