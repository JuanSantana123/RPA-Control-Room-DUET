from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

from developer_bridge.environment_manager import (
    ProjectEnvironment,
)
from developer_bridge.sdk_runtime import (
    discover_duet_sdk,
)

# ============================================================
# DUET DEVELOPER BRIDGE - IDE PROJECT CONFIGURATION
# ============================================================
#
# Responsabilidade:
#
# - preparar configuração LOCAL da IDE;
# - apontar a IDE para o Python isolado do projeto;
# - disponibilizar _libraries no PYTHONPATH;
# - permitir Run / Debug sem ativação manual de venv;
# - nunca sincronizar essas configurações com o Control Room.
#
# Arquivos gerados:
#
# Workspace/
#
#   .duet/
#       python.env
#
#   .vscode/
#       settings.json
#       launch.json
#
# IMPORTANTE:
#
# .duet e .vscode já são ignorados pelo WorkspaceSync.
#
# Portanto:
#
# - não entram no projeto oficial;
# - não entram na publicação;
# - não alteram o Agent;
# - não alteram o Studio.
# ============================================================


DUET_DIRECTORY_NAME = ".duet"
VSCODE_DIRECTORY_NAME = ".vscode"

PYTHON_ENV_FILE_NAME = "python.env"
VSCODE_SETTINGS_FILE_NAME = "settings.json"
VSCODE_LAUNCH_FILE_NAME = "launch.json"

DUET_DEBUG_CONFIGURATION_NAME = (
    "DUET: Executar Automação"
)


# ============================================================
# JSON
# ============================================================

def _read_json_object(
    path: Path,
) -> dict:
    """
    Lê um JSON local preservando configurações existentes.

    Arquivo inexistente ou inválido é tratado como vazio.
    """

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
        pass

    return {}


