# ============================================================
# ROUTER DE ROBÔS
# ============================================================
# Concentra as APIs relacionadas aos robôs:
#
# - Upload de robôs
# - Exclusão de robôs
# - Criação de pastas
# - Exclusão de pastas
# - Listagem de pastas
# - Listagem de robôs por pasta
#
# As URLs permanecem exatamente iguais às APIs existentes
# no main.py para não quebrar o frontend React.
# ============================================================


# ============================================================
# FASTAPI
# ============================================================
#
# O router continua responsável exclusivamente pela camada HTTP:
#
# - definição das URLs;
# - parâmetros recebidos pela API;
# - autenticação;
# - autorização RBAC.
#
# As regras de negócio foram movidas para os services de Robots.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
)


# ============================================================
# AUTENTICAÇÃO E AUTORIZAÇÃO
# ============================================================

# Identifica o usuário autenticado.
from auth.dependencies import get_usuario_atual

# Valida as permissões RBAC exigidas por cada endpoint.
from auth.permissions import require_permission


# ============================================================
# SCHEMAS
# ============================================================
#
# Contratos HTTP/Pydantic utilizados pelo router.
# ============================================================

from schemas.robots import RobotFolderRequest


# ============================================================
# SERVICES - ROBOTS
# ============================================================
#
# Toda regra de negócio pertence agora aos módulos abaixo.
#
# O api/robots.py apenas recebe a requisição HTTP, aplica RBAC
# e delega a operação para o service correspondente.
# ============================================================

from robots.upload_service import (
    upload_robot_service,
)

from robots.delete_service import (
    delete_robot_service,
)

from robots.folders_service import (
    create_robot_folder_service,
    delete_robot_folder_service,
    list_robot_folders_service,
    list_root_robots_service,
    list_robots_in_folder_service,
)

from robots.version_service import (
    download_robot_service,
    list_robot_version_libraries_service,
)

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["Robots"],
    dependencies=[
        Depends(get_usuario_atual)
    ]
)

# ============================================================
# UPLOAD DE ROBÔ
# ============================================================
#
# Este endpoint recebe o arquivo do robô e realiza o upload
# para o repositório do Control Room.
#
# O upload pode:
#   - criar um novo robô;
#   - atualizar um robô existente;
#   - criar uma nova versão do robô.
#
# Como essa operação altera o repositório de robôs, o usuário
# precisa possuir a permissão:
#
#     Robots:create
#
# O require_permission() verifica a autorização antes que
# a função upload_robot() seja executada.
# ============================================================

@router.post(
    "/robots/upload",
    summary="Enviar robô",
    description=(
        "Envia um arquivo de robô para o repositório do Control Room. "
        "O endpoint pode criar um novo robô, atualizar um robô existente "
        "ou criar uma nova versão quando o arquivo for alterado. "
        "O arquivo deve ser enviado no campo 'file'. "
        "O campo 'folder_id' é opcional e permite associar o robô "
        "a uma pasta específica. "
        "Requer autenticação do usuário e a permissão 'Robots:create'."
    ),
    dependencies=[
        Depends(
            require_permission("Robots", "create")
        )
    ]
)



async def upload_robot(
    file: UploadFile = File(
        ...,
        description="Arquivo do robô. Formatos permitidos: .zip ou .rar."
    ),

    folder_id: int | None = Form(
        None,
        description="ID da pasta onde o robô será armazenado. Opcional."
    ),

    # O usuário continua sendo resolvido pela camada HTTP.
    #
    # O service recebe o usuário já autenticado apenas porque
    # precisa registrar quem publicou a RobotVersion.
    usuario=Depends(
        get_usuario_atual
    )
):
    """
    Recebe o upload HTTP de um Robot e delega a publicação
    para a camada de serviço.

    Responsabilidades deste endpoint:

    - receber o UploadFile;
    - receber a pasta de destino;
    - aplicar autenticação/RBAC;
    - entregar os dados ao service.

    Toda regra de publicação, versionamento, SHA-256,
    persistência e rollback pertence a upload_service.py.
    """

    return await upload_robot_service(
        file=file,
        folder_id=folder_id,
        usuario=usuario,
    )
# ============================================================
# DOWNLOAD DO ROBÔ
# ============================================================

@router.get(
    "/robots/{robot_id}/download",
    summary="Baixar robô",
    dependencies=[
        Depends(require_permission("Robots", "view"))
    ]
)


def download_robot(
    robot_id: int
):
    """
    Baixa a versão atualmente vigente de um Robot.

    A validação da RobotVersion, existência física do artefato
    e integridade SHA-256 pertencem ao version_service.
    """

    return download_robot_service(
        robot_id=robot_id
    )
