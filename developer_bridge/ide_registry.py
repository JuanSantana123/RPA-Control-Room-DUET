from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


# ============================================================
# DUET DEVELOPER BRIDGE - IDE REGISTRY
# ============================================================
#
# Responsabilidade:
#
# - detectar IDEs instaladas;
# - permitir seleção da IDE;
# - abrir o Workspace local;
# - propagar o ambiente Python preparado pelo DUET.
#
# Este módulo NÃO:
#
# - cria venv;
# - instala requirements;
# - sincroniza Workspace.
#
# Essas responsabilidades permanecem em módulos separados.
# ============================================================


@dataclass(frozen=True)
class IdeOption:
    name: str
    executable: Path


def _candidate_paths() -> list[
    tuple[
        str,
        Path,
    ]
]:
    """
    Localiza executáveis conhecidos.
    """

    local_app_data = Path(
        os.environ.get(
            "LOCALAPPDATA",
            "",
        )
    )

    program_files = Path(
        os.environ.get(
            "ProgramFiles",
            r"C:\Program Files",
        )
    )


    candidates: list[
        tuple[
            str,
            Path,
        ]
    ] = []


    for name, command in (
        (
            "Visual Studio Code",
            "code",
        ),
        (
            "Cursor",
            "cursor",
        ),
        (
            "PyCharm",
            "pycharm64",
        ),
        (
            "PyCharm",
            "pycharm",
        ),
    ):

        found = shutil.which(
            command
        )


        if found:

            candidates.append(
                (
                    name,
                    Path(found),
                )
            )


    candidates.extend(
        [
            (
                "Visual Studio Code",
                (
                    local_app_data
                    / "Programs"
                    / "Microsoft VS Code"
                    / "Code.exe"
                ),
            ),

            (
                "Visual Studio Code",
                (
                    program_files
                    / "Microsoft VS Code"
                    / "Code.exe"
                ),
            ),

            (
                "Cursor",
                (
                    local_app_data
                    / "Programs"
                    / "cursor"
                    / "Cursor.exe"
                ),
            ),
        ]
    )


    jetbrains_root = (
        program_files
        / "JetBrains"
    )


    if jetbrains_root.exists():

        for executable in (
            jetbrains_root.glob(
                "PyCharm*\\bin\\pycharm64.exe"
            )
        ):

            candidates.append(
                (
                    "PyCharm",
                    executable,
                )
            )


    return candidates


def detect_ides() -> list[
    IdeOption
]:
    """
    Detecta IDEs conhecidas sem duplicar executáveis.
    """

    result: list[
        IdeOption
    ] = []


    seen: set[str] = set()


    for name, executable in (
        _candidate_paths()
    ):

        try:

            resolved = (
                executable.resolve()
            )

        except Exception:

            resolved = executable


        key = str(
            resolved
        ).lower()


        if (
            key in seen
            or not executable.exists()
        ):
            continue


        seen.add(
            key
        )


        result.append(
            IdeOption(
                name=name,
                executable=executable,
            )
        )


    return result


# ============================================================
# ABRIR IDE
# ============================================================

def _launch(
    executable: Path,
    workspace: Path,
    process_environment:
        Mapping[str, str] | None = None,
) -> None:
    """
    Abre a IDE apontando para o Workspace.

    Quando o ambiente DUET foi preparado, a IDE recebe:
    - PATH;
    - VIRTUAL_ENV;
    - PYTHONPATH.
    """

    subprocess.Popen(
        [
            str(
                executable
            ),
            str(
                workspace
            ),
        ],
        cwd=str(
            workspace
        ),
        env=(
            dict(
                process_environment
            )
            if process_environment
            is not None
            else None
        ),
        close_fds=True,
    )


def choose_and_launch_ide(
    workspace: Path,
    project_name: str,
    *,
    process_environment:
        Mapping[str, str] | None = None,
) -> None:
    """
    Permite:
    - IDE detectada;
    - qualquer outro .exe;
    - apenas abrir a pasta.
    """

    options = detect_ides()


    try:

        import tkinter as tk

        from tkinter import (
            filedialog,
            messagebox,
        )

    except ImportError:

        os.startfile(
            workspace
        )

        return


    root = tk.Tk()

    root.title(
        "DUET Developer Tools"
    )

    root.geometry(
        "560x380"
    )

    root.minsize(
        560,
        380,
    )


    selected: dict[
        str,
        Path | str | None,
    ] = {
        "value":
            None
    }


    tk.Label(
        root,
        text=(
            f"Abrir {project_name}"
        ),
        font=(
            "Segoe UI",
            14,
            "bold",
        ),
    ).pack(
        anchor="w",
        padx=24,
        pady=(
            24,
            6,
        ),
    )


    tk.Label(
        root,
        text=(
            "Escolha a IDE que deve abrir o Workspace "
            "sincronizado do DUET.\n"
            "O ambiente Python do projeto será configurado "
            "automaticamente."
        ),
        font=(
            "Segoe UI",
            10,
        ),
        justify="left",
    ).pack(
        anchor="w",
        padx=24,
        pady=(
            0,
            16,
        ),
    )


    listbox = tk.Listbox(
        root,
        font=(
            "Segoe UI",
            10,
        ),
        height=8,
        activestyle="dotbox",
    )


    listbox.pack(
        fill="both",
        expand=True,
        padx=24,
    )


    for option in options:

        listbox.insert(
            tk.END,
            (
                f"{option.name}  —  "
                f"{option.executable}"
            ),
        )


    if options:

        listbox.selection_set(
            0
        )


    button_bar = tk.Frame(
        root
    )


    button_bar.pack(
        fill="x",
        padx=24,
        pady=20,
    )


    def open_selected():

        selection = (
            listbox.curselection()
        )


        if not selection:

            messagebox.showinfo(
                "DUET",
                "Selecione uma IDE.",
            )

            return


        selected[
            "value"
        ] = (
            options[
                selection[0]
            ].executable
        )


        root.destroy()


    def choose_other():

        value = (
            filedialog
            .askopenfilename(
                title=(
                    "Selecione o executável da IDE"
                ),
                filetypes=[
                    (
                        "Executáveis",
                        "*.exe",
                    ),
                    (
                        "Todos os arquivos",
                        "*.*",
                    ),
                ],
            )
        )


        if value:

            selected[
                "value"
            ] = Path(
                value
            )


            root.destroy()


    def open_folder():

        selected[
            "value"
        ] = "folder"


        root.destroy()


    tk.Button(
        button_bar,
        text="Abrir pasta",
        command=open_folder,
        width=12,
    ).pack(
        side="left"
    )


    tk.Button(
        button_bar,
        text="Abrir",
        command=open_selected,
        width=12,
    ).pack(
        side="right",
        padx=(
            8,
            0,
        ),
    )


    tk.Button(
        button_bar,
        text="Outra IDE...",
        command=choose_other,
        width=14,
    ).pack(
        side="right",
        padx=(
            8,
            0,
        ),
    )


    root.mainloop()


    chosen = selected[
        "value"
    ]


    if chosen == "folder":

        os.startfile(
            workspace
        )


    elif isinstance(
        chosen,
        Path,
    ):

        _launch(
            executable=chosen,
            workspace=workspace,
            process_environment=
                process_environment,
        )