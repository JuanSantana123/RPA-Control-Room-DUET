# ============================================================
# DUET CORE - PROJECT PACKAGER
# ============================================================
#
# Responsável por montar um pacote executável de um
# AutomationProject sem alterar o workspace oficial.
#
# Fluxo:
#
# AutomationProject
#       ↓
# copia workspace para staging temporário
#       ↓
# resolve ProjectLibraryDependency
#       ↓
# valida SHA-256 dos snapshots publicados
#       ↓
# injeta as versões exatas das bibliotecas no staging
#       ↓
# gera um ZIP executável
#
# IMPORTANTE:
#
# - O workspace oficial NÃO é alterado.
# - Nenhuma LibraryVersion é alterada.
# - Nenhum Robot é criado aqui.
# - Nenhuma Release é criada aqui.
# - O Agent NÃO precisa conhecer Library/LibraryVersion.
#
# Este módulo será reutilizado futuramente pelo Publish/Release.
# ============================================================

import hashlib
from development.workspace_core import (
    DRAFT_DIRECTORY,
    use_library,
    use_new_library,
)
import os
import shutil
import stat
import tempfile
import zipfile

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    Library,
    LibraryVersion,
    ProjectLibraryDependency,
    ProjectLibraryDraft,
)

from security.artifacts import (
    ArtifactSecurityError,
    normalizar_membro_zip,
    validar_zip,
)
# ============================================================
# DIRETÓRIOS
# ============================================================

# ============================================================
# RAIZ DO CONTROL ROOM
# ============================================================
#
# Este módulo está fisicamente dentro de:
#
#     RPA-Control-Room/packaging/project_packager.py
#
# Portanto:
#
#     Path(__file__).parent
#
# apontaria para "packaging", e não para a raiz do Control Room.
#
# O parent adicional preserva os caminhos históricos de:
#
# - workspaces/
# - storage/libraries/
# - storage/builds/
# - storage/releases/
# ============================================================

BASE_DIRECTORY = Path(
    os.path.abspath(__file__)
).parent.parent


WORKSPACE_REPOSITORY = (
    BASE_DIRECTORY /
    "workspaces"
)

LIBRARIES_REPOSITORY = (
    BASE_DIRECTORY /
    "storage" /
    "libraries"
)

BUILD_REPOSITORY = (
    BASE_DIRECTORY /
    "storage" /
    "builds"
)

BUILD_TEMP_REPOSITORY = (
    BUILD_REPOSITORY /
    ".tmp"
)

BUILD_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True
)

BUILD_TEMP_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# ITENS LOCAIS QUE NÃO DEVEM IR PARA O PACOTE
# ============================================================
#
# São artefatos de desenvolvimento/ambiente local e não fazem
# parte do código executável da automação.
# ============================================================

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

IGNORED_FILES = {
    ".DS_Store",
}


# ============================================================
# RESULTADO DO BUILD
# ============================================================

@dataclass
class ProjectBuildResult:
    """
    Metadados retornados depois da geração do pacote.
    """

    project_id: int
    project_name: str
    package_path: Path
    package_hash: str
    dependencies: list[dict]


# ============================================================
# HASH
# ============================================================

def calcular_sha256(
    file_path: Path
) -> str:
    """
    Calcula o SHA-256 de um arquivo sem carregá-lo inteiro
    na memória.
    """

    digest = hashlib.sha256()

    with file_path.open(
        "rb"
    ) as arquivo:

        while True:

            bloco = arquivo.read(
                1024 * 1024
            )

            if not bloco:
                break

            digest.update(
                bloco
            )

    return digest.hexdigest()


# ============================================================
# COPIAR WORKSPACE
# ============================================================

def copiar_workspace_para_staging(
    workspace_path: Path,
    staging_path: Path
) -> None:
    """
    Copia o workspace oficial para a área temporária do build.

    O workspace permanece intacto.

    Arquivos/pastas locais de ambiente são ignorados para não
    empacotar venv, cache de Python ou metadados Git.
    """

    if not workspace_path.is_dir():

        raise RuntimeError(
            f"Workspace não encontrado: {workspace_path}"
        )

    main_py = (
        workspace_path /
        "main.py"
    )

    if not main_py.is_file():

        raise RuntimeError(
            "O workspace não possui main.py na raiz."
        )

    for root, dirs, files in os.walk(
        workspace_path
    ):

        root_path = Path(
            root
        )

        # Rejeita links antes de copiar qualquer conteúdo do workspace.
        if any((root_path / name).is_symlink() for name in dirs + files):
            raise RuntimeError("Links simbólicos não são permitidos no workspace.")

        # Remove diretórios ignorados da própria caminhada.
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in IGNORED_DIRECTORIES
            and not (root_path == workspace_path and directory == DRAFT_DIRECTORY)
        ]

        relative_root = (
            root_path.relative_to(
                workspace_path
            )
        )

        destination_root = (
            staging_path /
            relative_root
        )

        destination_root.mkdir(
            parents=True,
            exist_ok=True
        )

        for filename in files:

            if filename in IGNORED_FILES or filename.endswith((".pyc", ".pyo")):
                continue

            source_file = (
                root_path /
                filename
            )

            destination_file = (
                destination_root /
                filename
            )

            shutil.copy2(
                source_file,
                destination_file
            )


