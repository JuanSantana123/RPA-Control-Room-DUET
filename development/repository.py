# ============================================================
# DEVELOPMENT - WORKSPACE REPOSITORY
# ============================================================
#
# Responsável pela infraestrutura básica dos workspaces
# utilizados pelos AutomationProjects do DUET CORE.
#
# Este módulo centraliza:
#
# - localização do diretório de workspaces;
# - resolução do workspace físico de um projeto;
# - inicialização do workspace padrão;
# - resolução segura de caminhos relativos;
# - validação de nomes de arquivos e pastas;
# - montagem da árvore utilizada pelo Explorer do Studio.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - acessa o banco de dados;
# - realiza autenticação;
# - aplica RBAC;
# - controla Checkout;
# - executa regras de publicação.
#
# Essas responsabilidades pertencem às respectivas camadas
# de serviço e ao router HTTP.
# ============================================================

import os
import stat
import shutil
from pathlib import Path

from fastapi import HTTPException


# ============================================================
# DIRETÓRIO BASE DO CONTROL ROOM
# ============================================================
#
# __file__ aponta para:
#
#     RPA-Control-Room/development/repository.py
#
# Portanto:
#
#     Path(__file__).parent.parent
#
# representa:
#
#     RPA-Control-Room/
#
# Isso mantém exatamente a mesma raiz física utilizada
# anteriormente por api/development.py.
# ============================================================

BASE_DIRECTORY = Path(
    os.path.abspath(__file__)
).parent.parent


# ============================================================
# REPOSITÓRIO DOS WORKSPACES
# ============================================================
#
# Estrutura:
#
#     RPA-Control-Room/
#         workspaces/
#             {project_id}/
#
# Cada AutomationProject possui seu próprio diretório.
# ============================================================

WORKSPACE_REPOSITORY = (
    BASE_DIRECTORY /
    "workspaces"
)


# Garante que a raiz dos workspaces exista.
#
# exist_ok=True:
#     não gera erro quando a pasta já existe.
#
# parents=True:
#     cria diretórios pais caso sejam necessários.
WORKSPACE_REPOSITORY.mkdir(
    parents=True,
    exist_ok=True,
)

# ============================================================
# SEGURANÇA DO FILESYSTEM DO WORKSPACE
# ============================================================
#
# O DUET precisa produzir Workspaces portáveis para Agents
# Windows. Por isso aplicamos as restrições de nomes do Windows
# mesmo quando o Control Room estiver rodando em outro SO.
#
# Além disso, links simbólicos e outros pontos de redirecionamento
# não podem ser utilizados para fazer o Studio atravessar a
# fronteira física do Workspace.
# ============================================================

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

WINDOWS_INVALID_CHARACTERS = set(
    '<>:"/\\|?*'
)


def validar_componente_workspace(
    nome: str,
) -> str:
    """
    Valida UM componente de caminho do Workspace.

    Exemplos válidos:
        main.py
        src
        processamento.py

    Esta função não recebe caminhos completos. Cada componente
    de um path é validado individualmente por
    validar_caminho_relativo_workspace().
    """

    if not isinstance(nome, str):
        raise HTTPException(
            status_code=400,
            detail="Nome de arquivo ou pasta inválido.",
        )

    # Não fazemos strip silencioso aqui.
    #
    # " arquivo.py" é um nome diferente de "arquivo.py".
    # Alterar o valor recebido poderia fazer o backend operar
    # sobre um arquivo diferente daquele solicitado pelo Studio.
    if (
        not nome
        or nome in {".", ".."}
        or "\x00" in nome
    ):
        raise HTTPException(
            status_code=400,
            detail="Nome de arquivo ou pasta inválido.",
        )

    if any(
        caractere in WINDOWS_INVALID_CHARACTERS
        for caractere in nome
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "O nome contém caracteres não permitidos."
            ),
        )

    # Evita nomes ambíguos no filesystem do Windows.
    if nome.endswith((".", " ")):
        raise HTTPException(
            status_code=400,
            detail=(
                "O nome não pode terminar com ponto ou espaço."
            ),
        )

    nome_base = (
        nome
        .split(".", 1)[0]
        .upper()
    )

    if nome_base in WINDOWS_RESERVED_NAMES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nome reservado pelo sistema operacional."
            ),
        )

    return nome


