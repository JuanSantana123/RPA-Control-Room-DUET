# ============================================================
# AUTOMATION TEMPLATES - LIBRARIES SERVICE
# ============================================================
#
# Regras de negócio para composição de Libraries em Templates.
#
# REGRA CENTRAL:
#
# Uma AutomationTemplateVersion é imutável.
#
# Portanto, adicionar, remover ou trocar uma Library NUNCA altera
# a versão atual. A operação cria uma nova versão do Template,
# reutiliza o mesmo snapshot de código e grava um novo snapshot
# de dependências.
# ============================================================

from __future__ import annotations

import shutil

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    AutomationTemplateVersion,
    TemplateVersionLibraryDependency,
)

from automation_templates.service import (
    BASE_DIRECTORY,
    calcular_sha256,
    montar_artifact_path_relativo,
    obter_template_or_404,
    resolver_artifact_path,
    serializar_template_version,
)

from automation_templates.template_library_dependencies import (
    registrar_composicao_template_version,
    resolver_selecoes_template_libraries,
    serializar_dependencias_template_version,
)


# ============================================================
# CONSULTAR LIBRARIES DE UMA VERSÃO
# ============================================================

def listar_bibliotecas_template_version_service(
    *,
    template_id: int,
    version_id: int,
    db: Session,
) -> dict:
    """
    Retorna o snapshot de Libraries de uma versão específica
    do Template.
    """

    template = obter_template_or_404(
        db,
        template_id,
    )

    version = (
        db.query(
            AutomationTemplateVersion
        )
        .filter(
            AutomationTemplateVersion.id ==
                version_id,
            AutomationTemplateVersion.template_id ==
                template.id,
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail=(
                "A versão informada não pertence ao Template."
            ),
        )

    libraries = (
        serializar_dependencias_template_version(
            db,
            version.id,
        )
    )

    return {
        "status": "success",
        "template_id": template.id,
        "template_version_id": version.id,
        "template_version": version.version,
        "is_current":
            template.current_version_id == version.id,
        "total": len(libraries),
        "libraries": libraries,
    }


# ============================================================
# CRIAR NOVA VERSÃO POR ALTERAÇÃO DE LIBRARIES
# ============================================================

def atualizar_bibliotecas_template_service(
    *,
    template_id: int,
    libraries: list[dict],
    db: Session,
    usuario,
) -> dict:
    """
    Cria uma nova AutomationTemplateVersion alterando somente a
    composição de Libraries.

    O ZIP da versão atual é copiado como novo snapshot físico.
    A versão anterior permanece completamente intacta.
    """

    version_directory = None

    try:
        # --------------------------------------------------------
        # TEMPLATE ATUAL
        # --------------------------------------------------------

        template = obter_template_or_404(
            db,
            template_id,
            somente_ativo=True,
            lock=True,
        )

        if template.current_version_id is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "O Template não possui versão atual para "
                    "servir como base."
                ),
            )

        base_version = (
            db.query(
                AutomationTemplateVersion
            )
            .filter(
                AutomationTemplateVersion.id ==
                    template.current_version_id,
                AutomationTemplateVersion.template_id ==
                    template.id,
            )
            .first()
        )

        if not base_version:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A versão atual do Template não foi encontrada."
                ),
            )

        # --------------------------------------------------------
        # VALIDA NOVA COMPOSIÇÃO
        # --------------------------------------------------------

        resolved_libraries = (
            resolver_selecoes_template_libraries(
                db,
                libraries,
            )
        )

        current_dependencies = (
            db.query(
                TemplateVersionLibraryDependency
            )
            .filter(
                TemplateVersionLibraryDependency.template_version_id ==
                    base_version.id
            )
            .all()
        )

        # O Template registra somente QUAIS Libraries pertencem
        # à composição. LibraryVersion não faz parte da identidade
        # do Template.
        current_library_ids = {
            dependency.library_id
            for dependency in current_dependencies
        }

        requested_library_ids = {
            library.id
            for library, _production_version
            in resolved_libraries
        }

        if current_library_ids == requested_library_ids:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A composição de Libraries informada é igual "
                    "à versão atual do Template."
                ),
            )

        # --------------------------------------------------------
        # VALIDA SNAPSHOT DE CÓDIGO DA VERSÃO BASE
        # --------------------------------------------------------

        base_artifact = resolver_artifact_path(
            base_version.artifact_path
        )

        if not base_artifact.is_file():
            raise HTTPException(
                status_code=404,
                detail=(
                    "O arquivo físico da versão atual do Template "
                    "não foi encontrado."
                ),
            )

        actual_hash = calcular_sha256(
            base_artifact
        )

        if (
            base_version.file_hash and
            actual_hash != base_version.file_hash
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "O snapshot atual do Template falhou na "
                    "validação de integridade."
                ),
            )

        # --------------------------------------------------------
        # PRÓXIMA VERSÃO
        # --------------------------------------------------------

        max_version = (
            db.query(
                func.max(
                    AutomationTemplateVersion.version
                )
            )
            .filter(
                AutomationTemplateVersion.template_id ==
                    template.id
            )
            .scalar()
        )

        next_version = (
            int(
                max_version or 0
            ) +
            1
        )

        artifact_relative = (
            montar_artifact_path_relativo(
                template.id,
                next_version,
            )
        )

        artifact_absolute = (
            BASE_DIRECTORY /
            artifact_relative
        ).resolve()

        version_directory = (
            artifact_absolute.parent
        )

        artifact_absolute.parent.mkdir(
            parents=True,
            exist_ok=False,
        )

        shutil.copy2(
            base_artifact,
            artifact_absolute,
        )

        # --------------------------------------------------------
        # NOVA VERSÃO IMUTÁVEL
        # --------------------------------------------------------

        version = AutomationTemplateVersion(
            template_id=
                template.id,
            version=
                next_version,
            filename=
                base_version.filename,
            artifact_path=
                str(
                    artifact_relative
                ),
            file_hash=
                calcular_sha256(
                    artifact_absolute
                ),
            published_by=
                usuario.id,
        )

        db.add(
            version
        )

        db.flush()

        # --------------------------------------------------------
        # SNAPSHOT DAS LIBRARIES
        # --------------------------------------------------------

        registrar_composicao_template_version(
            db=db,
            template_version_id=
                version.id,
            resolved_libraries=
                resolved_libraries,
            created_by=
                usuario.id,
        )

        # A nova versão passa a ser a atual somente depois de
        # toda a composição ter sido preparada na transação.
        template.current_version_id = (
            version.id
        )

        db.commit()

        db.refresh(
            template
        )

        db.refresh(
            version
        )

        serialized_libraries = (
            serializar_dependencias_template_version(
                db,
                version.id,
            )
        )

        return {
            "status": "success",
            "message": (
                f"Versão v{version.version} criada com a nova "
                "composição de Libraries."
            ),
            "template_id": template.id,
            "version":
                serializar_template_version(
                    version,
                    current_version_id=
                        template.current_version_id,
                ),
            "libraries":
                serialized_libraries,
        }

    except HTTPException:
        db.rollback()

        if version_directory:
            shutil.rmtree(
                version_directory,
                ignore_errors=True,
            )

        raise

    except IntegrityError as error:
        db.rollback()

        if version_directory:
            shutil.rmtree(
                version_directory,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível registrar a nova composição "
                "de Libraries do Template."
            ),
        ) from error

    except Exception as error:
        db.rollback()

        if version_directory:
            shutil.rmtree(
                version_directory,
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível atualizar as Libraries do Template."
            ),
        ) from error