# ============================================================
# RESOLVER ARTEFATO DA BIBLIOTECA
# ============================================================

def resolver_artifact_path(
    version: LibraryVersion
) -> Path:
    """
    Resolve o caminho físico armazenado na LibraryVersion.

    artifact_path é persistido de forma relativa ao diretório
    do Control Room.
    """

    artifact_path = (
        BASE_DIRECTORY /
        version.artifact_path
    ).resolve()

    repository_root = (
        LIBRARIES_REPOSITORY
        .resolve()
    )

    # Defesa adicional:
    # o caminho persistido no banco precisa continuar dentro
    # do repository oficial de bibliotecas.
    if (
        artifact_path != repository_root and
        repository_root not in artifact_path.parents
    ):

        raise RuntimeError(
            "LibraryVersion possui artifact_path fora do "
            "repositório oficial de bibliotecas."
        )

    if not artifact_path.is_file():

        raise RuntimeError(
            "Artefato físico da biblioteca não encontrado: "
            f"{artifact_path}"
        )

    return artifact_path


# ============================================================
# EXTRAÇÃO SEGURA DE UMA LIBRARYVERSION
# ============================================================
def extrair_biblioteca_no_staging(
    artifact_path: Path,
    staging_path: Path,
    import_name: str,
) -> None:
    """
    Extrai uma LibraryVersion publicada no staging do Robot.

    A segurança estrutural do ZIP é validada pelo módulo comum.

    Esta função mantém as responsabilidades específicas do
    Packager:

    - garantir o namespace correto;
    - impedir colisão com conteúdo já existente no staging;
    - extrair manualmente, sem extractall().
    """

    package_root = (
        staging_path
        / import_name
    )

    if package_root.exists():

        raise RuntimeError(
            "Conflito ao montar pacote: já existe um item "
            f'"{import_name}" na raiz do workspace/build.'
        )

    try:

        validar_zip(
            artifact_path,
            max_zip_size=None,
        )

        with zipfile.ZipFile(
            artifact_path,
            "r",
        ) as arquivo_zip:

            members = (
                arquivo_zip.infolist()
            )

            if not members:

                raise RuntimeError(
                    f"Library {import_name}: ZIP vazio."
                )

            # =================================================
            # 1. REGRA DE NAMESPACE
            # =================================================

            for member in members:

                member_path = (
                    normalizar_membro_zip(
                        member.filename
                    )
                )

                if (
                    member_path.parts[0]
                    != import_name
                ):

                    raise RuntimeError(
                        f"Library {import_name}: o ZIP possui "
                        "conteúdo fora do namespace esperado."
                    )

            # =================================================
            # 2. EXTRAÇÃO MANUAL
            # =================================================

            for member in members:

                member_path = (
                    normalizar_membro_zip(
                        member.filename
                    )
                )

                destination = (
                    staging_path
                    / Path(
                        *member_path.parts
                    )
                )

                # Defesa adicional: mesmo depois da validação
                # lógica do ZIP, o destino físico precisa continuar
                # dentro do staging.
                staging_resolvido = (
                    staging_path.resolve()
                )

                destino_resolvido = (
                    destination.resolve()
                )

                try:

                    destino_resolvido.relative_to(
                        staging_resolvido
                    )

                except ValueError as error:

                    raise RuntimeError(
                        f"Library {import_name}: destino "
                        "fora do staging."
                    ) from error

                if member.is_dir():

                    # Um arquivo já existente nunca pode ser
                    # convertido silenciosamente em diretório.
                    if (
                        destination.exists()
                        and not destination.is_dir()
                    ):

                        raise RuntimeError(
                            "Conflito ao montar pacote: "
                            f"{destination.relative_to(staging_path)}"
                        )

                    destination.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    continue

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                # Nunca sobrescreve Robot ou outra Library.
                if destination.exists():

                    raise RuntimeError(
                        "Conflito de arquivo ao montar pacote: "
                        f"{destination.relative_to(staging_path)}"
                    )

                with arquivo_zip.open(
                    member,
                    "r",
                ) as source_file:

                    # "xb" adiciona outra defesa contra
                    # sobrescrita acidental.
                    with destination.open(
                        "xb",
                    ) as destination_file:

                        shutil.copyfileobj(
                            source_file,
                            destination_file,
                        )

    except ArtifactSecurityError as error:

        raise RuntimeError(
            f"Library {import_name}: {error}"
        ) from error

    except zipfile.BadZipFile as error:

        raise RuntimeError(
            f"Library {import_name}: artefato ZIP inválido."
        ) from error
