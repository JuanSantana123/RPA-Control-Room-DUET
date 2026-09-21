# ============================================================
# LIBRARIES - SNAPSHOT SERVICE
# ============================================================
#
# Responsável pela leitura segura dos snapshots imutáveis das
# LibraryVersions publicadas.
#
# RESPONSABILIDADES:
#
# - localizar uma versão pertencente a uma Library;
# - resolver com segurança o ZIP físico publicado;
# - montar a árvore interna do snapshot;
# - visualizar a árvore de arquivos;
# - visualizar arquivos textuais;
# - disponibilizar o ZIP para download.
#
# IMPORTANTE:
#
# Este módulo trabalha SOMENTE com snapshots publicados.
#
# Ele NÃO:
#
# - altera Working Copy;
# - extrai ZIP para Development;
# - publica novas versões;
# - altera banco de dados;
# - registra endpoints FastAPI;
# - executa RBAC.
#
# RBAC e Depends() continuarão no api/libraries.py.
# ============================================================


import zipfile

from pathlib import Path, PurePosixPath

from fastapi import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models import (
    Library,
    LibraryVersion,
)

from libraries.repository import (
    BASE_DIRECTORY,
    LIBRARIES_REPOSITORY,
    MAX_LIBRARY_VIEW_FILE_SIZE,
)

from libraries.serializers import (
    serializar_library_version,
)

from libraries.validators import (
    obter_library_or_404,
    validar_zip_biblioteca,
)


# ============================================================
# LOCALIZAR VERSÃO PUBLICADA
# ============================================================

def obter_versao_publicada_or_404(
    db: Session,
    library_id: int,
    version_id: int,
) -> tuple[Library, LibraryVersion]:
    """
    Localiza uma LibraryVersion pertencente à Library informada.

    Esta função é utilizada para leitura do snapshot imutável.

    Retorna:

        (
            Library,
            LibraryVersion
        )

    Nenhum registro ou arquivo é alterado.
    """

    library = obter_library_or_404(
        db,
        library_id,
    )

    version = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id == version_id,
            LibraryVersion.library_id == library_id,
        )
        .first()
    )

    if not version:

        raise HTTPException(
            status_code=404,
            detail="Versão da biblioteca não encontrada.",
        )

    return library, version


# ============================================================
# RESOLVER ARTEFATO FÍSICO
# ============================================================

def resolver_artefato_versao_publicada(
    version: LibraryVersion,
) -> Path:
    """
    Resolve com segurança o ZIP físico de uma LibraryVersion.

    O artifact_path persistido no banco precisa obrigatoriamente
    permanecer dentro de:

        storage/libraries/

    Essa proteção impede que um caminho incorreto ou adulterado
    no banco permita leitura de arquivos externos ao repositório
    oficial das Libraries.
    """

    artifact_path = (
        BASE_DIRECTORY
        / version.artifact_path
    ).resolve()

    repository_root = (
        LIBRARIES_REPOSITORY
        .resolve()
    )

    # --------------------------------------------------------
    # PROTEÇÃO CONTRA PATH ESCAPE
    # --------------------------------------------------------
    #
    # Aceitamos apenas:
    #
    #     repository_root / ...
    #
    # Qualquer caminho fora de storage/libraries é rejeitado.
    # --------------------------------------------------------

    if (
        artifact_path != repository_root
        and repository_root not in artifact_path.parents
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "O artefato da biblioteca possui "
                "um caminho inválido."
            ),
        )

    if not artifact_path.is_file():

        raise HTTPException(
            status_code=404,
            detail=(
                "O artefato físico desta versão "
                "não foi encontrado."
            ),
        )

    # Aqui verificamos apenas se o artefato físico é realmente
    # reconhecido como ZIP.
    #
    # A validação estrutural do namespace ocorre posteriormente
    # através de validar_zip_biblioteca().
    if not zipfile.is_zipfile(
        artifact_path
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "O snapshot desta versão não é "
                "um ZIP válido."
            ),
        )

    return artifact_path


# ============================================================
# MONTAR ÁRVORE DO SNAPSHOT
# ============================================================

