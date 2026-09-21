"""Cópias editáveis de Bibliotecas, isoladas por AutomationProject.

Dependências: SQLAlchemy, modelos locais e project_packager (importado
somente dentro das funções para evitar dependência circular).
A pasta _libraries aparece no Studio; no ZIP os namespaces ficam na raiz.
"""
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import HTTPException

DRAFT_DIRECTORY = "_libraries"


def tree_hash(root: Path) -> str:
    """Compara nomes e bytes; datas e caches não criam versões artificiais."""
    from packaging.project_packager import IGNORED_DIRECTORIES, IGNORED_FILES

    entries = []

    if not root.is_dir() or root.is_symlink():
        raise RuntimeError(
            f"Pasta de biblioteca inválida: {root.name}"
        )

    for current, dirs, files in os.walk(root):
        current = Path(current)

        for name in dirs + files:
            if (current / name).is_symlink():
                raise RuntimeError(
                    "Links simbólicos não são permitidos no pacote."
                )

        dirs[:] = [
            name
            for name in dirs
            if name not in IGNORED_DIRECTORIES
        ]

        for name in sorted(files):
            if (
                name in IGNORED_FILES
                or name.endswith((".pyc", ".pyo"))
            ):
                continue

            item = current / name

            entries.append(
                (
                    item.relative_to(root).as_posix(),
                    hashlib.sha256(
                        item.read_bytes()
                    ).hexdigest(),
                )
            )

    return hashlib.sha256(
        json.dumps(
            sorted(entries),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


def extract_base(
    library,
    version,
    destination: Path,
) -> Path:
    """Extrai e verifica a versão publicada; nunca altera seu artefato."""
    from packaging.project_packager import (
        resolver_artifact_path,
        calcular_sha256,
        extrair_biblioteca_no_staging,
    )

    artifact = resolver_artifact_path(version)

    if calcular_sha256(artifact) != version.file_hash:
        raise RuntimeError(
            f"Integridade inválida: {library.name} {version.version}."
        )

    extrair_biblioteca_no_staging(
        artifact,
        destination,
        library.import_name,
    )

    return destination / library.import_name


def draft_path(
    project_id: int,
    import_name: str,
) -> Path:
    """Local editável da Library dentro do workspace do projeto."""
    from packaging.project_packager import WORKSPACE_REPOSITORY

    if (
        not import_name.isidentifier()
        or import_name == DRAFT_DIRECTORY
    ):
        raise RuntimeError(
            "Namespace de Biblioteca inválido ou reservado."
        )

    return (
        WORKSPACE_REPOSITORY
        / str(project_id)
        / DRAFT_DIRECTORY
        / import_name
    )


def draft_workspace_value(
    project_id: int,
    import_name: str,
) -> str:
    """Retorna o caminho interno persistido no ProjectLibraryDraft.

    O valor é relativo à raiz do Control Room para não gravar no banco
    uma letra de unidade ou caminho absoluto específico de uma máquina.
    """
    from packaging.project_packager import BASE_DIRECTORY

    return (
        draft_path(project_id, import_name)
        .relative_to(BASE_DIRECTORY)
        .as_posix()
    )



def draft_has_changes(
    project_id: int,
    library,
    version,
) -> bool:
    """
    Compara a Working Copy de uma Library com a versão-base publicada.

    Não depende de ProjectLibraryDraft.is_modified.

    Isso permite detectar corretamente os dois sentidos:

        versão base
            -> arquivo alterado
            -> True

        versão base
            -> arquivo alterado
            -> arquivo restaurado ao conteúdo original
            -> False

    A comparação utiliza tree_hash(), portanto considera caminhos
    e bytes reais dos arquivos e ignora caches/arquivos técnicos
    conforme as mesmas regras utilizadas pelo Release.
    """

    from packaging.project_packager import BUILD_TEMP_REPOSITORY

    # Caminho oficial da Working Copy desta Library:
    #
    # workspaces/<project_id>/_libraries/<import_name>
    draft = draft_path(
        project_id,
        library.import_name,
    )

    # Se a Working Copy ainda não foi materializada, o projeto
    # continua efetivamente utilizando a versão-base sem alterações.
    if not draft.exists():
        return False

    # O namespace precisa continuar sendo uma pasta Python válida.
    if not draft.is_dir() or draft.is_symlink():
        raise RuntimeError(
            f"Working Copy inválida para a biblioteca {library.name}."
        )

    # Extrai a versão publicada para um diretório temporário.
    #
    # O artefato original nunca é alterado.
    with tempfile.TemporaryDirectory(
        dir=BUILD_TEMP_REPOSITORY
    ) as tmp:

        base = extract_base(
            library,
            version,
            Path(tmp),
        )

        # Alteração real = conteúdo atual diferente da versão-base.
        return (
            tree_hash(draft)
            != tree_hash(base)
        )

    
def ensure_drafts(
    db,
    project_id: int,
) -> None:
    """Materializa Bibliotecas ausentes sem sobrescrever alterações existentes.

    Chamado com o projeto bloqueado para atualização pela API de workspace.
    O vínculo no banco continua apontando à versão base até o Release.
    """
    from packaging.project_packager import (
        carregar_dependencias_projeto,
        BUILD_TEMP_REPOSITORY,
    )

    for _, library, version in carregar_dependencias_projeto(
        db,
        project_id,
    ):
        target = draft_path(
            project_id,
            library.import_name,
        )

        # Uma Library recém-publicada a partir do Robô já pode ter código
        # na raiz. Mantém esse código e não cria uma segunda cópia.
        if (
            target.exists()
            or (
                target.parent.parent
                / library.import_name
            ).exists()
        ):
            continue

        with tempfile.TemporaryDirectory(
            dir=BUILD_TEMP_REPOSITORY
        ) as tmp:
            source = extract_base(
                library,
                version,
                Path(tmp),
            )

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            os.replace(
                source,
                target,
            )


def use_library(
    db,
    project_id: int,
    library,
    version,
    staging: Path,
) -> dict:
    """Inclui a cópia editada, se houver; caso contrário usa a versão base.

    Retorna hashes de conteúdo para a prévia detectar alterações reais.
    """
    from packaging.project_packager import (
        BUILD_TEMP_REPOSITORY,
        IGNORED_DIRECTORIES,
        IGNORED_FILES,
    )

    target = staging / library.import_name

    if (
        staging
        / (library.import_name + ".py")
    ).exists():
        raise RuntimeError(
            f"Namespace duplicado no projeto: {library.import_name}."
        )

    with tempfile.TemporaryDirectory(
        dir=BUILD_TEMP_REPOSITORY
    ) as tmp:
        base = extract_base(
            library,
            version,
            Path(tmp),
        )

        base_hash = tree_hash(base)
        draft = draft_path(
            project_id,
            library.import_name,
        )

        if draft.exists() and target.exists():
            raise RuntimeError(
                f"Há duas cópias da Biblioteca {library.import_name}; "
                "mantenha somente uma."
            )

        source = (
            draft
            if draft.exists()
            else (
                target
                if target.exists()
                else base
            )
        )

        content_hash = tree_hash(source)

        if not (
            source / "__init__.py"
        ).is_file():
            raise RuntimeError(
                f"Biblioteca {library.name} precisa de __init__.py."
            )

        if source != target:
            shutil.copytree(
                source,
                target,
                ignore=shutil.ignore_patterns(
                    *IGNORED_DIRECTORIES,
                    *IGNORED_FILES,
                    "*.pyc",
                    "*.pyo",
                ),
            )

    return {
        "modified": content_hash != base_hash,
        "content_hash": content_hash,
    }


def use_new_library(
    project_id: int,
    library,
    draft,
    staging: Path,
) -> dict:
    """Inclui no build uma Library nova ainda sem LibraryVersion.

    A biblioteca já possui identidade no banco, porém ainda está inativa
    no catálogo de Produção e possui base_library_version_id = NULL.
    Durante testes/execuções o código do draft é copiado para a raiz do
    staging exatamente como ficará depois da primeira publicação.
    """
    from packaging.project_packager import (
        IGNORED_DIRECTORIES,
        IGNORED_FILES,
    )

    if draft.base_library_version_id is not None:
        raise RuntimeError(
            "Draft informado como novo possui uma versão base."
        )

    source = draft_path(
        project_id,
        library.import_name,
    )

    target = staging / library.import_name

    if not source.is_dir():
        raise RuntimeError(
            f"Draft da Biblioteca {library.name} não foi encontrado."
        )

    if (
        target.exists()
        or (
            staging
            / (library.import_name + ".py")
        ).exists()
    ):
        raise RuntimeError(
            f"Namespace duplicado no projeto: {library.import_name}."
        )

    if not (
        source / "__init__.py"
    ).is_file():
        raise RuntimeError(
            f"Biblioteca {library.name} precisa de __init__.py."
        )

    content_hash = tree_hash(source)

    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            *IGNORED_DIRECTORIES,
            *IGNORED_FILES,
            "*.pyc",
            "*.pyo",
        ),
    )

    return {
        # Uma biblioteca nova precisa obrigatoriamente gerar sua
        # primeira LibraryVersion no Release.
        "modified": True,
        "content_hash": content_hash,
        "is_new": True,
    }


