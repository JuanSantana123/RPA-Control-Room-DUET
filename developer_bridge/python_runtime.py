from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


# ============================================================
# DUET DEVELOPER BRIDGE - PYTHON RUNTIME
# ============================================================
#
# Responsabilidade:
#
# - localizar um Python instalado na máquina do desenvolvedor;
# - nunca instalar Python;
# - nunca utilizar silenciosamente o venv interno do Bridge
#   como runtime do AutomationProject;
# - permitir configuração explícita quando necessário;
# - validar o executável antes de utilizá-lo.
#
# IMPORTANTE:
#
# Este módulo pertence SOMENTE ao Developer Bridge.
#
# Ele não altera:
# - RPA Agent;
# - Control Room;
# - Scheduler;
# - runtime de Produção.
# ============================================================


class PythonRuntimeNotFoundError(RuntimeError):
    """Nenhum Python válido foi encontrado na máquina."""


@dataclass(frozen=True)
class PythonRuntime:
    """
    Representa um Python local validado.

    executable:
        Caminho real do python.exe.

    version:
        Versão completa detectada.
    """

    executable: Path
    version: tuple[int, int, int]

    @property
    def version_text(self) -> str:
        return ".".join(
            str(part)
            for part in self.version
        )


def _creation_flags() -> int:
    """
    Evita abrir janelas extras de console quando o Bridge
    estiver sendo executado através de pythonw.exe.
    """

    return int(
        getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )
    )


def _is_inside(
    candidate: Path,
    parent: Path,
) -> bool:
    """
    Verifica de forma segura se candidate está dentro de parent.
    """

    try:
        candidate.resolve().relative_to(
            parent.resolve()
        )
        return True

    except ValueError:
        return False


def _is_bridge_virtual_environment(
    executable: Path,
) -> bool:
    """
    Impede que o ambiente interno do Developer Bridge seja
    usado como ambiente do robô.

    O Bridge possui dependências próprias e deve permanecer
    completamente separado do projeto desenvolvido.
    """

    return _is_inside(
        executable,
        Path(sys.prefix),
    )


def _probe_python(
    executable: Path,
) -> PythonRuntime | None:
    """
    Executa uma validação mínima no Python candidato.

    Não confia apenas no nome python.exe.
    """

    if (
        not executable.exists()
        or not executable.is_file()
    ):
        return None

    try:

        result = subprocess.run(
            [
                str(executable),
                "-c",
                (
                    "import sys;"
                    "print("
                    "sys.version_info.major,"
                    "sys.version_info.minor,"
                    "sys.version_info.micro,"
                    "sep='.'"
                    ");"
                    "print(sys.executable)"
                ),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
            creationflags=_creation_flags(),
        )

    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return None


    if result.returncode != 0:
        return None


    lines = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


    if len(lines) < 2:
        return None


    version_parts = (
        lines[0]
        .strip()
        .split(".")
    )


    if len(version_parts) != 3:
        return None


    try:

        version = (
            int(version_parts[0]),
            int(version_parts[1]),
            int(version_parts[2]),
        )

    except ValueError:
        return None


    resolved_executable = Path(
        lines[1]
    )


    if not resolved_executable.exists():
        resolved_executable = executable


    return PythonRuntime(
        executable=resolved_executable.resolve(),
        version=version,
    )


def _configured_python() -> list[Path]:
    """
    Permite definir explicitamente um Python para desenvolvimento.

    Exemplo futuro:

        DUET_DEVELOPER_PYTHON=
            C:\\Python312\\python.exe

    Essa configuração é opcional.
    """

    configured = (
        os.environ
        .get(
            "DUET_DEVELOPER_PYTHON",
            "",
        )
        .strip()
        .strip('"')
    )


    if not configured:
        return []


    return [
        Path(configured)
    ]


def _base_python_candidates() -> list[Path]:
    """
    Tenta recuperar o Python real utilizado para criar o venv
    do Developer Bridge.

    Exemplo:

        Bridge:
            developer_bridge\\.venv\\Scripts\\python.exe

        Python real:
            C:\\Users\\...\\Python312\\python.exe
    """

    candidates: list[Path] = []


    base_executable = getattr(
        sys,
        "_base_executable",
        None,
    )


    if base_executable:
        candidates.append(
            Path(base_executable)
        )


    base_prefix_python = (
        Path(sys.base_prefix)
        / "python.exe"
    )


    candidates.append(
        base_prefix_python
    )


    return candidates


def _py_launcher_candidates() -> list[Path]:
    """
    Consulta o Python Launcher oficial do Windows, quando existe.

    Exemplo:

        py -0p
    """

    launcher = shutil.which(
        "py"
    )


    if not launcher:
        return []


    try:

        result = subprocess.run(
            [
                launcher,
                "-0p",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
            creationflags=_creation_flags(),
        )

    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return []


    if result.returncode != 0:
        return []


    candidates: list[Path] = []


    for line in result.stdout.splitlines():

        # Captura o caminho absoluto retornado pelo launcher.
        #
        # Exemplos:
        #
        # -V:3.12 * C:\...\Python312\python.exe
        #
        # -3.11     C:\...\Python311\python.exe
        match = re.search(
            r"([A-Za-z]:\\.*python(?:w)?\.exe)\s*$",
            line.strip(),
            flags=re.IGNORECASE,
        )


        if match:
            candidates.append(
                Path(
                    match.group(1)
                )
            )


    return candidates


def _path_candidates() -> list[Path]:
    """
    Último fallback: procura Python no PATH do Windows.
    """

    candidates: list[Path] = []


    for command in (
        "python",
        "python3",
    ):

        value = shutil.which(
            command
        )


        if value:
            candidates.append(
                Path(value)
            )


    return candidates


def discover_system_python() -> PythonRuntime:
    """
    Localiza o Python que será utilizado para criar o ambiente
    isolado do AutomationProject.

    Ordem:

    1. DUET_DEVELOPER_PYTHON;
    2. Python base do Bridge;
    3. Python Launcher do Windows;
    4. PATH.

    O primeiro candidato válido vence.
    """

    candidates = (
        _configured_python()
        + _base_python_candidates()
        + _py_launcher_candidates()
        + _path_candidates()
    )


    seen: set[str] = set()


    for candidate in candidates:

        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate


        key = str(
            resolved
        ).lower()


        if key in seen:
            continue


        seen.add(
            key
        )


        # O venv do próprio Bridge nunca deve virar
        # o ambiente de execução do robô.
        if _is_bridge_virtual_environment(
            resolved
        ):
            continue


        runtime = _probe_python(
            resolved
        )


        if runtime:
            return runtime


    raise PythonRuntimeNotFoundError(
        "Nenhum Python instalado foi encontrado para "
        "execução local do AutomationProject. "
        "O DUET Developer Tools não instala Python."
    )