def validar_caminho_relativo_workspace(
    relative_path: str,
) -> Path:
    """
    Valida um caminho lógico recebido do Studio.

    Bloqueia:
    - caminho vazio;
    - caminho absoluto;
    - path traversal;
    - UNC;
    - drive Windows;
    - ADS do NTFS;
    - componentes incompatíveis com Windows.

    Retorna um Path relativo já normalizado.
    """

    if not isinstance(relative_path, str):
        raise HTTPException(
            status_code=400,
            detail="Caminho inválido.",
        )

    caminho = (
        relative_path
        .replace("\\", "/")
    )

    if (
        not caminho
        or "\x00" in caminho
    ):
        raise HTTPException(
            status_code=400,
            detail="Caminho inválido.",
        )

    # Não aceitamos caminhos que mudariam semanticamente
    # caso espaços externos fossem removidos.
    if caminho != caminho.strip():
        raise HTTPException(
            status_code=400,
            detail="Caminho inválido.",
        )

    # UNC e caminhos absolutos POSIX.
    if caminho.startswith(("/", "//")):
        raise HTTPException(
            status_code=400,
            detail="Caminho absoluto não permitido.",
        )

    partes = caminho.split("/")

    if any(
        not parte
        or parte in {".", ".."}
        for parte in partes
    ):
        raise HTTPException(
            status_code=400,
            detail="Caminho inválido.",
        )

    for parte in partes:
        validar_componente_workspace(
            parte
        )

    return Path(*partes)


def caminho_eh_link_ou_reparse_point(
    caminho: Path,
) -> bool:
    """
    Detecta objetos do filesystem que podem redirecionar
    uma operação para outro local.

    is_symlink() cobre links simbólicos.

    Em Windows, FILE_ATTRIBUTE_REPARSE_POINT também cobre
    junctions e outros reparse points.
    """

    try:
        if caminho.is_symlink():
            return True

        if os.name == "nt":
            info = caminho.lstat()

            atributos = getattr(
                info,
                "st_file_attributes",
                0,
            )

            reparse_point = getattr(
                stat,
                "FILE_ATTRIBUTE_REPARSE_POINT",
                0x400,
            )

            if atributos & reparse_point:
                return True

    except FileNotFoundError:
        # Um destino novo pode legitimamente ainda não existir.
        return False

    return False


def garantir_sem_redirecionamento_workspace(
    workspace_path: Path,
    destino: Path,
) -> None:
    """
    Verifica todos os componentes existentes entre a raiz
    do Workspace e o destino.

    Nenhum deles pode ser symlink, junction ou outro
    reparse point.
    """

    raiz = workspace_path.resolve()

    # A própria raiz também não pode ser um redirecionamento.
    if caminho_eh_link_ou_reparse_point(
        workspace_path
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Workspace inválido: redirecionamento "
                "de filesystem não permitido."
            ),
        )

    try:
        relativo = destino.relative_to(
            raiz
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Caminho fora do workspace.",
        )

    atual = raiz

    for parte in relativo.parts:
        atual = atual / parte

        if (
            atual.exists()
            or atual.is_symlink()
        ):
            if caminho_eh_link_ou_reparse_point(
                atual
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Links, junctions e outros "
                        "redirecionamentos não são "
                        "permitidos no workspace."
                    ),
                )