def commit_dependency_change(
    db,
    project_id,
    library,
    old_version=None,
):
    """Confirma troca/remoção de vínculo sem perder código editado.

    Uma cópia limpa é retirada para ser rematerializada na próxima abertura.
    Uma cópia modificada bloqueia a operação; deve ser publicada ou o usuário
    deve restaurar seus arquivos à versão base antes de trocar a dependência.
    Em falha do banco, restaura a cópia original.
    """
    from packaging.project_packager import BUILD_TEMP_REPOSITORY

    target = draft_path(
        project_id,
        library.import_name,
    )

    root_copy = (
        target.parent.parent
        / library.import_name
    )

    if (
        not target.exists()
        and root_copy.exists()
    ):
        target = root_copy

    with tempfile.TemporaryDirectory(
        dir=BUILD_TEMP_REPOSITORY
    ) as tmp:
        backup = Path(tmp) / "backup"

        if target.exists():
            if old_version is None:
                raise HTTPException(
                    409,
                    "Já existe uma cópia local com esse namespace.",
                )

            base_dir = Path(tmp) / "base"
            base_dir.mkdir()

            base = extract_base(
                library,
                old_version,
                base_dir,
            )

            if tree_hash(target) != tree_hash(base):
                raise HTTPException(
                    409,
                    "A Biblioteca possui alterações locais. "
                    "Publique-as ou restaure os arquivos antes "
                    "de trocar/remover a dependência.",
                )

            os.replace(
                target,
                backup,
            )

        try:
            db.commit()

        except Exception:
            db.rollback()

            if backup.exists():
                target.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                os.replace(
                    backup,
                    target,
                )

            raise