def montar_arvore_snapshot(
    arquivos: list[str],
) -> list[dict]:
    """
    Converte caminhos internos do ZIP em uma árvore adequada
    para o Explorer do frontend.

    Exemplo:

        teste/__init__.py
        teste/teste1.py
        teste/teste1/teste.py

    Resultado conceitual:

        teste/
            __init__.py
            teste1.py
            teste1/
                teste.py

    Pastas aparecem antes dos arquivos e cada nível é ordenado
    alfabeticamente.
    """

    root: dict[str, dict] = {}

    for arquivo in sorted(
        arquivos,
        key=str.lower,
    ):

        caminho = PurePosixPath(
            arquivo
        )

        atual = root

        for indice, parte in enumerate(
            caminho.parts
        ):

            ultimo = (
                indice
                == len(caminho.parts) - 1
            )

            if parte not in atual:

                atual[parte] = {
                    "type":
                        "file"
                        if ultimo
                        else "folder",

                    "name":
                        parte,

                    "path":
                        "/".join(
                            caminho.parts[
                                :indice + 1
                            ]
                        ),

                    "children":
                        {}
                        if not ultimo
                        else None,
                }

            if not ultimo:

                atual = atual[
                    parte
                ]["children"]

    # --------------------------------------------------------
    # CONVERSÃO PARA O CONTRATO DA API
    # --------------------------------------------------------

    def converter(
        nodes: dict[str, dict],
    ) -> list[dict]:
        """
        Converte a estrutura interna baseada em dictionaries
        para a lista recursiva devolvida ao frontend.
        """

        resultado = []

        itens = sorted(
            nodes.values(),
            key=lambda item: (
                0
                if item["type"] == "folder"
                else 1,

                item["name"].lower(),
            ),
        )

        for item in itens:

            if item["type"] == "folder":

                resultado.append({
                    "type": "folder",
                    "name": item["name"],
                    "path": item["path"],
                    "children": converter(
                        item["children"]
                    ),
                })

            else:

                resultado.append({
                    "type": "file",
                    "name": item["name"],
                    "path": item["path"],
                })

        return resultado

    return converter(
        root
    )


# ============================================================
# VISUALIZAR ÁRVORE DA VERSÃO
# ============================================================

def visualizar_arvore_versao_service(
    library_id: int,
    version_id: int,
    db: Session,
) -> dict:
    """
    Retorna a estrutura de arquivos existente dentro do snapshot
    imutável de uma LibraryVersion.

    A operação:

    - não lê Working Copy;
    - não extrai o ZIP;
    - não modifica arquivos;
    - não altera o banco.
    """

    library, version = (
        obter_versao_publicada_or_404(
            db,
            library_id,
            version_id,
        )
    )

    artifact_path = (
        resolver_artefato_versao_publicada(
            version
        )
    )

    # Além de confirmar que o ZIP é válido, esta função garante
    # que o conteúdo está estruturado sob o import_name oficial
    # da Library.
    validar_zip_biblioteca(
        artifact_path,
        library.import_name,
    )

    arquivos = []

    try:

        with zipfile.ZipFile(
            artifact_path,
            "r",
        ) as arquivo_zip:

            for membro in (
                arquivo_zip.infolist()
            ):

                # Diretórios explícitos do ZIP não entram na lista.
                # A árvore é reconstruída através dos paths dos
                # arquivos reais.
                if membro.is_dir():
                    continue

                caminho = (
                    membro.filename
                    .replace("\\", "/")
                )

                arquivos.append(
                    caminho
                )

    except zipfile.BadZipFile:

        raise HTTPException(
            status_code=409,
            detail=(
                "O snapshot desta versão "
                "está corrompido."
            ),
        )

    return {
        "status": "success",

        "library": {
            "id": library.id,
            "name": library.name,
            "import_name":
                library.import_name,
        },

        "version":
            serializar_library_version(
                version,
                library.production_version_id,
            ),

        "tree":
            montar_arvore_snapshot(
                arquivos
            ),
    }


# ============================================================
# VISUALIZAR ARQUIVO DA VERSÃO
# ============================================================

