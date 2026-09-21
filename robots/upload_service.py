# ============================================================
# DUET CORE - ROBOTS - SERVIÇO DE UPLOAD/PUBLICAÇÃO DIRETA
# ============================================================
#
# Responsabilidades:
#
# - receber o pacote ZIP em streaming;
# - validar estruturalmente o artefato;
# - calcular SHA-256;
# - preservar versionamento imutável;
# - criar Robot / RobotVersion;
# - atualizar o ponteiro atual do Robot;
# - executar rollback do banco e filesystem em caso de falha.
#
# Autenticação e RBAC continuam em api/robots.py.
# ============================================================

import hashlib
import os

from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from database import SessionLocal
from models import (
    Robot,
    RobotFolder,
    RobotVersion,
)

from releases.service import (
    lock_publication,
    resolve_robot_version,
)

from robots.repository import (
    BASE_DIRECTORY,
    ROBOT_REPOSITORY,
)

from security.artifacts import (
    MAX_UPLOAD_SIZE,
    ArtifactSecurityError,
    caminho_relativo_seguro,
    validar_nome_zip,
    validar_zip,
)


# ============================================================
# LIMPEZA DE TENTATIVA
# ============================================================

def _limpar_tentativa(
    caminho: Path | None,
):
    """
    Remove somente o arquivo/diretórios pertencentes à tentativa
    atual de publicação.

    Nunca remove versões anteriores do Robot.
    """

    if caminho is None:
        return

    try:

        if caminho.exists():

            caminho.unlink()

        parent = caminho.parent

        while (
            parent != ROBOT_REPOSITORY
            and parent != parent.parent
        ):

            try:

                parent.rmdir()

            except OSError:

                break

            parent = parent.parent

    except Exception:

        # A limpeza nunca deve mascarar o erro principal.
        pass


# ============================================================
# UPLOAD
# ============================================================

