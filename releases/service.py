"""Release de AutomationProjects sem mudar o contrato de Robot/Scheduler.

Os pacotes são imutáveis por ID/versão. Robot.file_path aponta ao pacote
atual. O manifesto dentro do ZIP preserva dependências e autoria.
Este módulo não executa robôs e não altera agendamentos.
"""
import hashlib
import json
import re
import shutil
import stat
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from models import (
    Robot,
    RobotFolder,
    RobotVersion,  # Histórico imutável de cada versão publicada do Robot.
    Library,    
    LibraryVersion,
    ProjectLibraryDependency,
    ProjectLibraryDraft,
    RobotVersionLibraryDependency,
)
# Módulo responsável pela construção dos pacotes executáveis
# utilizados durante o processo de publicação de Releases.
from packaging import project_packager as packager
from security.artifacts import (
    ArtifactSecurityError,
    normalizar_membro_zip,
    validar_zip,
)
MANIFEST = "duet-release.json"


class NewReleaseLibrary(BaseModel):
    """Publica um pacote Python próprio do Robô como nova Library.

    O namespace deve ser uma pasta na raiz do projeto com __init__.py.
    Nenhum arquivo é movido no workspace durante a publicação.
    """
    import_name: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(default="1.0.0", max_length=255)


class ReleaseRequest(BaseModel):
    """Dados confirmados na prévia; as versões de Library são explícitas."""
    confirmation_name: str = Field(..., min_length=1, max_length=255)
    preview_token: str = Field(..., min_length=64, max_length=64)
    folder_id: int | None = None
    # Caminho relativo ao destino escolhido, por exemplo Financeiro/Pagamentos.
    new_folder_path: str = Field(default="", max_length=1000)
    robot_name: str | None = Field(default=None, max_length=255)
    library_versions: dict[int, str] = Field(default_factory=dict)
    new_libraries: list[NewReleaseLibrary] = Field(default_factory=list)


def safe_name(name: str) -> str:
    """Valida nomes de arquivo/pasta compatíveis com os Agents Windows."""
    value = name.strip()
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f'{p}{i}' for p in ('COM','LPT') for i in range(1,10)}
    if (not value or value in {'.','..'} or len(value) > 255
            or any(c in '<>:"/\\|?*' or ord(c) < 32 for c in value)
            or value.endswith(('.', ' ')) or value.split('.')[0].upper() in reserved):
        raise HTTPException(400, "Nome de arquivo ou pasta inválido.")
    return value


def read_package(
    path: Path,
) -> dict[str, bytes]:
    """
    Lê um pacote ZIP de Release.

    Mantém o limite histórico de 1 GB descompactado, mas utiliza
    a política central de segurança para caminhos, symlinks,
    colisões Windows, ZIP bomb e integridade.
    """

    try:

        # Releases historicamente aceitam até 1 GB
        # descompactado. Não reduzimos esse contrato para o
        # limite padrão de 500 MB usado por outros artefatos.
        validar_zip(
            path,
            max_zip_size=None,
            max_uncompressed_size=(
                1024 * 1024 * 1024
            ),
        )

        result = {}

        with zipfile.ZipFile(
            path,
            "r",
        ) as archive:

            for item in archive.infolist():

                if item.is_dir():
                    continue

                parts = (
                    normalizar_membro_zip(
                        item.filename
                    )
                )

                name = (
                    parts.as_posix()
                )

                result[name] = (
                    archive.read(
                        item
                    )
                )

        return result

    except ArtifactSecurityError as error:

        mensagem = str(error)

        if (
            "tamanho máximo descompactado"
            in mensagem
        ):

            raise HTTPException(
                status_code=413,
                detail=(
                    "Pacote descompactado ultrapassa 1 GB."
                ),
            ) from error

        raise HTTPException(
            status_code=409,
            detail=mensagem,
        ) from error

    except zipfile.BadZipFile as error:

        raise HTTPException(
            status_code=409,
            detail="Pacote ZIP inválido.",
        ) from error

