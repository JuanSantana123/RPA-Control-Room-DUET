# ============================================================
# DUET CORE - ROBOTS - IMPORTAÇÃO DE PACOTE
# ============================================================
#
# Responsável por importar um pacote ZIP para o catálogo de
# Robots do DUET.
#
# IMPORTANTE:
#
# A importação NÃO preserva robot_id e robot_version presentes
# no manifesto do ambiente de origem.
#
# O pacote é incorporado ao Control Room atual e recebe:
#
#     - Robot.id local;
#     - RobotVersion.version local;
#     - published_by local;
#     - published_at local;
#     - dependências resolvidas no catálogo local.
#
# Dessa forma um pacote exportado pode ser importado novamente
# sem deixar o duet-release.json inconsistente.
# ============================================================

import json
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from database import SessionLocal
from models import (
    Library,
    LibraryVersion,
    Robot,
    RobotFolder,
    RobotVersion,
    RobotVersionLibraryDependency,
)
from packaging import project_packager as packager
from releases.service import (
    MANIFEST,
    lock_publication,
    read_package,
    safe_name,
    write_package,
)
from robots.import_identity import (
    is_same_as_current_version,
)


# ============================================================
# RESOLVER DEPENDÊNCIAS DO PACOTE NO AMBIENTE LOCAL
# ============================================================

def _resolve_import_dependencies(
    db,
    source_manifest: dict | None,
) -> list[dict]:
    """
    Resolve dependências existentes no manifesto exportado.

    IDs do ambiente de origem NÃO são confiáveis porque outro
    Control Room pode possuir IDs completamente diferentes.

    A identidade portátil utilizada é:

        import_name + version

    Quando o manifesto também informa file_hash, o hash precisa
    corresponder ao artefato registrado localmente.
    """

    if not source_manifest:
        return []

    dependencies = (
        source_manifest.get("dependencies")
        or []
    )

    if not isinstance(dependencies, list):
        raise HTTPException(
            status_code=409,
            detail=(
                "O manifesto do pacote possui uma lista de "
                "dependências inválida."
            ),
        )

    resolved_dependencies = []
    seen_import_names = set()

    for dependency in dependencies:

        if not isinstance(dependency, dict):
            raise HTTPException(
                status_code=409,
                detail="O manifesto possui uma dependência inválida.",
            )

        import_name = str(
            dependency.get("import_name") or ""
        ).strip()

        version_name = str(
            dependency.get("version") or ""
        ).strip()

        expected_hash = str(
            dependency.get("file_hash") or ""
        ).strip()

        if not import_name or not version_name:
            raise HTTPException(
                status_code=409,
                detail=(
                    "O manifesto possui uma dependência sem "
                    "import_name ou versão."
                ),
            )

        # Um Release não pode declarar a mesma Library mais de uma
        # vez. Além de ser ambíguo, isso violaria a unicidade do
        # snapshot RobotVersionLibraryDependency.
        normalized_import_name = import_name.casefold()

        if normalized_import_name in seen_import_names:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A biblioteca "{import_name}" aparece mais de '
                    "uma vez no manifesto do pacote."
                ),
            )

        seen_import_names.add(
            normalized_import_name
        )

        # --------------------------------------------------------
        # Biblioteca local
        # --------------------------------------------------------

        library = (
            db.query(Library)
            .filter(
                Library.import_name == import_name
            )
            .first()
        )

        if not library:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A biblioteca "{import_name}" exigida pelo '
                    f'pacote não existe neste Control Room.'
                ),
            )

        # --------------------------------------------------------
        # Versão exata local
        # --------------------------------------------------------

        library_version = (
            db.query(LibraryVersion)
            .filter(
                LibraryVersion.library_id == library.id,
                LibraryVersion.version == version_name,
            )
            .first()
        )

        if not library_version:
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A biblioteca "{import_name}" existe, mas a '
                    f'versão {version_name} exigida pelo pacote '
                    f'não está disponível neste Control Room.'
                ),
            )

        # --------------------------------------------------------
        # Integridade da LibraryVersion
        # --------------------------------------------------------

        if (
            expected_hash
            and library_version.file_hash != expected_hash
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f'A biblioteca "{import_name}" '
                    f'{version_name} possui hash diferente do '
                    f'pacote importado.'
                ),
            )

        # --------------------------------------------------------
        # Gera representação LOCAL da dependência
        # --------------------------------------------------------

        resolved_dependencies.append({
            "library_id":
                library.id,

            "library_name":
                library.name,

            "import_name":
                library.import_name,

            "library_version_id":
                library_version.id,

            "version":
                library_version.version,

            "file_hash":
                library_version.file_hash,

            "modified":
                False,

            "source_type":
                library_version.source_type,

            "source_robot_id":
                library_version.source_robot_id,

            "source_robot_version":
                library_version.source_robot_version,
        })

    return resolved_dependencies


# ============================================================
# IMPORTAR PACOTE
# ============================================================