# ============================================================
# EXCLUSÃO DE ROBÔ
# ============================================================
#
# Este endpoint remove um robô do repositório do Control Room.
#
# Como a operação altera/exclui um recurso de robô, o usuário
# precisa possuir a permissão:
#
#     Robots:delete
#
# A validação acontece antes da execução da função.
# ============================================================

# ============================================================
# EXCLUSÃO DE ROBÔ
# ============================================================
#
# Hard delete controlado.
#
# O Robot somente pode ser excluído quando as dependências
# operacionais bloqueadoras tiverem sido resolvidas.
#
# IMPORTANTE:
#
# - Library usada pela versão atual -> BLOQUEIA;
# - Schedule existente             -> BLOQUEIA;
# - Projeto baseado no Robot       -> BLOQUEIA;
# - LibraryVersion originada dele  -> BLOQUEIA;
#
# Execuções históricas NÃO são apagadas.
#
# Como Execution.robot_id é nullable e Execution já possui
# robot_name / robot_filename, preservamos o histórico apenas
# removendo o vínculo direto com o Robot excluído.
# ============================================================

@router.delete(
    "/robots/{robot_id}",
    summary="Excluir robô",
    description=(
        "Exclui definitivamente um Robot quando não existem "
        "dependências bloqueadoras. "
        "Retorna HTTP 409 com o motivo exato quando a operação "
        "não pode ser realizada."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Robots",
                "delete"
            )
        )
    ]
)


def delete_robot(
    robot_id: int
):
    """
    Solicita o hard delete controlado de um Robot.

    Todas as validações de dependências e a limpeza física
    permanecem centralizadas em delete_service.py.

    Isso inclui:

    - Libraries da versão atual;
    - Schedules;
    - projetos de Desenvolvimento;
    - histórico de Execution;
    - snapshots de Libraries;
    - RobotVersions;
    - limpeza dos artefatos físicos.
    """

    return delete_robot_service(
        robot_id=robot_id
    )
# ============================================================
# EXCLUSÃO DE PASTA DE ROBÔS
# ============================================================
#
# Este endpoint remove uma pasta do repositório de robôs.
#
# Como a operação exclui uma estrutura do repositório, o
# usuário precisa possuir a permissão:
#
#     Robots:delete
#
# A validação do RBAC acontece antes da execução da função.
# ============================================================
@router.delete(
    "/robot-folders/{folder_id}",
    summary="Excluir pasta de robôs",
    description=(
        "Exclui uma pasta de Robôs somente quando ela estiver vazia. "
        "Pastas que possuam Robots ou subpastas retornam HTTP 409."
    ),
    dependencies=[
        Depends(
            require_permission("Robots", "delete")
        )
    ]
)
def delete_robot_folder(
    folder_id: int
):
    """
    Exclui uma pasta de Robots através da camada de serviço.

    O service preserva as regras atuais:

    - pasta inexistente -> HTTP 404;
    - pasta com Robots -> HTTP 409;
    - pasta com subpastas -> HTTP 409;
    - somente pasta vazia pode ser excluída.
    """

    return delete_robot_folder_service(
        folder_id=folder_id
    )


# ============================================================
# CRIAÇÃO DE PASTA DE ROBÔS
# ============================================================
#
# Este endpoint cria uma nova pasta no repositório de robôs.
#
# Como a criação altera a estrutura do repositório, o usuário
# precisa possuir a permissão:
#
#     Robots:create
#
# O require_permission() bloqueia a chamada com HTTP 403
# antes que a função seja executada caso o usuário não tenha
# essa permissão.
# ============================================================

@router.post(
    "/robot-folders",
    summary="Criar pasta de robôs",
    description=(
        "Cria uma nova pasta no repositório de robôs. "
        "A pasta pode ser criada na raiz ou dentro de outra pasta "
        "utilizando o campo 'parent_id'. "
        "Requer autenticação do usuário e a permissão 'Robots:create'."
    ),
    dependencies=[
        Depends(
            require_permission("Robots", "create")
        )
    ]
)


def create_robot_folder(
    request: RobotFolderRequest
):
    """
    Recebe os dados HTTP da nova pasta e delega sua criação
    para folders_service.py.

    A validação de nome, parent_id, duplicidade e persistência
    pertence ao service.
    """

    return create_robot_folder_service(
        request=request
    )
# ============================================================
# LISTAR PASTAS DE ROBÔS
# ============================================================

