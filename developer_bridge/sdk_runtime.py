from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from developer_bridge.config import (
    DEVELOPER_TOOLS_ROOT,
)


# ============================================================
# DUET DEVELOPER BRIDGE - SDK RUNTIME
# ============================================================
#
# Responsabilidade:
#
# - localizar o SDK oficial Python do DUET;
# - permitir que IDEs externas resolvam:
#
#       from rpa import vault
#
# - não depender exclusivamente da instalação do Agent;
# - permitir futuro empacotamento do SDK junto ao
#   DUET Developer Tools.
#
# O SDK NÃO pertence:
#
# - ao requirements.txt do Robot;
# - às Libraries do AutomationProject;
# - à venv do Developer Bridge.
#
# Ele é uma dependência de plataforma do próprio DUET.
# ============================================================


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


@dataclass(frozen=True)
class DuetSdkRuntime:
    """
    Representa o SDK oficial localizado.

    root:
        Diretório que precisa entrar no PYTHONPATH.

        Exemplo:

            C:\\RPA-Agent\\sdk

    package:
        Diretório físico do pacote rpa.

        Exemplo:

            C:\\RPA-Agent\\sdk\\rpa
    """

    root: Path
    package: Path


def _is_valid_sdk(
    root: Path,
) -> bool:
    """
    Verifica se o diretório contém a estrutura mínima
    esperada do SDK Python do DUET.
    """

    package = (
        root
        / "rpa"
    )

    return (
        root.is_dir()
        and package.is_dir()
        and (
            package
            / "__init__.py"
        ).is_file()
        and (
            package
            / "vault.py"
        ).is_file()
    )


def _candidate_sdk_roots() -> list[Path]:
    """
    Retorna candidatos em ordem de prioridade.

    Ordem:

    1. configuração explícita;
    2. SDK empacotado com Developer Tools;
    3. RPA-Agent irmão durante desenvolvimento;
    4. Agent instalado em C:\\RPA-Agent.
    """

    candidates: list[Path] = []


    # --------------------------------------------------------
    # 1. OVERRIDE EXPLÍCITO
    # --------------------------------------------------------

    configured = (
        os.environ.get(
            "DUET_DEVELOPER_SDK"
        )
    )

    if configured:

        candidates.append(
            Path(
                configured
            )
        )


    # --------------------------------------------------------
    # 2. DEVELOPER TOOLS INSTALADO
    # --------------------------------------------------------
    #
    # No produto final poderemos distribuir:
    #
    # %LOCALAPPDATA%\DUET\DeveloperTools\sdk\rpa
    #
    # sem exigir que o Agent esteja instalado na máquina
    # do desenvolvedor.
    # --------------------------------------------------------

    candidates.append(
        DEVELOPER_TOOLS_ROOT
        / "sdk"
    )


    # --------------------------------------------------------
    # 3. AMBIENTE DE DESENVOLVIMENTO DO DUET
    # --------------------------------------------------------
    #
    # Estrutura atual:
    #
    # Projeto RPA\
    #   RPA-Control-Room\
    #   RPA-Agent\
    #
    # Portanto, durante desenvolvimento podemos reutilizar
    # exatamente o mesmo SDK oficial do Agent.
    # --------------------------------------------------------

    candidates.append(
        PROJECT_ROOT.parent
        / "RPA-Agent"
        / "sdk"
    )


    # --------------------------------------------------------
    # 4. AGENT INSTALADO
    # --------------------------------------------------------
    #
    # Fallback útil em máquinas que também possuem o Agent.
    # Não será a dependência principal do produto final.
    # --------------------------------------------------------

    candidates.append(
        Path(
            r"C:\RPA-Agent\sdk"
        )
    )


    return candidates


def discover_duet_sdk() -> DuetSdkRuntime:
    """
    Localiza o SDK oficial Python do DUET.

    Falha explicitamente se nenhum SDK válido estiver
    disponível, evitando um ModuleNotFoundError obscuro
    somente durante o F5.
    """

    checked: list[str] = []


    for candidate in (
        _candidate_sdk_roots()
    ):

        try:

            resolved = (
                candidate
                .expanduser()
                .resolve()
            )

        except OSError:

            resolved = candidate


        checked.append(
            str(
                resolved
            )
        )


        if not _is_valid_sdk(
            resolved
        ):
            continue


        return DuetSdkRuntime(
            root=resolved,
            package=(
                resolved
                / "rpa"
            ),
        )


    formatted = "\n".join(
        f"  - {path}"
        for path in checked
    )


    raise RuntimeError(
        "SDK Python do DUET não foi encontrado.\n"
        "Diretórios verificados:\n"
        f"{formatted}"
    )