async def upload_robot_service(
    file: UploadFile,
    folder_id: int | None,
    usuario,
):
    """
    Publica diretamente uma nova versão de Robot.

    O arquivo recebido só passa a integrar o catálogo depois de:

    1. upload completo;
    2. validação de tamanho;
    3. validação estrutural do ZIP;
    4. SHA-256;
    5. validação da versão vigente;
    6. criação da RobotVersion;
    7. commit único no banco.
    """

    # ========================================================
    # 1. VALIDA NOME
    # ========================================================

    try:

        nome_arquivo = validar_nome_zip(
            file.filename or ""
        )

    except ArtifactSecurityError as error:

        return {
            "status": "error",
            "message": str(error),
        }

    # ========================================================
    # 2. ABRE TRANSAÇÃO
    # ========================================================

    db = SessionLocal()

    caminho_arquivo = None
    committed = False

    try:

        # Serializa alterações do catálogo de Produção.
        lock_publication(
            db
        )

        # ====================================================
        # 3. VALIDA PASTA
        # ====================================================

        pasta = None

        if folder_id is not None:

            pasta = (
                db.query(RobotFolder)
                .filter(
                    RobotFolder.id == folder_id
                )
                .first()
            )

            if not pasta:

                return {
                    "status": "error",
                    "message": "Pasta não encontrada",
                    "folder_id": folder_id,
                }

        # ====================================================
        # 4. ROBOT EXISTENTE
        # ====================================================

        robot = (
            db.query(Robot)
            .filter(
                Robot.name == nome_arquivo,
                Robot.folder_id == folder_id,
            )
            .first()
        )

        # A próxima versão é calculada sob o lock.
        nova_versao = (
            robot.version + 1
            if robot
            else 1
        )

        # ====================================================
        # 5. CAMINHO IMUTÁVEL DA TENTATIVA
        # ====================================================

        pasta_logica = (
            str(folder_id)
            if pasta
            else "root"
        )

        caminho_arquivo = (
            ROBOT_REPOSITORY
            / "_versions"
            / pasta_logica
            / str(nova_versao)
            / uuid4().hex
            / nome_arquivo
        )

        caminho_arquivo.parent.mkdir(
            parents=True,
            exist_ok=False,
        )

        # ====================================================
        # 6. RECEBE EM STREAMING + SHA-256
        # ====================================================
        #
        # Não utilizamos:
        #
        #     await file.read()
        #
        # sobre o arquivo inteiro.
        #
        # Isso impede que um upload grande ocupe memória
        # proporcionalmente ao tamanho total do pacote.
        # ====================================================

        hash_upload = hashlib.sha256()
        tamanho_recebido = 0

        with open(
            caminho_arquivo,
            "xb",
        ) as destino:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                tamanho_recebido += len(
                    chunk
                )

                if (
                    tamanho_recebido
                    > MAX_UPLOAD_SIZE
                ):

                    raise ArtifactSecurityError(
                        "Pacote excede o tamanho máximo "
                        "permitido para upload."
                    )

                hash_upload.update(
                    chunk
                )

                destino.write(
                    chunk
                )

            destino.flush()

            os.fsync(
                destino.fileno()
            )

        if tamanho_recebido == 0:

            raise ArtifactSecurityError(
                "Pacote recebido está vazio."
            )

        file_hash = (
            hash_upload.hexdigest()
        )

        # ====================================================
        # 7. VALIDA O ZIP FÍSICO
        # ====================================================

        validar_zip(
            caminho_arquivo
        )

        # ====================================================
        # 8. REVALIDA SHA-256 DO FILESYSTEM
        # ====================================================

        hash_fisico = hashlib.sha256()

        with open(
            caminho_arquivo,
            "rb",
        ) as arquivo_gravado:

            while True:

                chunk = arquivo_gravado.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                hash_fisico.update(
                    chunk
                )

        physical_hash = (
            hash_fisico.hexdigest()
        )

        if physical_hash != file_hash:

            raise RuntimeError(
                "O arquivo físico gravado falhou "
                "na validação SHA-256."
            )

        # ====================================================
        # 9. VALIDA A VERSÃO ATUAL
        # ====================================================
        #
        # Antes de aceitar vN+1, a versão atual precisa continuar
        # consistente entre:
        #
        # Robot
        # RobotVersion
        # filesystem
        # ====================================================

        if robot:

            (
                current_robot_version,
                current_artifact,
            ) = resolve_robot_version(
                db,
                robot.id,
                robot.version,
            )

            current_robot_path = Path(
                robot.file_path
            )

            if not current_robot_path.is_absolute():

                current_robot_path = (
                    BASE_DIRECTORY
                    / current_robot_path
                )

            if not current_robot_path.is_file():

                raise HTTPException(
                    status_code=409,
                    detail={
                        "code":
                            "ROBOT_CURRENT_ARTIFACT_MISSING",

                        "message": (
                            f'O arquivo atual do Robot '
                            f'"{robot.name}" v{robot.version} '
                            f'não existe fisicamente.'
                        ),

                        "robot_id":
                            robot.id,

                        "robot_version":
                            robot.version,
                    },
                )

            # Hash físico da versão atualmente vigente.
            current_hash = hashlib.sha256()

            with open(
                current_robot_path,
                "rb",
            ) as current_file:

                while True:

                    chunk = current_file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    current_hash.update(
                        chunk
                    )

            current_robot_hash = (
                current_hash.hexdigest()
            )

            if (
                current_robot_hash
                != robot.file_hash
            ):

                raise HTTPException(
                    status_code=409,
                    detail={
                        "code":
                            "ROBOT_CURRENT_ARTIFACT_HASH_MISMATCH",

                        "message": (
                            f'O arquivo atual do Robot '
                            f'"{robot.name}" v{robot.version} '
                            f'está com hash inválido.'
                        ),

                        "robot_id":
                            robot.id,

                        "robot_version":
                            robot.version,
                    },
                )

            if (
                current_robot_version.file_hash
                != robot.file_hash
            ):

                raise HTTPException(
                    status_code=409,
                    detail={
                        "code":
                            "ROBOT_CURRENT_VERSION_HASH_MISMATCH",

                        "message": (
                            f'O Robot "{robot.name}" está '
                            f'inconsistente. O hash registrado '
                            f'no Robot não corresponde à '
                            f'RobotVersion v{robot.version}.'
                        ),

                        "robot_id":
                            robot.id,

                        "robot_version":
                            robot.version,
                    },
                )

            # =================================================
            # MESMO CONTEÚDO
            # =================================================
            #
            # Como criamos um caminho imutável antes de conhecer
            # o hash, removemos a tentativa e mantemos exatamente
            # a versão já publicada.
            # =================================================

            if robot.file_hash == file_hash:

                _limpar_tentativa(
                    caminho_arquivo
                )

                caminho_arquivo = None

                return {
                    "status": "success",
                    "message": "Robot já está atualizado",
                    "upload": False,

                    "robot": {
                        "id": robot.id,
                        "name": robot.name,
                        "filename": robot.filename,
                        "version": robot.version,
                        "file_hash": robot.file_hash,
                        "folder_id": robot.folder_id,
                    },
                }

        # ====================================================
        # 10. CRIA/ATUALIZA ROBOT
        # ====================================================

        if robot:

            robot.filename = (
                nome_arquivo
            )

        else:

            robot = Robot(
                name=nome_arquivo,
                filename=nome_arquivo,
                version=nova_versao,
                file_hash=physical_hash,
                file_path=str(
                    caminho_arquivo
                ),
                folder_id=folder_id,
            )

            db.add(
                robot
            )

            # Precisamos do ID antes da RobotVersion.
            db.flush()

        # ====================================================
        # 11. ROBOTVERSION IMUTÁVEL
        # ====================================================

        artifact_path = (
            caminho_relativo_seguro(
                caminho_arquivo,
                BASE_DIRECTORY,
            )
        )

        robot_version = RobotVersion(
            robot_id=robot.id,
            version=nova_versao,
            filename=nome_arquivo,
            artifact_path=artifact_path,
            file_hash=physical_hash,

            # Upload direto não nasceu de projeto do Studio.
            source_project_id=None,

            published_by=usuario.id,

            # Model atual utiliza DateTime sem timezone.
            published_at=(
                datetime
                .now(UTC)
                .replace(tzinfo=None)
            ),
        )

        db.add(
            robot_version
        )

        # Faz constraints falharem antes de mover o ponteiro
        # atual do Robot.
        db.flush()

        # ====================================================
        # 12. ROBOT = PONTEIRO DA VERSÃO VIGENTE
        # ====================================================

        robot.version = (
            nova_versao
        )

        robot.filename = (
            nome_arquivo
        )

        robot.file_hash = (
            physical_hash
        )

        robot.file_path = str(
            caminho_arquivo
        )

        # ====================================================
        # 13. COMMIT ÚNICO
        # ====================================================

        db.commit()

        committed = True

        db.refresh(
            robot
        )

        return {
            "status": "success",
            "message": "Robot enviado para o Agent",
            "upload": True,

            "robot": {
                "id": robot.id,
                "name": robot.name,
                "filename": robot.filename,
                "version": robot.version,
                "file_hash": robot.file_hash,
                "folder_id": robot.folder_id,
            },
        }

    except ArtifactSecurityError as error:

        db.rollback()

        if not committed:

            _limpar_tentativa(
                caminho_arquivo
            )

        return {
            "status": "error",
            "message": str(error),
        }

    except HTTPException:

        db.rollback()

        if not committed:

            _limpar_tentativa(
                caminho_arquivo
            )

        raise

    except Exception as error:

        db.rollback()

        if not committed:

            _limpar_tentativa(
                caminho_arquivo
            )

        return {
            "status": "error",
            "message": "Não foi possível enviar o robô",
            "error": str(error),
        }

    finally:

        # Fecha UploadFile e sessão independentemente do caminho
        # de saída, inclusive retornos antecipados.
        try:

            await file.close()

        except Exception:
            pass

        db.close()