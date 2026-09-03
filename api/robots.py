# ============================================================
# ROUTER DE ROBÔS
# ============================================================
# Concentra as APIs relacionadas aos robôs:
#
# - Upload de robôs
# - Exclusão de robôs
# - Criação de pastas
# - Exclusão de pastas
# - Listagem de pastas
# - Listagem de robôs por pasta
#
# As URLs permanecem exatamente iguais às APIs existentes
# no main.py para não quebrar o frontend React.
# ============================================================


from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form
)

from pydantic import BaseModel

from database import SessionLocal

from models import (
    Robot,
    RobotFolder
)

from pathlib import Path

from hashlib import sha256

import os


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["Robots"]
)


# ============================================================
# REPOSITÓRIO DE ROBÔS
# ============================================================
#
# __file__:
#
#     api/robots.py
#
# parent:
#
#     api/
#
# parent.parent:
#
#     pasta principal do Control Room
#
# Portanto o repository fica:
#
#     RPA-Control-Room/repository
#
# ============================================================

BASE_DIRECTORY = Path(
    os.path.abspath(__file__)
).parent.parent


ROBOT_REPOSITORY = (
    BASE_DIRECTORY / "repository"
)


ROBOT_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FUNÇÃO CALCULAR HASH
# ============================================================

def calcular_hash_arquivo(
    arquivo: bytes
):
    """
    Calcula o SHA-256 do arquivo.

    O hash é utilizado para descobrir se o robô enviado
    é exatamente igual ao que já está cadastrado.
    """

    return sha256(
        arquivo
    ).hexdigest()


# ============================================================
# UPLOAD DE ROBÔ
# ============================================================

@router.post("/robots/upload")
async def upload_robot(
    file: UploadFile = File(...),
    folder_id: int | None = Form(None)
):

    # ========================================================
    # 1. VALIDA NOME DO ARQUIVO
    # ========================================================

    nome_arquivo = file.filename


    if not nome_arquivo:

        return {
            "status": "error",
            "message": "Nome do arquivo não informado"
        }


    # ========================================================
    # 2. VALIDA EXTENSÃO
    # ========================================================

    extensao = os.path.splitext(
        nome_arquivo
    )[1].lower()


    extensoes_permitidas = [
        ".zip",
        ".rar"
    ]


    if extensao not in extensoes_permitidas:

        return {
            "status": "error",
            "message": "Formato de robô não permitido",
            "extensao": extensao,
            "formatos_permitidos": extensoes_permitidas
        }


    # ========================================================
    # 3. LÊ O ARQUIVO
    # ========================================================

    try:

        conteudo = await file.read()

    except Exception as error:

        return {
            "status": "error",
            "message": "Não foi possível ler o arquivo",
            "error": str(error)
        }


    # ========================================================
    # 4. CALCULA SHA-256
    # ========================================================

    file_hash = calcular_hash_arquivo(
        conteudo
    )


    # ========================================================
    # 5. LOCALIZA A PASTA DO ROBÔ
    # ========================================================

    db = SessionLocal()

    try:

        pasta = None


        # ----------------------------------------------------
        # Se foi informada uma pasta, verifica se ela existe.
        # ----------------------------------------------------

        if folder_id is not None:

            pasta = db.query(
                RobotFolder
            ).filter(
                RobotFolder.id == folder_id
            ).first()


            if not pasta:

                return {
                    "status": "error",
                    "message": "Pasta não encontrada",
                    "folder_id": folder_id
                }

    finally:

        db.close()


    # ========================================================
    # 6. DEFINE CAMINHO FÍSICO
    # ========================================================

    if pasta:

        pasta_path = (
            ROBOT_REPOSITORY / pasta.name
        )

    else:

        pasta_path = (
            ROBOT_REPOSITORY / "Sem pasta"
        )


    pasta_path.mkdir(
        parents=True,
        exist_ok=True
    )


    caminho_arquivo = (
        pasta_path / nome_arquivo
    )


    # ========================================================
    # 7. SALVA ARQUIVO FISICAMENTE
    # ========================================================

    with open(
        caminho_arquivo,
        "wb"
    ) as arquivo_destino:

        arquivo_destino.write(
            conteudo
        )


    # ========================================================
    # 8. CONSULTA ROBÔ NO BANCO
    # ========================================================

    db = SessionLocal()

    try:

        robot = db.query(
            Robot
        ).filter(
            Robot.name == nome_arquivo
        ).first()

        

        # ====================================================
        # 9. VERIFICA SE O ROBÔ JÁ EXISTE
        # ====================================================

        if robot:

            # ------------------------------------------------
            # Arquivo é exatamente igual ao já cadastrado.
            # ------------------------------------------------

            if robot.file_hash == file_hash:

                return {

                    "status": "success",

                    "message": "Robot já está atualizado",

                    "upload": False,

                    "robot": {

                        "name": robot.name,

                        "filename": robot.filename,

                        "version": robot.version,

                        "file_hash": robot.file_hash

                    }

                }


            # ------------------------------------------------
            # Arquivo mudou.
            #
            # Incrementa a versão.
            # ------------------------------------------------

            nova_versao = (
                robot.version + 1
            )

        else:

            # ------------------------------------------------
            # Primeiro upload do robô.
            # ------------------------------------------------

            nova_versao = 1


        # ====================================================
        # 10. SALVA / ATUALIZA ROBÔ
        # ====================================================

        if robot:

            # ------------------------------------------------
            # Atualiza registro existente.
            # ------------------------------------------------

            robot.filename = nome_arquivo

            robot.version = nova_versao

            robot.file_hash = file_hash

            robot.file_path = (
                str(caminho_arquivo)
            )

            robot.folder_id = folder_id

        else:

            # ------------------------------------------------
            # Cria novo registro.
            # ------------------------------------------------

            robot = Robot(

                name=nome_arquivo,

                filename=nome_arquivo,

                version=nova_versao,

                file_hash=file_hash,

                file_path=str(
                    caminho_arquivo
                ),

                folder_id=folder_id

            )

            db.add(robot)


        # ====================================================
        # 11. COMMIT
        # ====================================================

        db.commit()

        db.refresh(robot)


    finally:

        db.close()


    # ========================================================
    # 12. RETORNO
    # ========================================================

    return {

        "status": "success",

        "message": "Robot enviado para o Agent",

        "upload": True,

        "robot": {

            "name": robot.name,

            "filename": robot.filename,

            "version": robot.version,

            "file_hash": robot.file_hash

        }

    }