def protect_draft_root(
    path: str,
    db=None,
    project_id=None,
) -> None:
    """Evita renomear/apagar o contêiner ou namespace de uma dependência.

    Arquivos e subpastas internos continuam editáveis pelo Studio.
    """
    parts = Path(
        path.replace("\\", "/")
    ).parts

    own_namespace = False

    if (
        db is not None
        and project_id is not None
        and len(parts) == 1
    ):
        from packaging.project_packager import carregar_dependencias_projeto

        own_namespace = (
            parts[0]
            in {
                lib.import_name
                for _, lib, _
                in carregar_dependencias_projeto(
                    db,
                    project_id,
                )
            }
        )

    if (
        own_namespace
        or (
            parts
            and parts[0] == DRAFT_DIRECTORY
            and len(parts) <= 2
        )
    ):
        raise HTTPException(
            409,
            "Use a gestão de dependências para remover a Biblioteca; "
            "edite seus arquivos internos no Studio.",
        )


def protect_draft_container_creation(
    path: str,
) -> None:
    """Bloqueia criação manual de namespaces dentro de _libraries.

    O usuário pode criar arquivos e subpastas DENTRO de uma biblioteca,
    porém o namespace principal precisa nascer pela ação "Nova biblioteca".
    Isso impede código órfão que o Packager não consegue associar a uma
    Library/ProjectLibraryDraft do banco.
    """
    parts = Path(
        path.replace("\\", "/")
    ).parts

    if (
        parts
        and parts[0] == DRAFT_DIRECTORY
        and len(parts) <= 2
    ):
        raise HTTPException(
            409,
            "Crie o namespace pela ação 'Nova biblioteca'. "
            "Dentro de uma biblioteca já criada, arquivos e subpastas "
            "continuam liberados normalmente.",
        )