def _write_json_atomic(
    path: Path,
    payload: dict,
) -> None:
    """
    Grava JSON local de forma atômica.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

def _libraries_path(
    workspace: Path,
) -> Path:
    """
    Diretório técnico onde ficam as Working Copies
    das Libraries do AutomationProject.
    """

    return (
        workspace
        / "_libraries"
    )


def _python_path_value(
    workspace: Path,
) -> str:
    """
    Monta o PYTHONPATH completo utilizado no desenvolvimento.

    Entradas:

    1. raiz do AutomationProject;
    2. Working Copies das Libraries;
    3. SDK oficial Python do DUET.

    Isso permite simultaneamente:

        from src...
        import logging_core
        from rpa import vault
    """

    sdk = (
        discover_duet_sdk()
    )


    entries = [
        str(
            workspace.resolve()
        ),

        str(
            _libraries_path(
                workspace
            ).resolve()
        ),

        str(
            sdk.root
        ),
    ]


    return os.pathsep.join(
        entries
    )
# ============================================================
# .DUET/PYTHON.ENV
# ============================================================

def _write_python_environment_file(
    *,
    workspace: Path,
    environment: ProjectEnvironment,
) -> Path:
    """
    Gera arquivo de ambiente consumido pelo VS Code/debugpy.

    O arquivo fica dentro de .duet e não é sincronizado.
    """

    duet_directory = (
        workspace
        / DUET_DIRECTORY_NAME
    )

    duet_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        duet_directory
        / PYTHON_ENV_FILE_NAME
    )

    content = "\n".join(
        [
            (
                "PYTHONPATH="
                + _python_path_value(
                    workspace
                )
            ),
            (
                "VIRTUAL_ENV="
                + str(
                    environment.virtual_environment
                )
            ),
            "",
        ]
    )

    destination.write_text(
        content,
        encoding="utf-8",
    )

    return destination


# ============================================================
# VS CODE - SETTINGS
# ============================================================

def _prepare_vscode_settings(
    *,
    workspace: Path,
    environment: ProjectEnvironment,
) -> None:
    """
    Configura o interpretador Python e o terminal integrado.

    Configurações existentes são preservadas.
    """

    vscode_directory = (
        workspace
        / VSCODE_DIRECTORY_NAME
    )

    settings_file = (
        vscode_directory
        / VSCODE_SETTINGS_FILE_NAME
    )

    settings = _read_json_object(
        settings_file
    )


    # --------------------------------------------------------
    # PYTHON DO AUTOMATIONPROJECT
    # --------------------------------------------------------

    settings[
        "python.defaultInterpreterPath"
    ] = str(
        environment.python_executable
    )


    # --------------------------------------------------------
    # ATIVAÇÃO AUTOMÁTICA
    # --------------------------------------------------------

    settings[
        "python.terminal.activateEnvironment"
    ] = True


    # --------------------------------------------------------
    # ENV FILE
    # --------------------------------------------------------

    settings[
        "python.envFile"
    ] = (
        "${workspaceFolder}\\.duet\\python.env"
    )


    # --------------------------------------------------------
    # INTELLISENSE DAS LIBRARIES
    # --------------------------------------------------------

    sdk = (
    discover_duet_sdk()
    )


    settings[
        "python.analysis.extraPaths"
    ] = [
        "${workspaceFolder}",
        "${workspaceFolder}\\_libraries",
        str(
            sdk.root
        ),
        ]


    # --------------------------------------------------------
    # TERMINAL INTEGRADO
    # --------------------------------------------------------
    #
    # Mesmo que o VS Code já esteja aberto em outro processo,
    # qualquer NOVO terminal deste Workspace recebe explicitamente:
    #
    # - VIRTUAL_ENV;
    # - PYTHONPATH;
    # - Scripts da venv no início do PATH.
    #
    # Assim:
    #
    #     python main.py
    #
    # utiliza o Python correto sem activation manual.
    # --------------------------------------------------------

    current_terminal_environment = (
        settings.get(
            "terminal.integrated.env.windows"
        )
    )

    if not isinstance(
        current_terminal_environment,
        dict,
    ):
        current_terminal_environment = {}


    scripts_directory = (
        environment.virtual_environment
        / "Scripts"
    )


    current_terminal_environment.update(
        {
            "VIRTUAL_ENV":
                str(
                    environment.virtual_environment
                ),

            "PYTHONPATH":
                _python_path_value(
                    workspace
                ),

            "PATH":
                (
                    str(
                        scripts_directory
                    )
                    + os.pathsep
                    + os.environ.get(
                        "PATH",
                        "",
                    )
                ),
        }
    )


    settings[
        "terminal.integrated.env.windows"
    ] = current_terminal_environment


    _write_json_atomic(
        settings_file,
        settings,
    )


# ============================================================
# VS CODE - LAUNCH.JSON
# ============================================================

def _prepare_vscode_launch(
    *,
    workspace: Path,
    environment: ProjectEnvironment,
) -> None:
    """
    Cria configuração de Debug/Run do DUET.

    O desenvolvedor poderá utilizar F5 diretamente.
    """

    vscode_directory = (
        workspace
        / VSCODE_DIRECTORY_NAME
    )

    launch_file = (
        vscode_directory
        / VSCODE_LAUNCH_FILE_NAME
    )

    launch = _read_json_object(
        launch_file
    )


    configurations = launch.get(
        "configurations"
    )


    if not isinstance(
        configurations,
        list,
    ):
        configurations = []


    # Remove somente uma configuração anterior gerada pelo DUET.
    #
    # Qualquer outra configuração criada pelo desenvolvedor
    # permanece intacta.
    configurations = [
        item
        for item in configurations
        if not (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "name"
            )
            == DUET_DEBUG_CONFIGURATION_NAME
        )
    ]


    configurations.append(
        {
            "name":
                DUET_DEBUG_CONFIGURATION_NAME,

            "type":
                "debugpy",

            "request":
                "launch",

            "program":
                "${workspaceFolder}\\main.py",

            "cwd":
                "${workspaceFolder}",

            "console":
                "integratedTerminal",

            "python":
                str(
                    environment.python_executable
                ),

            "envFile":
                "${workspaceFolder}\\.duet\\python.env",

            "justMyCode":
                False,
        }
    )


    launch[
        "version"
    ] = "0.2.0"


    launch[
        "configurations"
    ] = configurations


    _write_json_atomic(
        launch_file,
        launch,
    )


# ============================================================
# AMBIENTE HERDADO PELA IDE
# ============================================================

def build_ide_process_environment(
    *,
    workspace: Path,
    environment: ProjectEnvironment,
) -> dict[str, str]:
    """
    Monta as variáveis que serão herdadas pelo processo da IDE.

    Isso também ajuda IDEs diferentes de VS Code/Cursor.
    """

    process_environment = dict(
        os.environ
    )


    scripts_directory = (
        environment.virtual_environment
        / "Scripts"
    )


    current_path = process_environment.get(
        "PATH",
        "",
    )


    process_environment[
        "PATH"
    ] = (
        str(
            scripts_directory
        )
        + os.pathsep
        + current_path
    )


    process_environment[
        "VIRTUAL_ENV"
    ] = str(
        environment.virtual_environment
    )


    existing_python_path = (
        process_environment.get(
            "PYTHONPATH",
            "",
        )
    )


    duet_python_path = (
        _python_path_value(
            workspace
        )
    )


    if existing_python_path:

        process_environment[
            "PYTHONPATH"
        ] = (
            duet_python_path
            + os.pathsep
            + existing_python_path
        )

    else:

        process_environment[
            "PYTHONPATH"
        ] = duet_python_path


    return process_environment


# ============================================================
# PREPARAR WORKSPACE PARA IDE
# ============================================================

def prepare_ide_workspace(
    *,
    workspace: Path,
    environment: ProjectEnvironment,
) -> None:
    """
    Prepara arquivos técnicos locais da IDE.

    Atualmente:
    - .duet/python.env;
    - VS Code;
    - Cursor, que reutiliza o formato VS Code.

    Outras IDEs continuam recebendo o ambiente através
    do processo pai.
    """

    workspace = workspace.resolve()


    _write_python_environment_file(
        workspace=workspace,
        environment=environment,
    )


    _prepare_vscode_settings(
        workspace=workspace,
        environment=environment,
    )


    _prepare_vscode_launch(
        workspace=workspace,
        environment=environment,
    )