def validar_workspace_fisico(
    project_id: int,
    *,
    permitir_inexistente: bool = True,
) -> Path:
    """
    Obtém e valida a raiz física pertencente a um projeto.

    Esta função deve ser utilizada por operações de lifecycle
    que manipulam o Workspace inteiro, como:

    - rollback de criação;
    - exclusão permanente;
    - staging para remoção.

    IMPORTANTE:
    Não cria o Workspace.

    Um Workspace existente jamais pode ser symlink, junction
    ou outro reparse point.
    """

    workspace_path = obter_workspace_path(
        project_id
    )

    if not workspace_path.exists():

        # Um symlink quebrado pode retornar False em exists().
        # Portanto ele precisa ser verificado separadamente.
        if caminho_eh_link_ou_reparse_point(
            workspace_path
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Workspace inválido: redirecionamento "
                    "de filesystem não permitido."
                ),
            )

        if permitir_inexistente:
            return workspace_path

        raise HTTPException(
            status_code=409,
            detail="Workspace do projeto não encontrado.",
        )

    if caminho_eh_link_ou_reparse_point(
        workspace_path
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Workspace inválido: redirecionamento "
                "de filesystem não permitido."
            ),
        )

    if not workspace_path.is_dir():
        raise HTTPException(
            status_code=409,
            detail=(
                "Workspace inválido: o caminho do projeto "
                "não é um diretório."
            ),
        )

    # Confirma que a raiz calculada continua pertencendo ao
    # repositório oficial de Workspaces.
    raiz_repositorio = (
        WORKSPACE_REPOSITORY.resolve()
    )

    workspace_resolvido = (
        workspace_path.resolve()
    )

    try:
        workspace_resolvido.relative_to(
            raiz_repositorio
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=(
                "Workspace fora do repositório permitido."
            ),
        ) from error

    return workspace_path


def remover_workspace_controlado(
    workspace_path: Path,
) -> None:
    """
    Remove uma árvore de Workspace já validada.

    A função se recusa a executar rmtree() quando a própria
    raiz recebida é um symlink/junction/reparse point.

    O conteúdo interno pode conter arquivos normais, mas não
    seguimos uma raiz redirecionada para outro local.
    """

    if not (
        workspace_path.exists()
        or workspace_path.is_symlink()
    ):
        return

    if caminho_eh_link_ou_reparse_point(
        workspace_path
    ):
        raise RuntimeError(
            "Recusa de remoção de Workspace redirecionado."
        )

    if not workspace_path.is_dir():
        raise RuntimeError(
            "Workspace esperado não é um diretório."
        )

    shutil.rmtree(
        workspace_path
    )

# ============================================================
# OBTÉM O WORKSPACE DE UM PROJETO
# ============================================================

def obter_workspace_path(
    project_id: int,
) -> Path:
    """
    Retorna o diretório físico pertencente a um projeto.

    Parâmetros:
        project_id:
            ID do AutomationProject.

    Exemplo:

        project_id = 12

    Retorno:

        RPA-Control-Room/workspaces/12

    Esta função apenas calcula o caminho.

    Ela NÃO cria o diretório.
    """

    return (
        WORKSPACE_REPOSITORY /
        str(project_id)
    )


# ============================================================
# GARANTE A EXISTÊNCIA DO WORKSPACE
# ============================================================

