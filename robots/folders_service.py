# ============================================================
# DUET CORE - ROBOTS - SERVIÇO DE PASTAS
# ============================================================
#
# Agrupa a lógica existente de criação, exclusão e consulta das
# RobotFolders e das listagens de Robots por localização.
#
# NÃO registra endpoints FastAPI e NÃO altera regras de RBAC.
# ============================================================

from fastapi import HTTPException

from database import SessionLocal
from models import Robot, RobotFolder
from releases.service import lock_publication
from schemas.robots import RobotFolderRequest


def delete_robot_folder_service(
    folder_id: int
):
    """
    Exclui uma pasta de Robots somente quando ela estiver vazia.

    Regras:

    - pasta inexistente -> HTTP 404;
    - possui Robots     -> HTTP 409;
    - possui subpastas  -> HTTP 409;
    - pasta vazia       -> exclusão permitida.

    IMPORTANTE:

    Esta rota NÃO exclui Robots automaticamente e NÃO remove
    arquivos físicos de Robots.

    A exclusão de um Robot deve obrigatoriamente passar por:

        DELETE /robots/{robot_id}

    Dessa forma nenhuma pasta consegue contornar as validações
    de Libraries, Schedules, Desenvolvimento ou histórico.
    """

    db = SessionLocal()

    try:

        # ========================================================
        # 1. SERIALIZA ALTERAÇÕES NO CATÁLOGO DE PRODUÇÃO
        # ========================================================
        #
        # Usa o mesmo lock das operações de Robot/Release para
        # impedir alterações concorrentes durante a validação.
        # ========================================================

        lock_publication(
            db
        )


        # ========================================================
        # 2. LOCALIZA A PASTA
        # ========================================================

        folder = (
            db.query(RobotFolder)
            .filter(
                RobotFolder.id == folder_id
            )
            .first()
        )


        if not folder:

            raise HTTPException(
                status_code=404,
                detail={
                    "code":
                        "ROBOT_FOLDER_NOT_FOUND",

                    "message":
                        "Não foi possível excluir a pasta porque ela não existe.",

                    "folder_id":
                        folder_id,
                }
            )


        folder_name = folder.name


        # ========================================================
        # 3. VERIFICA ROBOTS DIRETAMENTE NA PASTA
        # ========================================================
        #
        # Nenhum Robot é excluído automaticamente.
        #
        # Isso é fundamental porque cada Robot possui suas
        # próprias regras de exclusão:
        #
        # - Libraries;
        # - Schedules;
        # - projetos ativos;
        # - histórico;
        # - arquivo físico.
        # ========================================================

        robots = (
            db.query(Robot)
            .filter(
                Robot.folder_id == folder.id
            )
            .order_by(
                Robot.name
            )
            .all()
        )


        if robots:

            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "ROBOT_FOLDER_HAS_ROBOTS",

                    "message": (
                        f'Não foi possível excluir a pasta '
                        f'"{folder_name}". '
                        f'Ela possui {len(robots)} Robot(s). '
                        f'Mova ou exclua esses Robots individualmente '
                        f'antes de excluir a pasta.'
                    ),

                    "folder_id":
                        folder.id,

                    "folder_name":
                        folder.name,

                    "total_robots":
                        len(robots),

                    "robots": [
                        {
                            "robot_id":
                                robot.id,

                            "robot_name":
                                robot.name,

                            "robot_version":
                                robot.version,
                        }

                        for robot in robots
                    ],
                }
            )


        # ========================================================
        # 4. VERIFICA SUBPASTAS
        # ========================================================
        #
        # Basta verificar filhos diretos.
        #
        # Se existir qualquer descendente na árvore, obrigatoriamente
        # haverá pelo menos uma subpasta diretamente ligada a esta.
        # ========================================================

        subpastas = (
            db.query(RobotFolder)
            .filter(
                RobotFolder.parent_id == folder.id
            )
            .order_by(
                RobotFolder.name
            )
            .all()
        )


        if subpastas:

            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "ROBOT_FOLDER_HAS_SUBFOLDERS",

                    "message": (
                        f'Não foi possível excluir a pasta '
                        f'"{folder_name}". '
                        f'Ela possui {len(subpastas)} subpasta(s). '
                        f'Remova ou mova essas subpastas antes '
                        f'de tentar novamente.'
                    ),

                    "folder_id":
                        folder.id,

                    "folder_name":
                        folder.name,

                    "total_subfolders":
                        len(subpastas),

                    "subfolders": [
                        {
                            "folder_id":
                                subpasta.id,

                            "folder_name":
                                subpasta.name,
                        }

                        for subpasta in subpastas
                    ],
                }
            )


        # ========================================================
        # 5. EXCLUI SOMENTE O REGISTRO DA PASTA
        # ========================================================
        #
        # Neste ponto já sabemos que:
        #
        # - não possui Robots;
        # - não possui subpastas.
        #
        # Portanto não existe nenhum arquivo de Robot que deva ser
        # removido por esta operação.
        # ========================================================

        db.delete(
            folder
        )

        db.commit()


        # ========================================================
        # 6. SUCESSO
        # ========================================================

        return {
            "status":
                "success",

            "message": (
                f'Pasta "{folder_name}" excluída com sucesso.'
            ),

            "folder_id":
                folder_id,

            "folder_name":
                folder_name,
        }


    # ============================================================
    # ERROS DE REGRA DE NEGÓCIO
    # ============================================================
    #
    # Preserva corretamente os HTTP 404/409 criados acima.
    # ============================================================

    except HTTPException:

        db.rollback()

        raise


    # ============================================================
    # ERRO TÉCNICO INESPERADO
    # ============================================================

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail={
                "code":
                    "ROBOT_FOLDER_DELETE_FAILED",

                "message":
                    "Não foi possível excluir a pasta devido a uma falha interna.",

                "folder_id":
                    folder_id,

                "error":
                    str(error),
            }
        )


    finally:

        db.close()