# ============================================================
# EXCLUIR ROBÔ
# ============================================================

@router.delete("/robots/{robot_id}")
def delete_robot(
    robot_id: int
):

    db = SessionLocal()

    try:

        # ====================================================
        # 1. BUSCA ROBÔ
        # ====================================================

        robot = db.query(
            Robot
        ).filter(
            Robot.id == robot_id
        ).first()


        if not robot:

            return {

                "status": "error",

                "message": "Robô não encontrado",

                "robot_id": robot_id

            }


        nome = robot.name

        file_path = robot.file_path


        # ====================================================
        # 2. EXCLUI ARQUIVO FÍSICO
        # ====================================================

        if file_path:

            caminho = Path(
                file_path
            )


            if caminho.exists():

                caminho.unlink()


        # ====================================================
        # 3. EXCLUI REGISTRO DO BANCO
        # ====================================================

        db.delete(
            robot
        )

        db.commit()


        # ====================================================
        # 4. RETORNO
        # ====================================================

        return {

            "status": "success",

            "message": "Robô excluído com sucesso",

            "robot_id": robot_id,

            "name": nome

        }


    except Exception as error:

        db.rollback()


        return {

            "status": "error",

            "message": "Não foi possível excluir o robô",

            "robot_id": robot_id,

            "error": str(error)

        }


    finally:

        db.close()


# ============================================================
# EXCLUIR PASTA DE ROBÔS
# ============================================================

@router.delete("/robot-folders/{folder_id}")
def delete_robot_folder(
    folder_id: int
):

    db = SessionLocal()

    try:

        # ====================================================
        # 1. BUSCA PASTA
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
        # 2. VERIFICA ROBÔS DENTRO DA PASTA
        # ====================================================

        robots = db.query(
            Robot
        ).filter(
            Robot.folder_id == folder_id
        ).all()


        if robots:

            return {

                "status": "error",

                "message": (
                    "Não é possível excluir a pasta "
                    "porque existem robôs dentro dela"
                ),

                "folder_id": folder_id,

                "robots_count": len(robots)

            }


        # ====================================================
        # 3. CAMINHO FÍSICO
        # ====================================================

        pasta_path = (
            ROBOT_REPOSITORY / folder.name
        )


        # ====================================================
        # 4. REMOVE PASTA FÍSICA
        # ====================================================

        if pasta_path.exists():

            pasta_path.rmdir()


        # ====================================================
        # 5. REMOVE DO BANCO
        # ====================================================

        db.delete(
            folder
        )

        db.commit()


        # ====================================================
        # 6. RETORNO
        # ====================================================

        return {

            "status": "success",

            "message": "Pasta excluída com sucesso",

            "folder_id": folder_id,

            "name": folder.name

        }


    except Exception as error:

        db.rollback()


        return {

            "status": "error",

            "message": "Não foi possível excluir a pasta",

            "folder_id": folder_id,

            "error": str(error)

        }


    finally:

        db.close()


# ============================================================
# MODELO PARA CRIAÇÃO DE PASTA
# ============================================================

class RobotFolderRequest(
    BaseModel
):

    name: str

    parent_id: int | None = None


# ============================================================
# CRIAR PASTA DE ROBÔS
# ============================================================

@router.post("/robot-folders")
def create_robot_folder(
    request: RobotFolderRequest
):

    db = SessionLocal()

    try:

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


# ============================================================
# LISTAR PASTAS DE ROBÔS
# ============================================================

@router.get("/robot-folders")
def list_robot_folders():

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


# ============================================================
# LISTAR ROBÔS DE UMA PASTA
# ============================================================

@router.get(
    "/robot-folders/{folder_id}/robots"
)
def list_robots_in_folder(
    folder_id: int
):

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