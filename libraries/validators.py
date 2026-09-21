# ============================================================
# LIBRARIES - VALIDATORS
# ============================================================
#
# Validações compartilhadas pelo domínio global de Libraries.
#
# RESPONSABILIDADES:
#
# - validar namespace Python (import_name);
# - validar Semantic Versioning;
# - validar segurança e estrutura de ZIPs;
# - calcular SHA-256 dos artefatos;
# - validar nomes e hierarquia de LibraryFolders;
# - localizar Library/LibraryFolder/AutomationProject;
# - exigir Checkout para alterações nas dependências.
#
# Este módulo NÃO registra endpoints FastAPI.
# Este módulo NÃO realiza commit/rollback.
# ============================================================


import hashlib
import keyword
import re
import stat
import zipfile

from pathlib import Path, PurePosixPath

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    AutomationProject,
    Library,
    LibraryFolder,
    ProjectCheckout,
    User,
)

from libraries.repository import (
    UPLOAD_CHUNK_SIZE,
)

from security.artifacts import (
    ArtifactSecurityError,
    normalizar_membro_zip,
    validar_zip,
)
# ============================================================
# SEMANTIC VERSIONING
# ============================================================
#
# Exemplos aceitos:
#
#     1.0.0
#     1.2.3
#     2.0.0-beta.1
#     2.0.0+build.7
#
# Mantém exatamente a expressão utilizada pelo módulo original.
# ============================================================

SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-"
    r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\."
    r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*"
    r")?"
    r"(?:\+"
    r"[0-9A-Za-z-]+"
    r"(?:\.[0-9A-Za-z-]+)*"
    r")?$"
)


# ============================================================
# IMPORT NAME
# ============================================================

def validar_import_name(
    value: str,
) -> str:
    """
    Valida o namespace Python da Library.

    Exemplos aceitos:

        financeiro
        kenan
        sap_utils

    Exemplos bloqueados:

        financeiro-pagamentos
        123lib
        class
        import
    """

    import_name = value.strip()

    if not import_name:

        raise HTTPException(
            status_code=400,
            detail="O import_name não pode ficar vazio.",
        )

    # isidentifier() garante que o valor pode ser utilizado como
    # identificador Python.
    if not import_name.isidentifier():

        raise HTTPException(
            status_code=400,
            detail=(
                "O import_name precisa ser um identificador Python válido. "
                "Exemplo: financeiro ou sap_utils."
            ),
        )

    # Mesmo sendo identificadores sintaticamente válidos, palavras
    # reservadas como "class" e "import" não podem ser namespaces.
    if keyword.iskeyword(import_name):

        raise HTTPException(
            status_code=400,
            detail=(
                "O import_name não pode ser uma palavra reservada do Python."
            ),
        )

    return import_name


# ============================================================
# VERSIONAMENTO
# ============================================================

def validar_versao(
    value: str,
) -> str:
    """
    Normaliza e valida uma versão usando o padrão SemVer aceito
    atualmente pelo DUET.
    """

    version = value.strip()

    if not SEMVER_PATTERN.fullmatch(version):

        raise HTTPException(
            status_code=400,
            detail=(
                "Versão inválida. Utilize versionamento semântico, "
                "por exemplo 1.0.0 ou 2.1.0-beta.1."
            ),
        )

    return version


# ============================================================
# ZIP DA LIBRARY
# ============================================================
# 
def validar_zip_biblioteca(
    zip_path: Path,
    import_name: str,
) -> None:
    """
    Valida uma LibraryVersion.

    A segurança estrutural genérica pertence a
    security.artifacts.

    Aqui permanecem apenas regras específicas de Library:

    - ZIP não vazio;
    - todo conteúdo pertence ao namespace import_name;
    - namespace existe;
    - __init__.py existe;
    - existe pelo menos um arquivo Python.
    """

    try:

        # A publicação standalone já limita o upload compactado
        # a 50 MB. Aqui aplicamos também todas as proteções
        # estruturais compartilhadas.
        validar_zip(
            zip_path,
            max_zip_size=None,
        )

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as arquivo_zip:

            membros = (
                arquivo_zip.infolist()
            )

            if not membros:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O ZIP da biblioteca está vazio."
                    ),
                )

            possui_codigo_python = False
            possui_init_raiz = False
            possui_pasta_import = False

            for membro in membros:

                caminho = (
                    normalizar_membro_zip(
                        membro.filename
                    )
                )

                if not caminho.parts:
                    continue

                # Library publicada não pode carregar conteúdo
                # fora do próprio namespace.
                if (
                    caminho.parts[0]
                    != import_name
                ):

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f'O ZIP da biblioteca deve conter '
                            f'apenas o namespace "{import_name}/".'
                        ),
                    )

                possui_pasta_import = True

                if (
                    len(caminho.parts) == 2
                    and caminho.parts[0] == import_name
                    and caminho.parts[1] == "__init__.py"
                ):

                    possui_init_raiz = True

                if (
                    not membro.is_dir()
                    and caminho.parts[0] == import_name
                    and caminho.suffix.lower() == ".py"
                ):

                    possui_codigo_python = True

            if not possui_pasta_import:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f'O ZIP precisa possuir a pasta '
                        f'"{import_name}/" na raiz.'
                    ),
                )

            if not possui_init_raiz:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f'O pacote precisa possuir '
                        f'"{import_name}/__init__.py".'
                    ),
                )

            if not possui_codigo_python:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O pacote não possui arquivos Python "
                        "dentro do namespace da biblioteca."
                    ),
                )

    except HTTPException:
        raise

    except ArtifactSecurityError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except zipfile.BadZipFile as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "O arquivo enviado não é um ZIP válido."
            ),
        ) from error
