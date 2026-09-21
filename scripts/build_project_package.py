# ============================================================
# DUET CORE - BUILD DE TESTE DE AUTOMATIONPROJECT
# ============================================================
#
# Script temporário de validação do Project Packager.
#
# Ele NÃO publica Robot e NÃO cria Release.
#
# Uso:
#
#     python build_project_package.py 10
#
# Resultado:
#
#     storage/builds/previews/project_10.zip
#
# Depois que o mecanismo for validado, o mesmo packager será
# chamado pelo fluxo real de Release/Publish.
# ============================================================

import sys

from pathlib import Path

from database import SessionLocal
from packaging.project_packager import (
    BASE_DIRECTORY,
    build_project_package,
)


def main() -> None:
    """
    Gera um pacote de preview para um AutomationProject.
    """

    if len(sys.argv) != 2:

        print(
            "Uso: python build_project_package.py <project_id>"
        )

        raise SystemExit(
            1
        )

    try:

        project_id = int(
            sys.argv[1]
        )

    except ValueError:

        print(
            "project_id precisa ser um número inteiro."
        )

        raise SystemExit(
            1
        )

    output_path = (
        BASE_DIRECTORY /
        "storage" /
        "builds" /
        "previews" /
        f"project_{project_id}.zip"
    )

    db = SessionLocal()

    try:

        print()
        print("=" * 60)
        print("DUET CORE - PROJECT PACKAGE BUILD")
        print("=" * 60)
        print(f"Project ID : {project_id}")
        print()

        result = build_project_package(
            db=db,
            project_id=project_id,
            output_path=output_path
        )

        print("Build concluído com sucesso.")
        print()
        print(f"Projeto      : {result.project_name}")
        print(f"Pacote       : {result.package_path}")
        print(f"SHA-256      : {result.package_hash}")
        print(
            f"Bibliotecas  : {len(result.dependencies)}"
        )

        for dependency in result.dependencies:

            print(
                "  - "
                f"{dependency['library_name']} "
                f"{dependency['version']} "
                f"({dependency['import_name']})"
            )

        print("=" * 60)
        print()

    except Exception as error:

        print()
        print("=" * 60)
        print("BUILD FALHOU")
        print("=" * 60)
        print(str(error))
        print("=" * 60)
        print()

        raise SystemExit(
            1
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()