def garantir_workspace(
    project_id: int,
) -> Path:
    """
    Garante que o workspace físico do projeto exista.

    Na primeira criação são inicializados:

        main.py
        requirements.txt
        elements/

    Se o workspace já existir, nenhum arquivo é recriado.

    Isso é importante porque o desenvolvedor pode remover
    intencionalmente algum arquivo padrão durante o trabalho.
    """

    workspace_path = obter_workspace_path(
        project_id
    )

    # --------------------------------------------------------
    # PRIMEIRA INICIALIZAÇÃO
    # --------------------------------------------------------
    #
    # Somente inicializamos a estrutura padrão quando o
    # diretório inteiro do projeto ainda não existe.
    # --------------------------------------------------------

    if not workspace_path.exists():

        workspace_path.mkdir(
            parents=True,
            exist_ok=False,
        )

        # ----------------------------------------------------
        # main.py
        # ----------------------------------------------------

        main_file = (
            workspace_path /
            "main.py"
        )

        main_file.write_text(
            (
                "# ============================================================\n"
                "# DUET CORE - ROBÔ\n"
                "# ============================================================\n"
                "\n"
                "\n"
                "def main():\n"
                "    print(\"DUET CORE - robô iniciado\")\n"
                "\n"
                "\n"
                "if __name__ == \"__main__\":\n"
                "    main()\n"
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # requirements.txt
        # ----------------------------------------------------

        requirements_file = (
            workspace_path /
            "requirements.txt"
        )

        requirements_file.write_text(
            (
                "# Dependências específicas deste robô.\n"
                "# Exemplo:\n"
                "# requests\n"
                "# pandas\n"
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # elements/
        # ----------------------------------------------------

        (
            workspace_path /
            "elements"
        ).mkdir()

    return workspace_path


# ============================================================
# RESOLVE CAMINHO DENTRO DO WORKSPACE
# ============================================================

def resolver_caminho_workspace(
    workspace_path: Path,
    relative_path: str,
) -> Path:
    """
    Resolve um caminho lógico do Studio dentro do Workspace.

    A proteção ocorre em três níveis:

    1. validação sintática do caminho relativo;
    2. confinamento após resolução física;
    3. bloqueio de symlink/junction/reparse point.
    """

    relativo = validar_caminho_relativo_workspace(
        relative_path
    )

    raiz = workspace_path.resolve()

    destino_nao_resolvido = (
        workspace_path /
        relativo
    )

    # Antes de confiar no resolve(), verificamos se algum
    # componente existente tenta redirecionar a operação.
    garantir_sem_redirecionamento_workspace(
        workspace_path,
        destino_nao_resolvido,
    )

    destino = destino_nao_resolvido.resolve()

    try:
        destino.relative_to(
            raiz
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Caminho fora do workspace.",
        )

    return destino
# ============================================================
# VALIDA NOVO NOME DE ITEM
# ============================================================

def validar_nome_item_workspace(
    nome: str,
) -> str:
    """
    Valida o novo nome utilizado pelo rename.

    O rename altera somente o último componente do caminho.
    Movimentação entre diretórios não é permitida aqui.
    """

    if not isinstance(nome, str):
        raise HTTPException(
            status_code=400,
            detail="O novo nome é inválido.",
        )

    novo_nome = nome.strip()

    if not novo_nome:
        raise HTTPException(
            status_code=400,
            detail=(
                "O novo nome não pode ficar vazio."
            ),
        )

    if (
        "/" in novo_nome
        or "\\" in novo_nome
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Informe somente o novo nome do item."
            ),
        )

    return validar_componente_workspace(
        novo_nome
    )

# ============================================================
# MONTA ÁRVORE DO WORKSPACE
# ============================================================

def montar_arvore_workspace(
    raiz: Path,
    diretorio: Path,
) -> list[dict]:
    """
    Percorre o filesystem e monta a árvore utilizada pelo
    Explorer do DUET Studio.

    Parâmetros:
        raiz:
            Raiz física do workspace.

        diretorio:
            Diretório atualmente percorrido.

    Retorno:
        Lista hierárquica contendo arquivos e pastas.

    IMPORTANTE:
        O conteúdo dos arquivos NÃO é carregado aqui.

        Esta função retorna somente os metadados necessários
        para montar o Explorer.

        O conteúdo é carregado posteriormente quando o usuário
        abre explicitamente um arquivo.
    """

    resultado = []

    # Pastas aparecem antes dos arquivos.
    #
    # Dentro de cada grupo utilizamos ordenação alfabética
    # case-insensitive.
    itens = sorted(
        diretorio.iterdir(),
        key=lambda item: (
            not item.is_dir(),
            item.name.lower(),
        ),
    )

    for item in itens:
        # O Explorer não segue links ou junctions.
        #
        # Além de proteger o Control Room, isso evita loops
        # recursivos na montagem da árvore.
        if caminho_eh_link_ou_reparse_point(
            item
        ):
            continue
        relativo = (
            item
            .relative_to(raiz)
            .as_posix()
        )

        # ----------------------------------------------------
        # PASTA
        # ----------------------------------------------------

        if item.is_dir():

            resultado.append({
                "id": relativo,
                "name": item.name,
                "type": "folder",
                "children": montar_arvore_workspace(
                    raiz,
                    item,
                ),
            })

        # ----------------------------------------------------
        # ARQUIVO
        # ----------------------------------------------------

        elif item.is_file():

            resultado.append({
                "id": relativo,
                "name": item.name,
                "type": "file",
            })

    return resultado