# ============================================================
# CARREGAR DEPENDÊNCIAS DO PROJETO
# ============================================================

def carregar_dependencias_projeto(
    db: Session,
    project_id: int
) -> list[tuple[
    ProjectLibraryDependency,
    Library,
    LibraryVersion
]]:
    """
    Resolve todas as dependências do projeto no banco.

    Cada vínculo precisa ser internamente consistente:
    - dependency.library_id == Library.id
    - dependency.library_version_id == LibraryVersion.id
    - LibraryVersion.library_id == Library.id
    """

    dependencies = (
        db.query(
            ProjectLibraryDependency,
            Library,
            LibraryVersion
        )
        .join(
            Library,
            Library.id ==
                ProjectLibraryDependency.library_id
        )
        .join(
            LibraryVersion,
            LibraryVersion.id ==
                ProjectLibraryDependency.library_version_id
        )
        .filter(
            ProjectLibraryDependency.project_id ==
                project_id
        )
        .order_by(
            Library.import_name.asc(),
            ProjectLibraryDependency.id.asc()
        )
        .all()
    )

    for dependency, library, version in dependencies:

        if version.library_id != library.id:

            raise RuntimeError(
                "Dependência inconsistente no banco: "
                f"LibraryVersion {version.id} não pertence "
                f"à Library {library.id}."
            )

    return dependencies


# ============================================================
# CARREGAR BIBLIOTECAS NOVAS DO PROJETO
# ============================================================

def carregar_bibliotecas_novas_projeto(
    db: Session,
    project_id: int
) -> list[tuple[
    ProjectLibraryDraft,
    Library
]]:
    """Resolve Libraries novas que ainda não possuem versão publicada.

    Uma biblioteca criada dentro do Desenvolvimento já possui identidade
    em ``libraries`` e um ProjectLibraryDraft, mas ainda NÃO possui
    ProjectLibraryDependency porque não existe LibraryVersion para fixar.

    Essas bibliotecas precisam participar de testes e execuções do projeto
    antes da primeira publicação.
    """

    drafts = (
        db.query(
            ProjectLibraryDraft,
            Library
        )
        .join(
            Library,
            Library.id ==
                ProjectLibraryDraft.library_id
        )
        .outerjoin(
            ProjectLibraryDependency,
            (
                ProjectLibraryDependency.project_id ==
                    ProjectLibraryDraft.project_id
            ) &
            (
                ProjectLibraryDependency.library_id ==
                    ProjectLibraryDraft.library_id
            )
        )
        .filter(
            ProjectLibraryDraft.project_id ==
                project_id,
            ProjectLibraryDraft.base_library_version_id.is_(None),
            ProjectLibraryDependency.id.is_(None)
        )
        .order_by(
            Library.import_name.asc(),
            ProjectLibraryDraft.id.asc()
        )
        .all()
    )

    for draft, library in drafts:

        # Library nova permanece fora do catálogo de Produção até
        # o primeiro Release. Se já houver versão de Produção, o
        # estado do banco está inconsistente e o build é interrompido.
        if library.production_version_id is not None:
            raise RuntimeError(
                f"Biblioteca {library.name} está marcada como nova, "
                "mas já possui versão de Produção."
            )

    return drafts


# ============================================================
# GERAR ZIP FINAL
# ============================================================