def create_robot_folder_service(
    request: RobotFolderRequest
):
    """
    Cria uma nova pasta no repositório de robôs.

    Parâmetros:
        request:
            Dados da nova pasta.

            name:
                Nome da pasta.

            parent_id:
                ID da pasta pai. Opcional.

    Permissão necessária:
        Robots:create
    """

    db = SessionLocal()

    try:
        lock_publication(db)

        # ====================================================
        # 1. VALIDA NOME
        # ====================================================

        nome = request.name.strip()


        if not nome:

            return {

                "status": "error",

                "message": "Nome da pasta não informado"

            }


        # ====================================================
        # 2. VALIDA PASTA PAI
        # ====================================================

        if request.parent_id is not None:

            parent = db.query(
                RobotFolder
            ).filter(
                RobotFolder.id == request.parent_id
            ).first()


            if not parent:

                return {

                    "status": "error",

                    "message": "Pasta pai não encontrada",

                    "parent_id": request.parent_id

                }


        # ====================================================
        # 3. VERIFICA DUPLICIDADE
        # ====================================================

        pasta_existente = db.query(
            RobotFolder
        ).filter(
            RobotFolder.name == nome,
            RobotFolder.parent_id == request.parent_id
        ).first()


        if pasta_existente:

            return {

                "status": "error",

                "message": "Pasta já existe",

                "folder_id": pasta_existente.id

            }


        # ====================================================
        # 4. CRIA PASTA
        # ====================================================

        pasta = RobotFolder(

            name=nome,

            parent_id=request.parent_id

        )


        db.add(
            pasta
        )

        db.commit()

        db.refresh(
            pasta
        )


        # ====================================================
        # 5. RETORNO
        # ====================================================

        return {

            "status": "success",

            "message": "Pasta criada com sucesso",

            "folder": {

                "id": pasta.id,

                "name": pasta.name,

                "parent_id": pasta.parent_id

            }

        }


    except Exception as error:

        db.rollback()


        return {

            "status": "error",

            "message": "Não foi possível criar a pasta",

            "error": str(error)

        }


    finally:

        db.close()


