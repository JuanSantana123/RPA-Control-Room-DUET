# ============================================================
# DUET CORE - DEVELOPMENT - PROJECT ENTRYPOINT SERVICE
# ============================================================
#
# Responsabilidade:
# - normalizar o caminho do entrypoint de um AutomationProject;
# - consultar o entrypoint configurado e seu estado físico;
# - alterar o entrypoint somente com Checkout próprio;
# - validar o entrypoint antes de build/execução/publicação.
#
# O serviço não executa código e não publica versões.
# ============================================================

from __future__ import annotations

from pathlib import Path, PurePosixPath

from fastapi import HTTPException
from sqlalchemy.orm import Session

from development.checkout_service import exigir_checkout_workspace
from models import AutomationProject


DEFAULT_ENTRYPOINT_PATH = "main.py"
MAX_ENTRYPOINT_LENGTH = 1000


def normalizar_entrypoint_path(value: str | None) -> str:
    """Normaliza e valida um caminho relativo de arquivo Python."""

    raw = str(value or DEFAULT_ENTRYPOINT_PATH).strip().replace("\\", "/")

    if not raw:
        raw = DEFAULT_ENTRYPOINT_PATH

    if len(raw) > MAX_ENTRYPOINT_LENGTH:
        raise ValueError("O caminho do entrypoint ultrapassa 1000 caracteres.")

    # PurePosixPath deixa a regra independente do SO do Control Room.
    path = PurePosixPath(raw)

    if path.is_absolute() or raw.startswith("/"):
        raise ValueError("O entrypoint precisa ser relativo à raiz do projeto.")

    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("O entrypoint possui um caminho relativo inválido.")

    # Evita caminhos Windows absolutos/drive mesmo quando o Control Room
    # estiver executando em outro sistema operacional.
    if path.parts and ":" in path.parts[0]:
        raise ValueError("O entrypoint precisa ser relativo à raiz do projeto.")

    if path.suffix.lower() != ".py":
        raise ValueError("O entrypoint precisa apontar para um arquivo .py.")

    return path.as_posix()


def obter_workspace_projeto(project_id: int) -> Path:
    """Retorna a raiz física do Workspace oficial do projeto."""

    # DUET_ENTRYPOINT_V1_0_1_WORKSPACE_REPOSITORY_IMPORT
    # WORKSPACE_REPOSITORY pertence ao project_packager; o import local mantém o acoplamento explícito e evita import incorreto.
    from packaging.project_packager import WORKSPACE_REPOSITORY

    return (WORKSPACE_REPOSITORY / str(project_id)).resolve()


def resolver_entrypoint_workspace(
    project_id: int,
    entrypoint_path: str,
    *,
    exigir_existencia: bool = True,
) -> Path:
    """Resolve o entrypoint garantindo confinamento dentro do Workspace."""

    normalized = normalizar_entrypoint_path(entrypoint_path)
    workspace = obter_workspace_projeto(project_id)
    target = (workspace / Path(normalized)).resolve()

    if target != workspace and workspace not in target.parents:
        raise ValueError("O entrypoint está fora do workspace do projeto.")

    if exigir_existencia and not target.is_file():
        raise FileNotFoundError(
            f'O arquivo de entrada "{normalized}" não existe no Workspace.'
        )

    return target


def _obter_projeto_ativo(db: Session, project_id: int) -> AutomationProject:
    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id == project_id,
            AutomationProject.is_active == 1,
        )
        .first()
    )

    if not projeto:
        raise HTTPException(404, "Projeto de Desenvolvimento não encontrado.")

    return projeto


def _listar_arquivos_python(project_id: int) -> list[str]:
    """Lista arquivos .py existentes no Workspace, em ordem estável."""

    workspace = obter_workspace_projeto(project_id)

    if not workspace.is_dir():
        return []

    result: list[str] = []

    for path in workspace.rglob("*.py"):
        if not path.is_file():
            continue

        try:
            relative = path.resolve().relative_to(workspace).as_posix()
        except ValueError:
            continue

        result.append(relative)

    return sorted(result, key=str.casefold)


def consultar_entrypoint_projeto_service(
    project_id: int,
    db: Session,
) -> dict:
    """Retorna configuração, existência física e opções .py do projeto."""

    projeto = _obter_projeto_ativo(db, project_id)

    try:
        entrypoint_path = normalizar_entrypoint_path(
            getattr(projeto, "entrypoint_path", None)
        )
        target = resolver_entrypoint_workspace(
            project_id,
            entrypoint_path,
            exigir_existencia=False,
        )
        exists = target.is_file()
        valid = True
    except ValueError:
        entrypoint_path = str(
            getattr(projeto, "entrypoint_path", None)
            or DEFAULT_ENTRYPOINT_PATH
        )
        exists = False
        valid = False

    return {
        "status": "success",
        "project_id": projeto.id,
        "entrypoint_path": entrypoint_path,
        "exists": exists,
        "valid": valid,
        "python_files": _listar_arquivos_python(project_id),
    }


def atualizar_entrypoint_projeto_service(
    project_id: int,
    entrypoint_path: str,
    db: Session,
    usuario,
) -> dict:
    """Altera o entrypoint do projeto sem criar Checkout automaticamente."""

    projeto = _obter_projeto_ativo(db, project_id)

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    try:
        normalized = normalizar_entrypoint_path(entrypoint_path)
        resolver_entrypoint_workspace(
            project_id,
            normalized,
            exigir_existencia=True,
        )
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(409, str(error)) from error

    projeto.entrypoint_path = normalized
    db.commit()
    db.refresh(projeto)

    return consultar_entrypoint_projeto_service(
        project_id=project_id,
        db=db,
    )


def exigir_entrypoint_valido_projeto(
    project: AutomationProject,
) -> str:
    """Valida o entrypoint antes de gerar um artefato executável."""

    try:
        normalized = normalizar_entrypoint_path(
            getattr(project, "entrypoint_path", None)
        )
        resolver_entrypoint_workspace(
            project.id,
            normalized,
            exigir_existencia=True,
        )
    except (ValueError, FileNotFoundError) as error:
        raise RuntimeError(str(error)) from error

    return normalized