async def import_robot_package_service(
    file: UploadFile,
    folder_id: int | None,
    usuario,
):
    """
    Importa um pacote de Robot para o Control Room.

    O ZIP recebido nunca é simplesmente reutilizado quando possui
    duet-release.json.

    O manifesto é reconstruído utilizando a identidade do Robot
    criada/localizada neste Control Room.
    """

    # ========================================================
    # 1. NOME
    # ========================================================

    filename = safe_name(
        file.filename or ""
    )

    if not filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail=(
                "A importação de pacote DUET aceita somente "
                "arquivos .zip."
            ),
        )

    # ========================================================
    # 2. CONTEÚDO RECEBIDO
    # ========================================================

    try:
        uploaded_bytes = await file.read()

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível ler o pacote enviado.",
        ) from error

    if not uploaded_bytes:
        raise HTTPException(
            status_code=400,
            detail="O pacote enviado está vazio.",
        )

    db = SessionLocal()

    created_package: Path | None = None
    committed = False

    try:

        # ====================================================
        # 3. LOCK DE PUBLICAÇÃO
        # ====================================================

        lock_publication(
            db
        )

        # ====================================================
        # 4. VALIDA PASTA
        # ====================================================

        if folder_id is not None:

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
                    detail="Pasta de destino não encontrada.",
                )

        # ====================================================
        # 5. LÊ E VALIDA O ZIP
        # ====================================================
        #
        # Utilizamos read_package() para manter a mesma política
        # de segurança dos Releases:
        #
        # - paths;
        # - symlinks;
        # - ZIP bomb;
        # - colisões;
        # - tamanho descompactado.
        # ====================================================

        packager.BUILD_TEMP_REPOSITORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.TemporaryDirectory(
            dir=packager.BUILD_TEMP_REPOSITORY
        ) as temp_dir:

            temp_package = (
                Path(temp_dir) /
                "import-package.zip"
            )

            temp_package.write_bytes(
                uploaded_bytes
            )

            contents = read_package(
                temp_package
            )

        # ====================================================
        # 6. ENTRYPOINT
        # ====================================================

        if "main.py" not in contents:
            raise HTTPException(
                status_code=409,
                detail=(
                    "O pacote precisa conter main.py na raiz."
                ),
            )

        # ====================================================
        # 7. MANIFESTO DE ORIGEM
        # ====================================================

        source_manifest = None

        if MANIFEST in contents:

            try:
                source_manifest = json.loads(
                    contents.pop(MANIFEST)
                )

            except Exception as error:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "O duet-release.json do pacote é inválido."
                    ),
                ) from error

            if (
                source_manifest.get("schema_version")
                != 1
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A versão do manifesto do pacote "
                        "não é suportada."
                    ),
                )

        # ====================================================
        # 8. DEPENDÊNCIAS
        # ====================================================

        dependencies = (
            _resolve_import_dependencies(
                db,
                source_manifest,
            )
        )

        # ====================================================
        # 9. ROBOT DESTINO
        # ====================================================

        robot = (
            db.query(Robot)
            .filter(
                Robot.name == filename,
                Robot.folder_id == folder_id,
            )
            .first()
        )

        if robot:

            # ====================================================
            # 9.1 IDEMPOTÊNCIA DA IMPORTAÇÃO
            # ====================================================
            #
            # Reimportar exatamente o mesmo conteúdo funcional e
            # as mesmas dependências NÃO cria uma nova versão.
            #
            # A comparação ignora duet-release.json porque ele
            # contém identidade/auditoria locais deste ambiente.
            # ====================================================

            if is_same_as_current_version(
                db,
                robot,
                contents,
                dependencies,
            ):
                response = {
                    "status":
                        "up_to_date",

                    "message": (
                        f'Robot "{robot.name}" já está atualizado '
                        f'na versão {robot.version}.'
                    ),

                    "robot": {
                        "id":
                            robot.id,

                        "name":
                            robot.name,

                        "version":
                            robot.version,

                        "folder_id":
                            robot.folder_id,

                        "file_hash":
                            robot.file_hash,
                    },

                    "dependencies":
                        len(dependencies),
                }

                # Nenhuma alteração foi persistida. O rollback libera
                # explicitamente a transação/lock antes do retorno.
                db.rollback()

                return response

            next_version = (
                robot.version + 1
            )

        else:

            next_version = 1

            # O ID do Robot é necessário antes da criação do
            # novo manifesto.
            #
            # file_path/file_hash recebem valores temporários
            # somente dentro desta transação. Antes do commit
            # ambos serão substituídos pelo artefato real.
            robot = Robot(
                name=filename,
                filename=filename,
                version=next_version,
                file_hash="",
                file_path="",
                folder_id=folder_id,
            )

            db.add(
                robot
            )

            db.flush()

        # ====================================================
        # 10. NOVO MANIFESTO LOCAL
        # ====================================================

        imported_at = datetime.utcnow()

        new_manifest = {
            "schema_version":
                1,

            # Identidade deste Control Room.
            "robot_id":
                robot.id,

            "robot_version":
                next_version,

            # Não existe AutomationProject de origem local.
            "project_id":
                None,

            "published_by":
                usuario.id,

            "published_at":
                imported_at.isoformat(),

            "dependencies":
                dependencies,
        }

        # Mantém somente informação de auditoria sobre a origem.
        # Esses valores NÃO são utilizados como IDs locais.
        if source_manifest:

            new_manifest["import_source"] = {
                "robot_id":
                    source_manifest.get("robot_id"),

                "robot_version":
                    source_manifest.get(
                        "robot_version"
                    ),

                "project_id":
                    source_manifest.get(
                        "project_id"
                    ),

                "published_by":
                    source_manifest.get(
                        "published_by"
                    ),

                "published_at":
                    source_manifest.get(
                        "published_at"
                    ),
            }

        contents[MANIFEST] = json.dumps(
            new_manifest,
            indent=2,
            ensure_ascii=False,
        ).encode("utf-8")

        # ====================================================
        # 11. ARTEFATO IMUTÁVEL
        # ====================================================

        created_package = (
            packager.BASE_DIRECTORY
            / "storage"
            / "releases"
            / str(robot.id)
            / str(next_version)
            / uuid4().hex
            / filename
        )

        package_hash = write_package(
            created_package,
            contents,
        )

        # ====================================================
        # 12. REVALIDAÇÃO FÍSICA E LÓGICA
        # ====================================================
        #
        # Antes de registrar a RobotVersion, confirmamos que:
        #
        # 1. o artefato realmente existe;
        # 2. o SHA-256 físico continua igual ao retornado na escrita;
        # 3. o ZIP continua legível pela política segura do Release;
        # 4. o manifesto representa exatamente Robot/version locais.
        # ====================================================

        if not created_package.is_file():
            raise HTTPException(
                status_code=500,
                detail=(
                    "O pacote importado não foi encontrado "
                    "após a criação."
                ),
            )

        verified_hash = packager.calcular_sha256(
            created_package
        )

        if verified_hash != package_hash:
            raise HTTPException(
                status_code=500,
                detail=(
                    "O pacote importado falhou na validação "
                    "de integridade."
                ),
            )

        verified_contents = read_package(
            created_package
        )

        if MANIFEST not in verified_contents:
            raise HTTPException(
                status_code=500,
                detail=(
                    "O pacote importado foi gerado "
                    "sem manifesto."
                ),
            )

        verified_manifest = json.loads(
            verified_contents[MANIFEST]
        )

        if (
            verified_manifest.get("robot_id")
            != robot.id

            or

            verified_manifest.get("robot_version")
            != next_version

            or

            verified_manifest.get("schema_version")
            != 1
        ):
            raise HTTPException(
                status_code=500,
                detail=(
                    "O manifesto regenerado não corresponde "
                    "ao Robot importado."
                ),
            )

        # ====================================================
        # 13. ROBOTVERSION
        # ====================================================

        robot_version = RobotVersion(
            robot_id=robot.id,
            version=next_version,
            filename=filename,
            artifact_path=(
                created_package
                .relative_to(
                    packager.BASE_DIRECTORY
                )
                .as_posix()
            ),
            file_hash=verified_hash,

            # Importação não nasceu de um AutomationProject local.
            source_project_id=None,

            published_by=usuario.id,
            published_at=imported_at,
        )

        db.add(
            robot_version
        )

        db.flush()

        # ====================================================
        # 14. SNAPSHOT DE LIBRARIES
        # ====================================================

        for dependency in dependencies:

            db.add(
                RobotVersionLibraryDependency(
                    robot_id=robot.id,
                    robot_version=next_version,
                    library_id=(
                        dependency["library_id"]
                    ),
                    library_version_id=(
                        dependency[
                            "library_version_id"
                        ]
                    ),

                    # Não existe projeto local que originou
                    # esta importação.
                    source_project_id=None,

                    created_by=usuario.id,
                )
            )

        # ====================================================
        # 15. PONTEIRO OPERACIONAL DO ROBOT
        # ====================================================

        robot.version = next_version
        robot.filename = filename
        robot.file_hash = verified_hash
        robot.file_path = str(
            created_package
        )

        # ====================================================
        # 16. COMMIT
        # ====================================================

        db.commit()

        committed = True

        return {
            "status":
                "success",

            "message":
                (
                    f'Robot "{robot.name}" importado '
                    f'com sucesso como versão '
                    f'{next_version}.'
                ),

            "robot": {
                "id":
                    robot.id,

                "name":
                    robot.name,

                "version":
                    next_version,

                "folder_id":
                    robot.folder_id,

                "file_hash":
                    verified_hash,
            },

            "dependencies":
                len(dependencies),
        }

    except HTTPException:

        db.rollback()

        if (
            not committed
            and created_package is not None
            and created_package.exists()
        ):
            try:
                created_package.unlink()
            except Exception:
                pass

        raise

    except Exception as error:

        db.rollback()

        if (
            not committed
            and created_package is not None
            and created_package.exists()
        ):
            try:
                created_package.unlink()
            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail={
                "code":
                    "ROBOT_IMPORT_FAILED",

                "message":
                    "Não foi possível importar o pacote do Robot.",

                "error":
                    str(error),
            },
        ) from error

    finally:

        db.close()