# 
# ==========================================================
# SHA-256
# ============================================================

def calcular_sha256(
    file_path: Path,
) -> str:
    """
    Calcula o SHA-256 do artefato completo da Library.

    A leitura ocorre em blocos definidos por UPLOAD_CHUNK_SIZE,
    evitando carregar todo o ZIP em memória.
    """

    digest = hashlib.sha256()

    with file_path.open(
        "rb",
    ) as arquivo:

        while True:

            bloco = arquivo.read(
                UPLOAD_CHUNK_SIZE
            )

            if not bloco:
                break

            digest.update(
                bloco
            )

    return digest.hexdigest()


# ============================================================
# LIBRARY FOLDER - NOME
# ============================================================

def validar_nome_pasta(
    value: str,
) -> str:
    """
    Remove espaços externos e impede nomes compostos somente
    por espaços.

    O limite de tamanho continua sendo responsabilidade do
    schema Pydantic.
    """

    nome = value.strip()

    if not nome:

        raise HTTPException(
            status_code=400,
            detail="O nome da pasta não pode ficar vazio.",
        )

    return nome


# ============================================================
# LIBRARY FOLDER - BUSCA
# ============================================================

def obter_library_folder_or_404(
    db: Session,
    folder_id: int,
    somente_ativa: bool = False,
) -> LibraryFolder:
    """
    Localiza uma LibraryFolder.

    somente_ativa=True:
        também exige is_active == 1.

    Essa opção é utilizada principalmente quando a pasta será
    utilizada como destino de outra pasta ou Library.
    """

    consulta = (
        db.query(LibraryFolder)
        .filter(
            LibraryFolder.id == folder_id
        )
    )

    if somente_ativa:

        consulta = consulta.filter(
            LibraryFolder.is_active == 1
        )

    folder = consulta.first()

    if not folder:

        raise HTTPException(
            status_code=404,
            detail="Pasta de bibliotecas não encontrada.",
        )

    return folder


# ============================================================
# LIBRARY FOLDER - UNICIDADE
# ============================================================

def validar_nome_pasta_unico(
    db: Session,
    nome: str,
    parent_id: int | None,
    ignorar_folder_id: int | None = None,
) -> None:
    """
    Impede duas pastas ATIVAS com o mesmo nome dentro do mesmo pai.

    Permitido:

        Financeiro / Util
        SAP        / Util

    Bloqueado:

        Financeiro / Util
        Financeiro / Util

    ignorar_folder_id:
        utilizado durante rename para a pasta não conflitar
        consigo mesma.
    """

    consulta = (
        db.query(LibraryFolder)
        .filter(
            LibraryFolder.is_active == 1,
            func.lower(LibraryFolder.name)
            == nome.lower(),
        )
    )

    if parent_id is None:

        consulta = consulta.filter(
            LibraryFolder.parent_id.is_(None)
        )

    else:

        consulta = consulta.filter(
            LibraryFolder.parent_id == parent_id
        )

    if ignorar_folder_id is not None:

        consulta = consulta.filter(
            LibraryFolder.id != ignorar_folder_id
        )

    if consulta.first():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe uma pasta ativa com este nome "
                "neste mesmo local."
            ),
        )


# ============================================================
# LIBRARY FOLDER - DESTINO
# ============================================================

