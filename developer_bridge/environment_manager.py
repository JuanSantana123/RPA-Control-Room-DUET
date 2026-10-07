from __future__ import annotations

import hashlib
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from developer_bridge.config import (
    DUET_LOCAL_ROOT,
)
from developer_bridge.python_runtime import (
    PythonRuntime,
    discover_system_python,
)


# ============================================================
# DUET DEVELOPER BRIDGE - ENVIRONMENT MANAGER
# ============================================================
#
# Responsabilidade:
#
# - criar ambiente Python isolado por AutomationProject;
# - reutilizar o ambiente nas próximas aberturas;
# - instalar requirements.txt automaticamente;
# - reinstalar somente quando requirements.txt mudar;
# - manter o ambiente FORA do Workspace sincronizado;
# - nunca instalar Python.
#
# Estrutura:
#
# %LOCALAPPDATA%\DUET\
#
#     Workspaces\
#         115\
#
#     Environments\
#         115\
#             .venv\
#             state.json
#
# Dessa forma:
#
# - .venv não entra no projeto;
# - .venv não é sincronizado;
# - .venv não é publicado;
# - cada AutomationProject possui dependências isoladas.
# ============================================================


logger = logging.getLogger(
    "duet.developer_bridge.environment"
)


ENVIRONMENTS_ROOT = (
    DUET_LOCAL_ROOT
    / "Environments"
)


STATE_FILE_NAME = (
    "state.json"
)


REQUIREMENTS_FILE_NAME = (
    "requirements.txt"
)


class EnvironmentPreparationError(
    RuntimeError
):
    """
    Falha durante preparação do ambiente local do projeto.
    """


@dataclass(frozen=True)
class ProjectEnvironment:
    """
    Resultado da preparação do ambiente.

    python_executable:
        Interpretador isolado que deverá ser utilizado
        pelo VS Code / PyCharm / Cursor.

    environment_root:
        Pasta técnica do ambiente DUET.

    created:
        True quando o venv foi criado nesta execução.

    requirements_installed:
        True quando pip install foi executado nesta execução.
    """

    project_id: int
    environment_root: Path
    virtual_environment: Path
    python_executable: Path
    source_runtime: PythonRuntime
    created: bool
    requirements_installed: bool


def _creation_flags() -> int:
    """
    Impede abertura de console extra quando executado
    pelo Developer Bridge via pythonw.exe.
    """

    return int(
        getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )
    )


def project_environment_root(
    project_id: int,
) -> Path:
    """
    Retorna a pasta técnica do ambiente do projeto.
    """

    return (
        ENVIRONMENTS_ROOT
        / str(project_id)
    )


def project_virtual_environment(
    project_id: int,
) -> Path:
    """
    Retorna a pasta do venv do projeto.
    """

    return (
        project_environment_root(
            project_id
        )
        / ".venv"
    )


def project_python_executable(
    project_id: int,
) -> Path:
    """
    Python isolado utilizado pelo AutomationProject.
    """

    return (
        project_virtual_environment(
            project_id
        )
        / "Scripts"
        / "python.exe"
    )


def _state_file(
    project_id: int,
) -> Path:
    """
    Arquivo técnico utilizado para detectar alterações
    no runtime e no requirements.txt.
    """

    return (
        project_environment_root(
            project_id
        )
        / STATE_FILE_NAME
    )


def _requirements_hash(
    requirements: Path,
) -> str | None:
    """
    Calcula fingerprint do requirements.txt.

    Datas de modificação não são utilizadas:
    apenas o conteúdo importa.
    """

    if not requirements.exists():
        return None


    return hashlib.sha256(
        requirements.read_bytes()
    ).hexdigest()


def _has_effective_requirements(
    requirements: Path,
) -> bool:
    """
    Retorna True quando requirements.txt contém
    alguma instrução efetiva para o pip.

    Linhas vazias e comentários não contam.
    """

    if not requirements.exists():
        return False


    try:

        content = requirements.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError as error:

        raise EnvironmentPreparationError(
            "requirements.txt não está em UTF-8."
        ) from error


    for raw_line in content.splitlines():

        line = raw_line.strip()


        if (
            line
            and not line.startswith("#")
        ):
            return True


    return False


def _load_state(
    project_id: int,
) -> dict:
    """
    Carrega estado persistido do ambiente.

    Estado inválido é tratado como ambiente ainda não preparado.
    """

    path = _state_file(
        project_id
    )


    if not path.exists():
        return {}


    try:

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )


        if isinstance(
            payload,
            dict,
        ):
            return payload


    except (
        OSError,
        json.JSONDecodeError,
    ):
        logger.warning(
            "Estado do ambiente inválido: %s",
            path,
        )


    return {}


def _save_state(
    project_id: int,
    payload: dict,
) -> None:
    """
    Persiste state.json de forma atômica.
    """

    root = project_environment_root(
        project_id
    )


    root.mkdir(
        parents=True,
        exist_ok=True,
    )


    destination = _state_file(
        project_id
    )


    temporary = destination.with_suffix(
        ".tmp"
    )


    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


    temporary.replace(
        destination
    )


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    description: str,
) -> None:
    """
    Executa comando técnico e transforma falhas em erro
    legível para o Developer Bridge.
    """

    try:

        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=_creation_flags(),
        )

    except subprocess.TimeoutExpired as error:

        raise EnvironmentPreparationError(
            f"{description} excedeu o tempo limite."
        ) from error

    except OSError as error:

        raise EnvironmentPreparationError(
            f"Não foi possível executar: {description}."
        ) from error


    if result.returncode == 0:
        return


    details = (
        result.stderr.strip()
        or result.stdout.strip()
        or "Erro sem detalhes adicionais."
    )


    raise EnvironmentPreparationError(
        f"{description} falhou.\n\n{details}"
    )