def gerar_zip_staging(
    staging_path: Path,
    output_path: Path
) -> str:
    """
    Compacta todo o staging em um ZIP e retorna o SHA-256
    do pacote final.

    O arquivo é criado primeiro como .tmp e só substitui o
    destino final depois de concluído com sucesso.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_output = (
        output_path.parent /
        f".{output_path.name}.tmp"
    )

    if temp_output.exists():

        temp_output.unlink()

    try:

        with zipfile.ZipFile(
            temp_output,
            "w",
            compression=zipfile.ZIP_DEFLATED
        ) as zip_file:

            for item in sorted(
                staging_path.rglob("*"),
                key=lambda path: path.as_posix().lower()
            ):

                if not item.is_file():
                    continue

                arcname = (
                    item.relative_to(
                        staging_path
                    )
                    .as_posix()
                )

                zip_file.write(
                    item,
                    arcname
                )

        package_hash = calcular_sha256(
            temp_output
        )

        os.replace(
            temp_output,
            output_path
        )

        return package_hash

    finally:

        if temp_output.exists():

            try:
                temp_output.unlink()
            except Exception:
                pass


# ============================================================
# BUILD PRINCIPAL
# ============================================================

def build_project_package(
    db: Session,
    project_id: int,
    output_path: Path
) -> ProjectBuildResult:
    """
    Monta um ZIP executável a partir de um AutomationProject.

    Este build ainda NÃO cria Robot nem Release.

    Ele apenas produz o artefato que futuramente será consumido
    pelo processo de publicação.
    """

    project = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id ==
                project_id,
            AutomationProject.is_active == 1
        )
        .with_for_update()
        .first()
    )

    if not project:

        raise RuntimeError(
            "AutomationProject ativo não encontrado."
        )

    workspace_path = (
        WORKSPACE_REPOSITORY /
        str(
            project.id
        )
    )

    dependencies = carregar_dependencias_projeto(
        db,
        project.id
    )

    # Bibliotecas novas ainda não possuem LibraryVersion e, portanto,
    # não aparecem em ProjectLibraryDependency. Mesmo assim precisam
    # participar do pacote de teste/execução do Desenvolvimento.
    new_library_drafts = carregar_bibliotecas_novas_projeto(
        db,
        project.id
    )

    staging_path = Path(
        tempfile.mkdtemp(
            prefix=f"project_{project.id}_",
            dir=BUILD_TEMP_REPOSITORY
        )
    )

    dependency_metadata = []

    try:
        draft_root = workspace_path / DRAFT_DIRECTORY

        if draft_root.exists():
            expected = {
                library.import_name
                for _, library, _ in dependencies
            } | {
                library.import_name
                for _, library in new_library_drafts
            }

            if any(
                item.name not in expected
                for item in draft_root.iterdir()
            ):
                raise RuntimeError(
                    "Existe código em _libraries sem dependência "
                    "ou draft cadastrado."
                )


        # ----------------------------------------------------
        # 1. WORKSPACE
        # ----------------------------------------------------

        copiar_workspace_para_staging(
            workspace_path,
            staging_path
        )

        # ----------------------------------------------------
        # 2. BIBLIOTECAS FIXADAS
        # ----------------------------------------------------

        for dependency, library, version in dependencies:

            # Testes e Release usam a cópia editável quando presente.
            # A versão no banco só muda durante a publicação.
            draft_metadata = use_library(
                db, project.id, library, version, staging_path
            )

            dependency_metadata.append({
                **draft_metadata,
                "is_new": False,
                "draft_id": None,
                "dependency_id": dependency.id,
                "library_id": library.id,
                "library_name": library.name,
                "import_name": library.import_name,
                "library_version_id": version.id,
                "version": version.version,
                "file_hash": version.file_hash,
                "source_type": version.source_type,
                "source_robot_id": version.source_robot_id,
                "source_robot_version":
                    version.source_robot_version,
            })

        # ----------------------------------------------------
        # 3. BIBLIOTECAS NOVAS AINDA NÃO PUBLICADAS
        # ----------------------------------------------------

        for draft, library in new_library_drafts:

            draft_metadata = use_new_library(
                project.id,
                library,
                draft,
                staging_path
            )

            dependency_metadata.append({
                **draft_metadata,
                "draft_id": draft.id,
                "dependency_id": None,
                "library_id": library.id,
                "library_name": library.name,
                "import_name": library.import_name,
                "library_version_id": None,
                "version": None,
                "file_hash": None,
                "source_type": "draft",
                "source_robot_id": None,
                "source_robot_version": None,
            })

        # ----------------------------------------------------
        # 4. ZIP FINAL
        # ----------------------------------------------------

        package_hash = gerar_zip_staging(
            staging_path,
            output_path
        )

        return ProjectBuildResult(
            project_id=project.id,
            project_name=project.name,
            package_path=output_path,
            package_hash=package_hash,
            dependencies=dependency_metadata
        )

    finally:

        shutil.rmtree(
            staging_path,
            ignore_errors=True
        )