def validar_destino_pasta(
    db: Session,
    parent_id: int | None,
    folder_id_movida: int | None = None,
) -> LibraryFolder | None:
    """
    Valida a pasta de destino de uma movimentação.

    Regras preservadas:

    - None representa a raiz;
    - destino precisa existir e estar ativo;
    - pasta não pode ser movida para ela mesma;
    - pasta não pode entrar em uma descendente;
    - ciclos existentes na hierarquia também são detectados.
    """

    # None representa a raiz do catálogo.
    if parent_id is None:
        return None

    destino = obter_library_folder_or_404(
        db,
        parent_id,
        somente_ativa=True,
    )

    # Quando não estamos movendo uma pasta, basta confirmar que
    # o destino existe e está ativo.
    if folder_id_movida is None:
        return destino

    if destino.id == folder_id_movida:

        raise HTTPException(
            status_code=409,
            detail=(
                "Uma pasta não pode ser movida para dentro dela mesma."
            ),
        )

    visitados = set()
    atual = destino

    # Caminha dos pais do destino em direção à raiz.
    #
    # Se encontrarmos folder_id_movida, significa que o destino
    # está dentro da própria árvore que está sendo movida.
    while atual is not None:

        if atual.id in visitados:

            raise HTTPException(
                status_code=409,
                detail=(
                    "A hierarquia de pastas possui um ciclo inválido. "
                    "A movimentação foi bloqueada."
                ),
            )

        visitados.add(
            atual.id
        )

        if atual.id == folder_id_movida:

            raise HTTPException(
                status_code=409,
                detail=(
                    "A pasta não pode ser movida para dentro "
                    "de uma de suas próprias subpastas."
                ),
            )

        if atual.parent_id is None:
            break

        atual = (
            db.query(LibraryFolder)
            .filter(
                LibraryFolder.id
                == atual.parent_id,
                LibraryFolder.is_active == 1,
            )
            .first()
        )

        if atual is None:

            raise HTTPException(
                status_code=409,
                detail=(
                    "A pasta de destino possui uma hierarquia inválida "
                    "ou contém uma pasta pai desativada."
                ),
            )

    return destino


# ============================================================
# LIBRARY - BUSCA
# ============================================================

def obter_library_or_404(
    db: Session,
    library_id: int,
    somente_ativa: bool = False,
) -> Library:
    """
    Localiza uma Library pelo ID.

    somente_ativa=True:
        também exige Library.is_active == 1.
    """

    consulta = (
        db.query(Library)
        .filter(
            Library.id == library_id
        )
    )

    if somente_ativa:

        consulta = consulta.filter(
            Library.is_active == 1
        )

    library = consulta.first()

    if not library:

        raise HTTPException(
            status_code=404,
            detail="Biblioteca não encontrada.",
        )

    return library


# ============================================================
# AUTOMATION PROJECT - BUSCA
# ============================================================

def obter_projeto_ativo_or_404(
    db: Session,
    project_id: int,
) -> AutomationProject:
    """
    Localiza um AutomationProject ativo.

    with_for_update():
        preserva o bloqueio pessimista utilizado pelo código
        original para operações que alteram sua composição.
    """

    projeto = (
        db.query(AutomationProject)
        .filter(
            AutomationProject.id == project_id,
            AutomationProject.is_active == 1,
        )
        .with_for_update()
        .first()
    )

    if not projeto:

        raise HTTPException(
            status_code=404,
            detail="Projeto de Desenvolvimento não encontrado.",
        )

    return projeto


# ============================================================
# CHECKOUT DO PROJETO
# ============================================================

def exigir_checkout_projeto(
    db: Session,
    project_id: int,
    user_id: int,
) -> ProjectCheckout:
    """
    Exige Checkout pertencente ao usuário que está tentando
    alterar as dependências da Library no AutomationProject.

    Dependências fazem parte da composição do projeto e seguem
    a mesma proteção de edição utilizada pelo Development.
    """

    checkout = (
        db.query(ProjectCheckout)
        .filter(
            ProjectCheckout.project_id
            == project_id
        )
        .first()
    )

    # Projeto sem Checkout não pode ter composição alterada.
    if not checkout:

        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "É necessário realizar Checkout antes de alterar "
                    "as bibliotecas do projeto."
                ),
                "checkout_user_id": None,
                "checkout_user_name": None,
            },
        )

    # Existe Checkout, mas pertence a outro usuário.
    if checkout.user_id != user_id:

        checkout_user = (
            db.query(User)
            .filter(
                User.id
                == checkout.user_id
            )
            .first()
        )

        raise HTTPException(
            status_code=423,
            detail={
                "message": (
                    "O projeto está em Checkout por outro usuário."
                ),
                "checkout_user_id":
                    checkout.user_id,
                "checkout_user_name": (
                    checkout_user.name
                    if checkout_user
                    else None
                ),
            },
        )

    return checkout