# ============================================================
# LISTAGEM DE PASTAS DE ROBÔS
# ============================================================
#
# Este endpoint consulta as pastas existentes no repositório
# de robôs.
#
# Como é uma operação de consulta, o usuário precisa possuir
# a permissão:
#
#     Robots:view
#
# O require_permission() valida a autorização antes de
# executar a função.
# ============================================================

@router.get(
    "/robot-folders",
    summary="Listar pastas de robôs",
    description=(
        "Retorna todas as pastas cadastradas no repositório de robôs. "
        "A resposta apresenta o identificador, nome e pasta pai "
        "de cada pasta. "
        "Requer autenticação do usuário e a permissão 'Robots:view'."
    ),
    dependencies=[
        Depends(
            require_permission("Robots", "view")
        )
    ]
)

def list_robot_folders():
    """
    Lista as pastas existentes no repositório de Robots.

    A consulta ao banco pertence ao folders_service.
    """

    return list_robot_folders_service()
# ============================================================
# LISTAR ROBÔS DA RAIZ
# ============================================================
#
# A "Raiz de Robôs" não é uma RobotFolder cadastrada no banco.
#
# Ela representa os Robots cujo:
#
#     folder_id = NULL
#
# Esse endpoint permite que o frontend trate a raiz como uma
# localização navegável, sem criar uma pasta artificial no banco.
# ============================================================

@router.get(
    "/robots/root",
    summary="Listar robôs da raiz",
    description=(
        "Retorna os robôs publicados diretamente na Raiz de Robôs, "
        "ou seja, registros cujo folder_id é nulo. "
        "Requer a permissão 'Robots:view'."
    ),
    dependencies=[
        Depends(
            require_permission("Robots", "view")
        )
    ]
)


def list_root_robots():
    """
    Lista somente os Robots publicados diretamente na raiz.

    A raiz representa:

        Robot.folder_id IS NULL

    A consulta ao banco pertence ao folders_service.
    """

    return list_root_robots_service()
# ============================================================
# BIBLIOTECAS UTILIZADAS POR UMA VERSÃO DO ROBOT
# ============================================================
#
# Cada Release do DUET registra um snapshot imutável contendo
# as versões EXATAS das bibliotecas utilizadas pelo Robot.
#
# Exemplo:
#
#     SERV v1
#         lib2 -> 2.0.0
#         lib3 -> 1.0.0
#         nova -> 1.0.0
#
# Mesmo que futuramente lib2 chegue à versão 5.0.0,
# este endpoint continuará retornando 2.0.0 para SERV v1.
# ============================================================

@router.get(
    "/robots/{robot_id}/versions/{robot_version}/libraries",
    summary="Listar bibliotecas de uma versão do robô",
    description=(
        "Retorna o snapshot exato das bibliotecas utilizadas "
        "por uma versão publicada do Robot."
    ),
    dependencies=[
        Depends(
            require_permission("Robots", "view")
        )
    ]
)


def list_robot_version_libraries(
    robot_id: int,
    robot_version: int
):
    """
    Retorna o snapshot imutável das Libraries utilizadas
    por uma RobotVersion específica.

    A validação da RobotVersion e a consulta das dependências
    pertencem ao version_service.
    """

    return list_robot_version_libraries_service(
        robot_id=robot_id,
        robot_version=robot_version,
    )


# ============================================================
# LISTAR ROBÔS DE UMA PASTA
# ============================================================
#
# Este endpoint consulta os robôs existentes dentro de uma
# determinada pasta do repositório.
#
# Como é uma operação de consulta, o usuário precisa possuir
# a permissão:
#
#     Robots:view
#
# O require_permission() valida a autorização antes de
# executar a função.
# ============================================================

@router.get(
    "/robot-folders/{folder_id}/robots",
    summary="Listar robôs de uma pasta",
    description=(
        "Retorna os robôs pertencentes a uma pasta específica. "
        "A pasta é identificada pelo parâmetro 'folder_id'. "
        "A resposta contém informações dos robôs, incluindo "
        "identificador, nome, arquivo, versão, hash e caminho. "
        "Requer autenticação do usuário e a permissão 'Robots:view'."
    ),

    # A listagem dos Robots de uma pasta é uma operação de
    # leitura do domínio Robots. Portanto, além da autenticação
    # global do router, exige autorização RBAC explícita.
    dependencies=[
        Depends(
            require_permission("Robots", "view")
        )
    ]
)

def list_robots_in_folder(
    folder_id: int
):
    """
    Lista os Robots pertencentes à pasta informada.

    A localização da pasta e a consulta dos Robots pertencem
    ao folders_service.
    """

    return list_robots_in_folder_service(
        folder_id=folder_id
    )