def _create_virtual_environment(
    *,
    runtime: PythonRuntime,
    project_id: int,
    workspace: Path,
) -> Path:
    """
    Cria o venv do projeto usando o Python instalado
    na máquina do desenvolvedor.
    """

    environment_root = (
        project_environment_root(
            project_id
        )
    )


    virtual_environment = (
        project_virtual_environment(
            project_id
        )
    )


    environment_root.mkdir(
        parents=True,
        exist_ok=True,
    )


    _run_command(
        [
            str(
                runtime.executable
            ),
            "-m",
            "venv",
            str(
                virtual_environment
            ),
        ],
        cwd=workspace,
        timeout=180,
        description=(
            "Criação do ambiente Python "
            "do AutomationProject"
        ),
    )


    python_executable = (
        project_python_executable(
            project_id
        )
    )


    if not python_executable.exists():

        raise EnvironmentPreparationError(
            "O ambiente foi criado, mas python.exe "
            "não foi localizado."
        )


    logger.info(
        "Ambiente Python criado para projeto %s: %s",
        project_id,
        virtual_environment,
    )


    return python_executable


def _remove_virtual_environment(
    project_id: int,
) -> None:
    """
    Remove somente o ambiente técnico local do projeto.

    Nunca toca no Workspace.
    """

    virtual_environment = (
        project_virtual_environment(
            project_id
        )
    )


    if virtual_environment.exists():

        shutil.rmtree(
            virtual_environment
        )


def _runtime_changed(
    *,
    state: dict,
    runtime: PythonRuntime,
) -> bool:
    """
    Detecta se o ambiente foi criado a partir de outro Python.
    """

    previous_python = str(
        state.get(
            "source_python",
            ""
        )
    ).lower()


    previous_version = str(
        state.get(
            "source_python_version",
            ""
        )
    )


    current_python = str(
        runtime.executable
    ).lower()


    return (
        bool(previous_python)
        and (
            previous_python != current_python
            or previous_version != runtime.version_text
        )
    )


def _install_requirements(
    *,
    python_executable: Path,
    requirements: Path,
    workspace: Path,
) -> None:
    """
    Instala requirements.txt dentro do venv isolado.

    --no-input evita que o Bridge fique preso esperando
    interação invisível do usuário.
    """

    _run_command(
        [
            str(
                python_executable
            ),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "-r",
            str(
                requirements
            ),
        ],
        cwd=workspace,
        timeout=900,
        description=(
            "Instalação das dependências "
            "do requirements.txt"
        ),
    )


def prepare_project_environment(
    *,
    project_id: int,
    workspace: Path,
) -> ProjectEnvironment:
    """
    Prepara o ambiente Python de desenvolvimento.

    Fluxo:

    1. detecta Python instalado;
    2. cria/reutiliza venv;
    3. verifica requirements.txt;
    4. instala apenas quando mudou;
    5. persiste fingerprint;
    6. devolve python.exe pronto para uso.

    Esta função NÃO executa main.py.
    """

    workspace = (
        workspace.resolve()
    )


    if not workspace.exists():

        raise EnvironmentPreparationError(
            "Workspace local do projeto não existe."
        )


    runtime = (
        discover_system_python()
    )


    state = (
        _load_state(
            project_id
        )
    )


    python_executable = (
        project_python_executable(
            project_id
        )
    )


    created = False


    # Se o Python de origem mudou, recriamos somente o
    # ambiente local de desenvolvimento.
    if (
        python_executable.exists()
        and _runtime_changed(
            state=state,
            runtime=runtime,
        )
    ):

        logger.info(
            "Python de origem mudou. "
            "Recriando ambiente do projeto %s.",
            project_id,
        )


        _remove_virtual_environment(
            project_id
        )


        python_executable = (
            project_python_executable(
                project_id
            )
        )


    if not python_executable.exists():

        python_executable = (
            _create_virtual_environment(
                runtime=runtime,
                project_id=project_id,
                workspace=workspace,
            )
        )

        created = True


    requirements = (
        workspace
        / REQUIREMENTS_FILE_NAME
    )


    current_requirements_hash = (
        _requirements_hash(
            requirements
        )
    )


    previous_requirements_hash = (
        state.get(
            "requirements_hash"
        )
    )


    requirements_installed = False


    requirements_changed = (
        current_requirements_hash
        != previous_requirements_hash
    )


    if (
        requirements_changed
        and _has_effective_requirements(
            requirements
        )
    ):

        logger.info(
            "requirements.txt alterado. "
            "Sincronizando dependências do projeto %s.",
            project_id,
        )


        _install_requirements(
            python_executable=
                python_executable,

            requirements=
                requirements,

            workspace=
                workspace,
        )


        requirements_installed = True


    _save_state(
        project_id,
        {
            "project_id":
                project_id,

            "source_python":
                str(
                    runtime.executable
                ),

            "source_python_version":
                runtime.version_text,

            "virtual_environment":
                str(
                    project_virtual_environment(
                        project_id
                    )
                ),

            "python_executable":
                str(
                    python_executable
                ),

            "requirements_hash":
                current_requirements_hash,
        },
    )


    logger.info(
        "Ambiente do projeto %s preparado. Python: %s",
        project_id,
        python_executable,
    )


    return ProjectEnvironment(
        project_id=
            project_id,

        environment_root=
            project_environment_root(
                project_id
            ),

        virtual_environment=
            project_virtual_environment(
                project_id
            ),

        python_executable=
            python_executable,

        source_runtime=
            runtime,

        created=
            created,

        requirements_installed=
            requirements_installed,
    )