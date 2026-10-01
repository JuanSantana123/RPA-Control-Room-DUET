# ============================================================
# DUET CORE - ROBOTS - IDENTIDADE DE PACOTE IMPORTADO
# ============================================================
#
# Responsabilidade:
# - calcular a identidade funcional de um pacote de Robot;
# - comparar o snapshot de Libraries da importação com a versão atual;
# - decidir se uma importação é idempotente.
#
# IMPORTANTE:
# O duet-release.json não participa do fingerprint funcional porque
# contém dados locais/voláteis como robot_id, robot_version,
# published_by e published_at.
# ============================================================

import json
from hashlib import sha256

from fastapi import HTTPException

from models import (
    Library,
    LibraryVersion,
    Robot,
    RobotVersionLibraryDependency,
)
from releases.service import (
    MANIFEST,
    read_package,
    resolve_robot_version,
)


# ============================================================
# FINGERPRINT DO CONTEÚDO FUNCIONAL
# ============================================================

def calculate_content_fingerprint(
    contents: dict[str, bytes],
) -> str:
    """
    Calcula uma identidade determinística do conteúdo funcional.

    A identidade considera caminho + bytes exatos de cada arquivo,
    em ordem determinística, ignorando somente duet-release.json.
    """

    hasher = sha256()

    for name, data in sorted(
        (
            (name, data)
            for name, data in contents.items()
            if name != MANIFEST
        ),
        key=lambda item: item[0],
    ):
        name_bytes = name.encode("utf-8")

        # Prefixos de tamanho evitam ambiguidades de concatenação.
        hasher.update(
            len(name_bytes).to_bytes(8, "big")
        )
        hasher.update(
            name_bytes
        )
        hasher.update(
            len(data).to_bytes(8, "big")
        )
        hasher.update(
            data
        )

    return hasher.hexdigest()


# ============================================================
# ASSINATURA PORTÁTIL DAS DEPENDÊNCIAS
# ============================================================

def _dependency_signature_from_resolved(
    dependencies: list[dict],
) -> tuple[tuple[str, str, str], ...]:
    """
    Converte as dependências resolvidas da nova importação em uma
    assinatura independente dos IDs locais do banco.
    """

    return tuple(sorted(
        (
            str(dependency.get("import_name") or ""),
            str(dependency.get("version") or ""),
            str(dependency.get("file_hash") or ""),
        )
        for dependency in dependencies
    ))


def _dependency_signature_from_current_version(
    db,
    robot_id: int,
    robot_version: int,
) -> tuple[tuple[str, str, str], ...]:
    """
    Obtém do snapshot oficial da RobotVersion a assinatura portátil
    das Libraries atualmente utilizadas.
    """

    links = (
        db.query(
            RobotVersionLibraryDependency
        )
        .filter(
            RobotVersionLibraryDependency.robot_id == robot_id,
            RobotVersionLibraryDependency.robot_version == robot_version,
        )
        .all()
    )

    rows = (
        db.query(
            RobotVersionLibraryDependency,
            Library,
            LibraryVersion,
        )
        .join(
            Library,
            Library.id
            == RobotVersionLibraryDependency.library_id,
        )
        .join(
            LibraryVersion,
            LibraryVersion.id
            == RobotVersionLibraryDependency.library_version_id,
        )
        .filter(
            RobotVersionLibraryDependency.robot_id == robot_id,
            RobotVersionLibraryDependency.robot_version == robot_version,
            LibraryVersion.library_id == Library.id,
        )
        .all()
    )

    # Um link sem Library/LibraryVersion correspondente representa
    # inconsistência de catálogo. Não tratamos isso como "mudança" e
    # não escondemos o problema criando uma nova RobotVersion.
    if len(rows) != len(links):
        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "ROBOT_LIBRARY_SNAPSHOT_INCONSISTENT",

                "message": (
                    "O snapshot de Libraries da RobotVersion atual "
                    "está inconsistente com o catálogo local."
                ),

                "robot_id":
                    robot_id,

                "robot_version":
                    robot_version,
            },
        )

    return tuple(sorted(
        (
            str(library.import_name or ""),
            str(library_version.version or ""),
            str(library_version.file_hash or ""),
        )
        for _, library, library_version in rows
    ))


# ============================================================
# IDEMPOTÊNCIA DA IMPORTAÇÃO
# ============================================================

def is_same_as_current_version(
    db,
    robot: Robot,
    imported_contents: dict[str, bytes],
    imported_dependencies: list[dict],
) -> bool:
    """
    Retorna True somente quando a importação é funcionalmente igual
    à RobotVersion vigente.

    São comparados:
      1. arquivos funcionais do pacote;
      2. snapshot exato de Libraries.

    Antes da comparação, a RobotVersion vigente também é validada
    fisicamente e quanto à identidade de seu manifesto.
    """

    current_robot_version, current_package_path = (
        resolve_robot_version(
            db,
            robot.id,
            robot.version,
        )
    )

    # O Robot é o ponteiro operacional da versão vigente. Se o hash
    # divergir da RobotVersion, não é seguro continuar a comparação.
    if (
        robot.file_hash
        and robot.file_hash != current_robot_version.file_hash
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
            },
        )

    current_contents = read_package(
        current_package_path
    )

    # Manifesto ausente é tolerado para compatibilidade com snapshots
    # legados. Se existir, porém, precisa representar exatamente a
    # RobotVersion vigente.
    if MANIFEST in current_contents:
        try:
            current_manifest = json.loads(
                current_contents[MANIFEST]
            )
        except Exception as error:
            raise HTTPException(
                status_code=409,
                detail=(
                    "O manifesto da RobotVersion atual é inválido."
                ),
            ) from error

        if (
            current_manifest.get("schema_version") != 1
            or current_manifest.get("robot_id") != robot.id
            or current_manifest.get("robot_version") != robot.version
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "O manifesto da RobotVersion atual não corresponde "
                    "ao Robot vigente."
                ),
            )

    imported_fingerprint = (
        calculate_content_fingerprint(
            imported_contents
        )
    )

    current_fingerprint = (
        calculate_content_fingerprint(
            current_contents
        )
    )

    if imported_fingerprint != current_fingerprint:
        return False

    imported_dependency_signature = (
        _dependency_signature_from_resolved(
            imported_dependencies
        )
    )

    current_dependency_signature = (
        _dependency_signature_from_current_version(
            db,
            robot.id,
            robot.version,
        )
    )

    return (
        imported_dependency_signature
        == current_dependency_signature
    )