def visualizar_arquivo_versao_service(
    library_id: int,
    version_id: int,
    path: str,
    db: Session,
) -> dict:
    """
    Retorna o conteúdo textual UTF-8 de um arquivo existente
    dentro do snapshot imutável.

    Proteções:

    - caminho precisa estar dentro do import_name;
    - caminhos absolutos são bloqueados;
    - ".." é bloqueado;
    - diretórios não podem ser abertos como arquivo;
    - arquivos muito grandes não são carregados;
    - conteúdo precisa ser UTF-8.
    """

    library, version = (
        obter_versao_publicada_or_404(
            db,
            library_id,
            version_id,
        )
    )

    artifact_path = (
        resolver_artefato_versao_publicada(
            version
        )
    )

    caminho = PurePosixPath(
        path
        .strip()
        .replace("\\", "/")
    )

    # --------------------------------------------------------
    # SEGURANÇA DO PATH SOLICITADO
    # --------------------------------------------------------

    if (
        not caminho.parts
        or caminho.is_absolute()
        or ".." in caminho.parts
        or caminho.parts[0]
        != library.import_name
    ):

        raise HTTPException(
            status_code=400,
            detail="Caminho de arquivo inválido.",
        )

    # Confirma novamente que o snapshot completo obedece à
    # estrutura segura da Library.
    validar_zip_biblioteca(
        artifact_path,
        library.import_name,
    )

    try:

        with zipfile.ZipFile(
            artifact_path,
            "r",
        ) as arquivo_zip:

            try:

                info = arquivo_zip.getinfo(
                    caminho.as_posix()
                )

            except KeyError:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Arquivo não encontrado "
                        "nesta versão."
                    ),
                )

            if info.is_dir():

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O caminho informado "
                        "representa uma pasta."
                    ),
                )

            # Impede carregar arquivos excessivamente grandes no
            # visualizador de código do frontend.
            if (
                info.file_size
                > MAX_LIBRARY_VIEW_FILE_SIZE
            ):

                raise HTTPException(
                    status_code=413,
                    detail=(
                        "O arquivo é muito grande "
                        "para visualização."
                    ),
                )

            conteudo_bytes = (
                arquivo_zip.read(
                    info
                )
            )

    except zipfile.BadZipFile:

        raise HTTPException(
            status_code=409,
            detail=(
                "O snapshot desta versão "
                "está corrompido."
            ),
        )

    # O visualizador trabalha somente com conteúdo textual UTF-8.
    try:

        conteudo = (
            conteudo_bytes.decode(
                "utf-8"
            )
        )

    except UnicodeDecodeError:

        raise HTTPException(
            status_code=415,
            detail=(
                "Este arquivo não é textual "
                "UTF-8 e não pode ser "
                "visualizado no editor."
            ),
        )

    return {
        "status": "success",
        "library_id": library.id,
        "version_id": version.id,
        "version": version.version,
        "path": caminho.as_posix(),
        "content": conteudo,
    }


# ============================================================
# DOWNLOAD DA VERSÃO
# ============================================================

def baixar_versao_service(
    library_id: int,
    version_id: int,
    db: Session,
) -> FileResponse:
    """
    Retorna o snapshot ZIP imutável da LibraryVersion.

    O cliente nunca fornece o caminho físico do artefato.

    IMPORTANTE:

    Este método mantém o comportamento específico do endpoint
    original de download: valida existência e confinamento físico
    do artefato, mas não executa validar_zip_biblioteca().
    """

    obter_library_or_404(
        db,
        library_id,
    )

    version = (
        db.query(LibraryVersion)
        .filter(
            LibraryVersion.id
            == version_id,
            LibraryVersion.library_id
            == library_id,
        )
        .first()
    )

    if not version:

        raise HTTPException(
            status_code=404,
            detail=(
                "Versão da biblioteca não encontrada."
            ),
        )

    artifact_path = (
        BASE_DIRECTORY
        / version.artifact_path
    ).resolve()

    repository_root = (
        LIBRARIES_REPOSITORY
        .resolve()
    )

    # Defesa contra um artifact_path indevido persistido no banco.
    if (
        artifact_path != repository_root
        and repository_root not in artifact_path.parents
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "O artefato da biblioteca possui um caminho inválido."
            ),
        )

    if not artifact_path.is_file():

        raise HTTPException(
            status_code=404,
            detail=(
                "O artefato físico desta versão não foi encontrado."
            ),
        )

    return FileResponse(
        path=str(
            artifact_path
        ),
        media_type="application/zip",
        filename=(
            f"{version.version}.zip"
        ),
    )