def list_robot_folders_service():
    """
    Lista todas as pastas do repositório de robôs.

    Parâmetros:
        Nenhum.

    Permissão necessária:
        Robots:view
    """

    db = SessionLocal()

    try:

        # ====================================================
        # BUSCA TODAS AS PASTAS
        # ====================================================

        folders = db.query(
            RobotFolder
        ).order_by(
            RobotFolder.name
        ).all()


        # ====================================================
        # RETORNO
        # ====================================================

        return {

            "status": "success",

            "total": len(folders),

            "folders": [

                {

                    "id": folder.id,

                    "name": folder.name,

                    "parent_id": folder.parent_id

                }

                for folder in folders

            ]

        }


    except Exception as error:

        return {

            "status": "error",

            "message": "Não foi possível listar as pastas",

            "error": str(error)

        }


    finally:

        db.close()


def list_root_robots_service():
    """
    Lista somente os robôs armazenados diretamente na raiz.

    Regra:

        Robot.folder_id IS NULL

    A Raiz de Robôs é uma localização lógica do Control Room.
    Ela não corresponde a um registro da tabela RobotFolder.
    """

    db = SessionLocal()

    try:

        # --------------------------------------------------------
        # BUSCA SOMENTE ROBÔS SEM PASTA
        # --------------------------------------------------------
        #
        # SQL equivalente:
        #
        #     WHERE folder_id IS NULL
        #
        # Não incluímos robôs pertencentes a nenhuma pasta real.
        # --------------------------------------------------------

        robots = (
            db.query(Robot)
            .filter(
                Robot.folder_id.is_(None)
            )
            .order_by(
                Robot.name
            )
            .all()
        )

        # --------------------------------------------------------
        # RETORNO
        # --------------------------------------------------------
        #
        # Mantemos praticamente o mesmo formato utilizado pelo
        # endpoint de robôs por pasta para facilitar o frontend.
        # --------------------------------------------------------

        return {
            "status": "success",

            "folder": {
                "id": None,
                "name": "Raiz de Robôs"
            },

            "total": len(robots),

            "robots": [
                {
                    "id": robot.id,
                    "name": robot.name,
                    "filename": robot.filename,
                    "version": robot.version,
                    "file_hash": robot.file_hash,
                    "file_path": robot.file_path
                }

                for robot in robots
            ]
        }

    finally:

        # Sempre encerra a sessão do banco após a consulta.
        db.close()


def list_robots_in_folder_service(
    folder_id: int
):
    """
    Lista os robôs pertencentes a uma pasta.

    Parâmetros:
        folder_id:
            Identificador único da pasta.

    Retorna os robôs cadastrados dentro da pasta informada.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. BUSCA A PASTA
        # ====================================================

        folder = db.query(
            RobotFolder
        ).filter(
            RobotFolder.id == folder_id
        ).first()


        if not folder:

            return {

                "status": "error",

                "message": "Pasta não encontrada",

                "folder_id": folder_id

            }


        # ====================================================
        # 2. BUSCA OS ROBÔS
        # ====================================================

        robots = db.query(
            Robot
        ).filter(
            Robot.folder_id == folder_id
        ).order_by(
            Robot.name
        ).all()


        # ====================================================
        # 3. RETORNO
        # ====================================================

        return {

            "status": "success",

            "folder": {

                "id": folder.id,

                "name": folder.name

            },

            "total": len(robots),

            "robots": [

                {

                    "id": robot.id,

                    "name": robot.name,

                    "filename": robot.filename,

                    "version": robot.version,

                    "file_hash": robot.file_hash,

                    "file_path": robot.file_path

                }

                for robot in robots

            ]

        }


    except Exception as error:

        return {

            "status": "error",

            "message": (
                "Não foi possível listar "
                "os robôs da pasta"
            ),

            "error": str(error)

        }


    finally:

        db.close()