def write_package(path: Path, contents: dict[str, bytes]) -> str:
    """Cria um ZIP determinístico e exclusivo; nunca sobrescreve versão."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return packager.calcular_sha256(path)


def robot_path(robot) -> Path:
    """
    Resolve o file_path legado/current pointer do Robot.

    Esta função permanece temporariamente porque ainda existem
    fluxos antigos que consultam diretamente o Robot atual.
    """

    path = Path(
        robot.file_path
    )

    return (
        path
        if path.is_absolute()
        else packager.BASE_DIRECTORY / path
    )


def robot_version_path(
    robot_version: RobotVersion
) -> Path:
    """
    Resolve o artefato imutável pertencente a uma RobotVersion.

    RobotVersion.artifact_path normalmente é armazenado relativo
    à raiz do Control Room:

        storage/releases/{robot_id}/{version}/.../robot.zip

    Também suportamos caminho absoluto para compatibilidade com
    possíveis registros legados.
    """

    path = Path(
        robot_version.artifact_path
    )

    return (
        path
        if path.is_absolute()
        else packager.BASE_DIRECTORY / path
    )


def resolve_robot_version(
    db,
    robot_id: int,
    version: int
) -> tuple[RobotVersion, Path]:
    """
    Localiza e valida uma versão publicada imutável do Robot.

    A RobotVersion passa a ser a fonte oficial para recuperar
    uma versão publicada no Studio.

    Valida:

    - existência da RobotVersion no banco;
    - existência física do ZIP;
    - SHA-256 do artefato.
    """

    robot_version = (
        db.query(RobotVersion)
        .filter(
            RobotVersion.robot_id == robot_id,
            RobotVersion.version == version
        )
        .first()
    )


    if not robot_version:

        raise HTTPException(
            409,
            (
                f"O Robô não possui RobotVersion registrada "
                f"para a versão {version}."
            )
        )


    path = robot_version_path(
        robot_version
    )


    if not path.is_file():

        raise HTTPException(
            409,
            (
                f"O artefato da versão {version} do Robô "
                "está ausente em Produção."
            )
        )


    actual_hash = (
        packager.calcular_sha256(
            path
        )
    )


    if actual_hash != robot_version.file_hash:

        raise HTTPException(
            409,
            (
                f"O artefato da versão {version} do Robô "
                "falhou na validação de integridade."
            )
        )


    return (
        robot_version,
        path
    )


def collect_snapshot(db, project):
    """Usa o mesmo empacotador dos testes; não publica nenhuma versão."""
    with tempfile.TemporaryDirectory(dir=packager.BUILD_TEMP_REPOSITORY) as tmp:
        result = packager.build_project_package(db, project.id, Path(tmp) / 'snapshot.zip')
        contents = read_package(result.package_path)
    if MANIFEST in contents:
        raise HTTPException(409, f"{MANIFEST} é reservado ao Release; remova esse arquivo do workspace.")
    return result.dependencies, contents


def resolve_existing(db, project):
    """Projeto vinculado atualiza obrigatoriamente o mesmo Robot em PRD."""
    if project.base_robot_id is None:
        return None
    robot = db.query(Robot).filter(Robot.id == project.base_robot_id).with_for_update().first()
    if not robot:
        raise HTTPException(409, "O Robô de origem não existe mais; resolva o vínculo antes de publicar.")
    if project.base_version != robot.version:
        raise HTTPException(409, "O Robô recebeu outra versão em PRD. Abra um projeto a partir da versão atual e incorpore suas alterações.")
    return robot


def snapshot_token(project, robot, dependencies, contents):
    """Liga a confirmação aos bytes, dependências e versão atual de PRD."""
    data = {'project': project.id, 'name': project.name,
            'stage': project.current_stage_id,
            'robot': [robot.id, robot.version, robot.file_hash, robot.folder_id] if robot else None,
            'dependencies': dependencies,
            'files': [(n, hashlib.sha256(b).hexdigest()) for n,b in sorted(contents.items())]}
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def next_library_version(db, library_id: int) -> str:
    """Retorna a próxima versão MAJOR oficial da biblioteca.

    Regra atual do DUET:
        1.x.x -> 2.0.0
        2.x.x -> 3.0.0

    Uma biblioteca sem nenhuma versão publicada começa em 1.0.0.
    """

    versions = [
        value[0]
        for value in (
            db.query(LibraryVersion.version)
            .filter(
                LibraryVersion.library_id == library_id
            )
            .all()
        )
    ]

    majors = [
        int(value.split('.')[0])
        for value in versions
        if re.match(r'^\d+\.', value)
    ]

    return f'{max(majors, default=0) + 1}.0.0'


def preview_release(db, project):
    """Prévia somente leitura: mostra destino, versão e Bibliotecas alteradas."""
    robot = resolve_existing(db, project)
    dependencies, contents = collect_snapshot(db, project)
    for dependency in dependencies:
        dependency['suggested_version'] = next_library_version(
            db,
            dependency['library_id']
        )

        library = db.get(
            Library,
            dependency['library_id']
        )

        dependency['production_version_id'] = (
            library.production_version_id
            if library
            else None
        )
    # A sugestão não participa do token: é escolha explícita na confirmação.
    token_dependencies = [{k:v for k,v in d.items() if k not in {'suggested_version', 'production_version_id'}} for d in dependencies]
    folders = db.query(RobotFolder).order_by(RobotFolder.name).all()
    return {'status':'success', 'project_id':project.id,
            'preview_token':snapshot_token(project, robot, token_dependencies, contents),
            'robot': {'id':robot.id, 'name':robot.name, 'version':robot.version,
                      'folder_id':robot.folder_id} if robot else None,
            'next_version': robot.version + 1 if robot else 1,
            'dependencies':dependencies,
            # Somente pacotes próprios da raiz podem ser promovidos aqui.
            'library_candidates': sorted({n.split('/')[0] for n in contents
                if n.count('/') == 1 and n.endswith('/__init__.py')
                and n.split('/')[0].isidentifier()
                and n.split('/')[0] not in {d['import_name'] for d in dependencies}}),
            'folders':[{'id':f.id, 'name':f.name, 'parent_id':f.parent_id} for f in folders]}


def destination_folder(db, folder_id, new_path):
    """Escolhe ou cria toda a sequência de pastas dentro da transação."""
    if folder_id is not None and not db.get(RobotFolder, folder_id):
        raise HTTPException(404, "Pasta de destino não encontrada.")
    if not new_path.strip():
        return folder_id
    for part in new_path.replace('\\','/').split('/'):
        name = safe_name(part)
        folder = db.query(RobotFolder).filter(
            RobotFolder.parent_id == folder_id,
            func.lower(RobotFolder.name) == name.lower()).first()
        if not folder:
            folder = RobotFolder(name=name, parent_id=folder_id)
            db.add(folder)
            db.flush()
        folder_id = folder.id
    return folder_id


def prepare_release(db, project, request, user_id, created_paths):
    """Prepara artefatos e alterações ORM, sem commit.

    O endpoint confirma Robot, LibraryVersions, vínculos e Workflow em uma
    única transação. created_paths permite limpar apenas artefatos desta
    tentativa quando a transação falhar.
    """
    robot = resolve_existing(db, project)
    dependencies, contents = collect_snapshot(db, project)
    if request.preview_token != snapshot_token(project, robot, dependencies, contents):
        raise HTTPException(409, "O projeto mudou depois da prévia. Feche e abra o Release novamente.")
    modified = {d['library_id'] for d in dependencies if d['modified']}
    if set(request.library_versions) != modified:
        raise HTTPException(400, "Informe uma nova versão para cada Biblioteca modificada, e somente para elas.")
    if robot:
        if request.new_folder_path.strip() or request.folder_id not in (None, robot.folder_id):
            raise HTTPException(409, "Robô existente deve permanecer na mesma pasta.")
        if request.robot_name and request.robot_name != robot.name:
            raise HTTPException(409, "Robô existente deve manter o mesmo cadastro.")
    else:
        folder_id = destination_folder(db, request.folder_id, request.new_folder_path)
        name = safe_name(request.robot_name or project.name)
        if not name.lower().endswith('.zip'):
            name += '.zip'
        name = safe_name(name)
        if db.query(Robot).filter(Robot.folder_id == folder_id,
                                 func.lower(Robot.name) == name.lower()).first():
            raise HTTPException(409, "Já existe um Robô com esse nome no destino. Para alterá-lo, use um projeto criado a partir dele.")
        robot = Robot(name=name, filename=name, version=0, file_hash='', file_path='', folder_id=folder_id)
        db.add(robot)
        db.flush()
    next_version = robot.version + 1
    # Mantém a versão pré-Release, inclusive para Robôs antigos cujo upload
    # sobrescrevia o ZIP. Versões anteriores já perdidas não são reconstruídas.
    if robot.version:
        old = robot_path(robot)
        if not old.is_file() or packager.calcular_sha256(old) != robot.file_hash:
            raise HTTPException(409, "Pacote atual de PRD ausente ou com hash inválido.")
        backup = packager.BASE_DIRECTORY / 'storage' / 'releases' / str(robot.id) / 'legacy' / f'{robot.version}-{robot.file_hash}' / old.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(old, backup)
        elif packager.calcular_sha256(backup) != robot.file_hash:
            raise HTTPException(409, "Snapshot anterior possui hash inválido.")
    # Ordem fixa de locks para dois projetos com várias Bibliotecas.
    for library_id in sorted(modified):
        library = (
            db.query(Library)
            .filter(Library.id == library_id)
            .with_for_update()
            .first()
        )

        if not library:
            raise HTTPException(
                409,
                "Biblioteca não encontrada durante o Release."
            )

        dependency = next(
            item
            for item in dependencies
            if item['library_id'] == library_id
        )

        is_new = bool(
            dependency.get('is_new')
            or dependency.get('library_version_id') is None
        )

        # Biblioteca publicada/modificada precisa continuar ativa.
        # Biblioteca NOVA nasce inativa de propósito para não aparecer
        # em Robôs > Bibliotecas antes do primeiro Release.
        if not is_new and not library.is_active:
            raise HTTPException(
                409,
                "Biblioteca desativada não pode receber nova versão."
            )

        if is_new:
            if library.production_version_id is not None:
                raise HTTPException(
                    409,
                    f'{library.name}: o draft está marcado como novo, '
                    'mas a biblioteca já possui versão em Produção.'
                )
        else:
            # Concorrência/stale draft: se outra publicação promoveu uma
            # versão de Produção depois que este projeto iniciou a edição,
            # não criamos uma nova versão em cima de uma base antiga.
            if (
                library.production_version_id
                != dependency['library_version_id']
            ):
                raise HTTPException(
                    409,
                    f'{library.name}: a Produção mudou desde que este '
                    'projeto começou a editar a biblioteca. Atualize a '
                    'dependência antes de publicar.'
                )

        version_name = request.library_versions[
            library_id
        ].strip()

        # Segue o mesmo validador semântico utilizado pela publicação
        # standalone, mas aplica a política atual do DUET: nova biblioteca
        # começa em 1.0.0 e cada alteração publicada sobe a MAJOR.
        from api.libraries import validar_versao
        version_name = validar_versao(version_name)

        expected_version = next_library_version(
            db,
            library_id
        )

        if version_name != expected_version:
            raise HTTPException(
                409,
                f'{library.name}: a próxima versão deve ser '
                f'{expected_version}.'
            )

        if (
            db.query(LibraryVersion)
            .filter(
                LibraryVersion.library_id == library_id,
                LibraryVersion.version == version_name
            )
            .first()
        ):
            raise HTTPException(
                409,
                f'{library.name}: a versão {version_name} já existe.'
            )

        namespace = dependency['import_name'] + '/'
        library_files = {
            name: data
            for name, data in contents.items()
            if name.startswith(namespace)
        }

        if namespace + '__init__.py' not in library_files:
            raise HTTPException(
                409,
                f'{library.name}: __init__.py não foi encontrado no '
                'snapshot do Release.'
            )

        # UUID impede que uma tentativa concorrente sobrescreva
        # outro artefato da mesma versão.
        artifact = (
            packager.LIBRARIES_REPOSITORY
            / str(library_id)
            / version_name
            / uuid4().hex
            / 'library.zip'
        )

        created_paths.append(artifact)

        artifact_hash = write_package(
            artifact,
            library_files
        )

        new_version = LibraryVersion(
            library_id=library_id,
            version=version_name,
            source_type='robot',
            source_robot_id=robot.id,
            source_robot_version=next_version,
            source_path=library.import_name,
            artifact_path=(
                artifact
                .relative_to(packager.BASE_DIRECTORY)
                .as_posix()
            ),
            file_hash=artifact_hash,
            published_by=user_id,
            is_active=1
        )

        db.add(new_version)
        db.flush()

        # A versão recém-criada passa a ser a versão vigente da Library
        # em Produção. A anterior continua imutável no histórico.
        library.production_version_id = new_version.id
        library.is_active = 1

        if dependency.get('dependency_id') is None:
            # Primeira publicação: agora finalmente existe uma versão
            # que pode ser fixada pelo AutomationProject.
            link = ProjectLibraryDependency(
                project_id=project.id,
                library_id=library.id,
                library_version_id=new_version.id,
                added_by=user_id
            )
            db.add(link)
            db.flush()
        else:
            link = db.get(
                ProjectLibraryDependency,
                dependency['dependency_id']
            )

            if not link:
                raise HTTPException(
                    409,
                    f'{library.name}: vínculo do projeto não foi encontrado.'
                )

            link.library_version_id = new_version.id
            link.added_by = user_id

        # Mantém o ProjectLibraryDraft como Working Copy do projeto,
        # agora baseado na versão que acabou de ser publicada.
        draft = (
            db.query(ProjectLibraryDraft)
            .filter(
                ProjectLibraryDraft.project_id == project.id,
                ProjectLibraryDraft.library_id == library.id
            )
            .first()
        )

        if draft:
            draft.base_library_version_id = new_version.id
            draft.is_modified = 0
            draft.updated_by = user_id

        dependency.update(
            draft_id=(draft.id if draft else dependency.get('draft_id')),
            dependency_id=link.id,
            library_version_id=new_version.id,
            version=version_name,
            file_hash=artifact_hash,
            modified=False,
            is_new=False,
            source_type='robot',
            source_robot_id=robot.id,
            source_robot_version=next_version
        )

    # Bibliotecas novas podem nascer de pacotes próprios do Robô.
    # O namespace e o código permanecem iguais aos utilizados nos testes.
    for item in request.new_libraries:
        from api.libraries import validar_import_name, validar_versao
        namespace = validar_import_name(item.import_name)
        version_name = validar_versao(item.version)
        if namespace + '/__init__.py' not in contents:
            raise HTTPException(400, "A nova Biblioteca precisa ser um pacote Python na raiz do projeto.")
        if db.query(Library).filter(Library.import_name == namespace).first():
            raise HTTPException(409, f"Já existe Biblioteca com namespace {namespace}; vincule-a ao projeto antes de publicar.")
        if not item.name.strip():
            raise HTTPException(400, "Informe o nome da nova Biblioteca.")
        library = Library(name=item.name.strip(), import_name=namespace, created_by=user_id, is_active=1)
        db.add(library)
        db.flush()
        artifact = packager.LIBRARIES_REPOSITORY / str(library.id) / version_name / uuid4().hex / 'library.zip'
        created_paths.append(artifact)
        file_hash = write_package(artifact, {n:b for n,b in contents.items() if n.startswith(namespace + '/')})
        version = LibraryVersion(library_id=library.id, version=version_name,
            source_type='robot', source_robot_id=robot.id, source_robot_version=next_version,
            source_path=namespace,
            artifact_path=artifact.relative_to(packager.BASE_DIRECTORY).as_posix(),
            file_hash=file_hash, published_by=user_id, is_active=1)
        db.add(version)
        db.flush()
        library.production_version_id = version.id
        library.is_active = 1
        link = ProjectLibraryDependency(project_id=project.id, library_id=library.id,
            library_version_id=version.id, added_by=user_id)
        db.add(link)
        db.flush()
        dependencies.append({'dependency_id':link.id, 'library_id':library.id,
            'library_name':library.name, 'import_name':namespace,
            'library_version_id':version.id, 'version':version_name,
            'file_hash':file_hash, 'modified':False, 'source_type':'robot',
            'source_robot_id':robot.id, 'source_robot_version':next_version})

    # Congela exatamente quais versões de bibliotecas foram utilizadas
    # por esta versão do Robot. Releases antigos nunca são atualizados.
    for dependency in dependencies:
        if dependency.get('library_version_id') is None:
            raise HTTPException(
                409,
                "Release possui biblioteca sem versão publicada."
            )

        db.add(
            RobotVersionLibraryDependency(
                robot_id=robot.id,
                robot_version=next_version,
                library_id=dependency['library_id'],
                library_version_id=dependency['library_version_id'],
                source_project_id=project.id,
                created_by=user_id
            )
        )



    # ============================================================
    # DATA ÚNICA DO RELEASE
    # ============================================================
    #
    # Utilizamos o mesmo instante tanto no manifesto quanto na
    # RobotVersion para que ambos representem a mesma publicação.
    # ============================================================

    release_published_at = datetime.utcnow()


    # ============================================================
    # MANIFESTO DO RELEASE
    # ============================================================

    manifest = {
        'schema_version': 1,
        'robot_id': robot.id,
        'robot_version': next_version,
        'project_id': project.id,
        'published_by': user_id,
        'published_at': release_published_at.isoformat(),
        'dependencies': dependencies,
    }


    contents[MANIFEST] = json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False
    ).encode()


    # ============================================================
    # NOME DO PACOTE
    # ============================================================

    filename = safe_name(
        robot.filename
    )


    if not filename.lower().endswith('.zip'):

        filename = (
            Path(filename).stem +
            '.zip'
        )


    # ============================================================
    # CAMINHO IMUTÁVEL DA NOVA VERSÃO
    # ============================================================
    #
    # Cada tentativa utiliza um UUID próprio.
    #
    # Nunca sobrescrevemos o artefato de outra versão ou
    # de outra tentativa de publicação.
    # ============================================================

    package = (
        packager.BASE_DIRECTORY
        / 'storage'
        / 'releases'
        / str(robot.id)
        / str(next_version)
        / uuid4().hex
        / filename
    )


    # O endpoint superior utiliza created_paths para remover
    # somente artefatos desta tentativa caso a transação falhe.
    created_paths.append(
        package
    )


    # ============================================================
    # CRIA O ZIP
    # ============================================================

    package_hash = write_package(
        package,
        contents
    )


    # ============================================================
    # REVALIDAÇÃO FÍSICA DO ARTEFATO
    # ============================================================
    #
    # Não confiamos somente no retorno de write_package.
    #
    # Antes de registrar RobotVersion:
    #
    # 1. o arquivo precisa existir;
    # 2. o SHA-256 precisa continuar igual;
    # 3. o ZIP precisa ser legível;
    # 4. o manifesto precisa existir e representar exatamente
    #    este Robot/version.
    # ============================================================

    if not package.is_file():

        raise HTTPException(
            500,
            "O pacote do Release não foi encontrado após a criação."
        )


    verified_hash = (
        packager.calcular_sha256(
            package
        )
    )


    if verified_hash != package_hash:

        raise HTTPException(
            500,
            "O pacote do Release falhou na validação de integridade."
        )


    verified_contents = read_package(
        package
    )


    if MANIFEST not in verified_contents:

        raise HTTPException(
            500,
            "O pacote do Release foi criado sem manifesto."
        )


    try:

        verified_manifest = json.loads(
            verified_contents[
                MANIFEST
            ]
        )

    except Exception as error:

        raise HTTPException(
            500,
            "O manifesto gravado no pacote do Release é inválido."
        ) from error


    if (
        verified_manifest.get(
            'schema_version'
        ) != 1

        or

        verified_manifest.get(
            'robot_id'
        ) != robot.id

        or

        verified_manifest.get(
            'robot_version'
        ) != next_version
    ):

        raise HTTPException(
            500,
            "O manifesto gravado não corresponde ao Robot/version do Release."
        )


    # ============================================================
    # ROBOT VERSION IMUTÁVEL
    # ============================================================
    #
    # Agora o Release deixa de existir somente como:
    #
    #     Robot.file_path
    #     Robot.file_hash
    #
    # Cada versão passa a possuir um registro próprio.
    #
    # IMPORTANTE:
    # ainda estamos dentro da MESMA transação do Release.
    #
    # Se qualquer parte posterior falhar:
    #
    #     db.rollback()
    #
    # remove este registro junto com as demais alterações.
    # ============================================================

    robot_version = RobotVersion(

        # Robot lógico proprietário desta versão.
        robot_id=
            robot.id,

        # Número exato da versão publicada.
        version=
            next_version,

        # Nome físico do ZIP.
        filename=
            filename,

        # RobotVersion utiliza caminho relativo à raiz do
        # Control Room para evitar acoplamento à máquina.
        artifact_path=
            package
            .relative_to(
                packager.BASE_DIRECTORY
            )
            .as_posix(),

        # SHA-256 comprovado após a escrita do arquivo.
        file_hash=
            verified_hash,

        # AutomationProject que originou esta versão.
        source_project_id=
            project.id,

        # Usuário responsável pela publicação.
        published_by=
            user_id,

        # Mesmo instante utilizado no manifesto.
        published_at=
            release_published_at,
    )


    db.add(
        robot_version
    )


    # Força INSERT ainda dentro da transação.
    #
    # Isso faz constraints como:
    #
    #     UNIQUE(robot_id, version)
    #
    # falharem ANTES de atualizarmos o ponteiro atual do Robot.
    db.flush()


    # ============================================================
    # ROBOT = PONTEIRO PARA A VERSÃO ATUAL
    # ============================================================
    #
    # Robot continua existindo porque Agent, Scheduler e outras
    # partes da aplicação dependem dele.
    #
    # Mas agora ele deixa de ser a única fonte do artefato.
    # ============================================================

    robot.version = next_version
    robot.filename = filename
    robot.file_path = str(
        package
    )
    robot.file_hash = verified_hash


    # ============================================================
    # PROJECT PUBLICADO
    # ============================================================

    project.base_robot_id = robot.id
    project.base_version = next_version
    project.status = 'published'


    return {
        'robot_id': robot.id,
        'robot_name': robot.name,
        'version': next_version,
        'folder_id': robot.folder_id,
        'file_hash': verified_hash,
        'dependencies': dependencies,
    }

def restore_project_from_robot(db, project, robot, user_id):
    """
    Restaura código e vínculos a partir de uma RobotVersion publicada.

    A fonte oficial não é mais:

        Robot.file_path
        Robot.file_hash

    A versão exata utilizada pelo AutomationProject é:

        project.base_version

    Isso permitirá inclusive abrir versões históricas futuramente,
    sem depender do ponteiro atual do Robot.
    """

    from development.workspace_core import DRAFT_DIRECTORY


    # ============================================================
    # VERSÃO EXATA DE ORIGEM
    # ============================================================

    if project.base_version is None:

        raise HTTPException(
            409,
            "O projeto não possui versão de origem definida."
        )


    # Localiza e valida fisicamente a RobotVersion.
    robot_version, path = resolve_robot_version(
        db,
        robot.id,
        project.base_version
    )


    # ============================================================
    # FORMATO DO PACOTE
    # ============================================================

    if not zipfile.is_zipfile(
        path
    ):

        raise HTTPException(
            409,
            (
                "Para abrir no Studio, a RobotVersion precisa "
                "possuir um pacote ZIP válido."
            )
        )


    contents = read_package(
        path
    )


    manifest = (
        json.loads(
            contents.pop(
                MANIFEST
            )
        )
        if MANIFEST in contents
        else None
    )


    # ============================================================
    # ENTRYPOINT DO ROBOT
    # ============================================================

    if 'main.py' not in contents:

        raise HTTPException(
            409,
            (
                "O pacote precisa conter main.py na raiz "
                "para abrir no Studio."
            )
        )


    # ============================================================
    # CONSISTÊNCIA DO MANIFESTO
    # ============================================================

    if manifest and (
        manifest.get(
            'schema_version'
        ) != 1

        or

        manifest.get(
            'robot_id'
        ) != robot.id

        or

        manifest.get(
            'robot_version'
        ) != robot_version.version
    ):

        raise HTTPException(
            409,
            (
                "Manifesto do Release não corresponde "
                "à RobotVersion selecionada."
            )
        )
    target = packager.WORKSPACE_REPOSITORY / str(project.id)
    if target.exists():
        raise HTTPException(409, "O workspace de destino já existe.")
    namespaces = {}
    for dependency in manifest.get('dependencies', []) if manifest else []:
        version = db.get(LibraryVersion, dependency['library_version_id'])
        library = db.get(Library, dependency['library_id'])
        if not version or not library or version.library_id != library.id or library.import_name != dependency['import_name']:
            raise HTTPException(409, "Dependência do Release não está disponível no cadastro.")
        namespaces[library.import_name] = library.id
        db.add(ProjectLibraryDependency(project_id=project.id, library_id=library.id,
            library_version_id=version.id, added_by=user_id))

        # Registra também a Working Copy do projeto. O código físico é
        # restaurado em _libraries logo abaixo, preservando a separação
        # entre versão publicada e cópia editável.
        from development.workspace_core import draft_workspace_value
        db.add(ProjectLibraryDraft(
            project_id=project.id,
            library_id=library.id,
            base_library_version_id=version.id,
            workspace_path=draft_workspace_value(
                project.id,
                library.import_name
            ),
            is_modified=0,
            created_by=user_id,
            updated_by=None
        ))
    with tempfile.TemporaryDirectory(dir=packager.BUILD_TEMP_REPOSITORY) as tmp:
        root = Path(tmp) / 'workspace'
        root.mkdir()
        for name, data in contents.items():
            if name.split('/')[0] == DRAFT_DIRECTORY:
                raise HTTPException(409, "Pacote contém pasta reservada de Desenvolvimento.")
            destination = root / (DRAFT_DIRECTORY if name.split('/')[0] in namespaces else '') / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root), str(target))
    return target


def lock_publication(db):
    """Serializa criação de pastas/Robôs entre rotas no PostgreSQL.

    Transacional e liberado automaticamente pelo banco. Os locks de projeto
    protegem workspace/checkout; este lock também cobre novos cadastros,
    que ainda não possuem uma linha para SELECT FOR UPDATE.
    """
    from sqlalchemy import text
    if db.get_bind().dialect.name == 'postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(734621901)'))
