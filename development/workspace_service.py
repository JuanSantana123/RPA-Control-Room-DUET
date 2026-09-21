# ============================================================
# DEVELOPMENT - WORKSPACE SERVICE
# ============================================================
#
# Responsável pelas operações do Explorer/Studio sobre o
# Workspace físico de um AutomationProject.
#
# Este módulo concentra:
#
# - árvore de arquivos;
# - abertura de arquivo;
# - salvamento;
# - criação de arquivo;
# - criação de pasta;
# - renomeação;
# - exclusão.
#
# REGRAS IMPORTANTES:
#
# - operações de escrita exigem Checkout;
# - paths são sempre resolvidos dentro do Workspace;
# - main.py continua protegido como entrypoint;
# - _libraries possui regras próprias de proteção;
# - leitura de arquivos pelo Studio aceita somente UTF-8.
#
# Este módulo NÃO registra endpoints FastAPI, não utiliza
# Depends e não aplica RBAC.
# ============================================================

import logging
import os
import shutil
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import AutomationProject

from development.workspace_core import (
    ensure_drafts,
    protect_draft_root,
    protect_draft_container_creation,
)

from development.checkout_service import (
    exigir_checkout_workspace,
)

from development.repository import (
    garantir_workspace,
    resolver_caminho_workspace,
    validar_nome_item_workspace,
    montar_arvore_workspace,
)

from schemas.development import (
    WorkspaceFileSave,
    WorkspaceItemCreate,
    WorkspaceItemRename,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# LISTAR ÁRVORE DO WORKSPACE
# ============================================================

def listar_workspace_service(
    project_id: int,
    db: Session,
) -> dict:
    """
    Retorna a estrutura de arquivos e pastas do projeto.

    O conteúdo dos arquivos não é carregado nesta operação.
    """

    # ========================================================
    # PROJETO
    # ========================================================

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
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # WORKSPACE
    # ========================================================

    workspace_path = garantir_workspace(
        project_id
    )

    # Garante as Working Copies necessárias das Libraries
    # vinculadas ao projeto antes de montar a árvore.
    ensure_drafts(
        db,
        project_id,
    )

    return {
        "status": "success",
        "project_id": project_id,

        "tree":
            montar_arvore_workspace(
                workspace_path,
                workspace_path,
            ),
    }


# ============================================================
# ABRIR ARQUIVO
# ============================================================

def abrir_arquivo_workspace_service(
    project_id: int,
    path: str,
    db: Session,
) -> dict:
    """
    Carrega somente o arquivo solicitado pelo Studio.

    Arquivos não textuais ou não codificados em UTF-8
    não são disponibilizados para edição textual.
    """

    # ========================================================
    # PROJETO
    # ========================================================

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
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # RESOLVE ARQUIVO
    # ========================================================

    workspace_path = garantir_workspace(
        project_id
    )

    arquivo_path = resolver_caminho_workspace(
        workspace_path,
        path,
    )

    if not arquivo_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Arquivo não encontrado.",
        )

    if not arquivo_path.is_file():

        raise HTTPException(
            status_code=400,
            detail=(
                "O caminho informado não é um arquivo."
            ),
        )

    # ========================================================
    # LEITURA UTF-8
    # ========================================================

    try:

        conteudo = arquivo_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        raise HTTPException(
            status_code=415,
            detail=(
                "Este arquivo não é um arquivo textual "
                "UTF-8 editável pelo Studio."
            ),
        )

    return {
        "status": "success",
        "project_id": project_id,
        "path": path,
        "content": conteudo,
    }


# ============================================================
# SALVAR ARQUIVO
# ============================================================

def salvar_arquivo_workspace_service(
    project_id: int,
    request: WorkspaceFileSave,
    db: Session,
    usuario,
) -> dict:
    """
    Salva o conteúdo de um arquivo textual existente.

    Somente o arquivo informado é atualizado.
    """

    # ========================================================
    # PROJETO
    # ========================================================

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
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT
    # ========================================================

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    # ========================================================
    # ARQUIVO
    # ========================================================

    workspace_path = garantir_workspace(
        project_id
    )

    arquivo_path = resolver_caminho_workspace(
        workspace_path,
        request.path,
    )

    if not arquivo_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Arquivo não encontrado.",
        )

    if not arquivo_path.is_file():

        raise HTTPException(
            status_code=400,
            detail=(
                "O caminho informado não é um arquivo."
            ),
        )

    # ========================================================
    # SALVA
    # ========================================================

    try:

        # A gravação ocorre primeiro em um arquivo temporário
        # único no MESMO diretório do arquivo oficial.
        #
        # Dessa forma os.replace() pode efetuar a troca final
        # atomicamente no mesmo filesystem.
        arquivo_temporario = (
            arquivo_path.parent /
            (
                f".{arquivo_path.name}."
                f"{uuid4().hex}.duet_tmp"
            )
        )

        try:
            with arquivo_temporario.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as arquivo:
                arquivo.write(
                    request.content
                )

                arquivo.flush()

                # Força os bytes do arquivo temporário para
                # o filesystem antes da substituição.
                os.fsync(
                    arquivo.fileno()
                )

            os.replace(
                arquivo_temporario,
                arquivo_path,
            )

        finally:
            # Se qualquer etapa anterior ao replace falhar,
            # não deixamos lixo temporário no Workspace.
            if arquivo_temporario.exists():
                arquivo_temporario.unlink()

        logger.info(
            "Arquivo do workspace salvo",
            extra={
                "event":
                    "workspace_file_saved",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "workspace_path":
                    request.path,

                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message":
                "Arquivo salvo com sucesso.",

            "project_id":
                project_id,

            "path":
                request.path,
        }

    except Exception as error:

        logger.exception(
            "Falha ao salvar arquivo do workspace",
            extra={
                "event":
                    "workspace_file_save_failed",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "workspace_path":
                    request.path,

                "status":
                    "error",

                "error_type":
                    type(error).__name__,

                "error_message":
                    str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível salvar o arquivo."
            ),
        )


# ============================================================
# CRIAR ARQUIVO
# ============================================================

def criar_arquivo_workspace_service(
    project_id: int,
    request: WorkspaceItemCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Cria um arquivo vazio dentro do Workspace.
    """

    # ========================================================
    # PROJETO
    # ========================================================

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
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT
    # ========================================================

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    workspace_path = garantir_workspace(
        project_id
    )

    # ========================================================
    # PROTEÇÃO DAS LIBRARIES
    # ========================================================
    #
    # O namespace principal de uma Library somente pode ser
    # criado pela gestão de Libraries.
    #
    # Arquivos internos de uma Library continuam permitidos.
    # ========================================================

    protect_draft_container_creation(
        request.path
    )

    arquivo_path = resolver_caminho_workspace(
        workspace_path,
        request.path,
    )

    # ========================================================
    # VALIDAÇÕES
    # ========================================================

    if arquivo_path.exists():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um arquivo ou pasta nesse caminho."
            ),
        )

    if not arquivo_path.parent.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "A pasta de destino não existe."
            ),
        )

    # ========================================================
    # CRIA
    # ========================================================

    arquivo_path.touch(
        exist_ok=False
    )

    return {
        "status": "success",
        "message":
            "Arquivo criado com sucesso.",

        "project_id":
            project_id,

        "path":
            request.path,
    }


# ============================================================
# CRIAR PASTA
# ============================================================

def criar_pasta_workspace_service(
    project_id: int,
    request: WorkspaceItemCreate,
    db: Session,
    usuario,
) -> dict:
    """
    Cria uma pasta dentro do Workspace.
    """

    # ========================================================
    # PROJETO
    # ========================================================

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
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT
    # ========================================================

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    workspace_path = garantir_workspace(
        project_id
    )

    # ========================================================
    # PROTEÇÃO DAS LIBRARIES
    # ========================================================
    #
    # _libraries e seus namespaces imediatos são gerenciados
    # pelo DUET.
    #
    # Subpastas dentro da Library são permitidas.
    # ========================================================

    protect_draft_container_creation(
        request.path
    )

    pasta_path = resolver_caminho_workspace(
        workspace_path,
        request.path,
    )

    # ========================================================
    # VALIDAÇÕES
    # ========================================================

    if pasta_path.exists():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um arquivo ou pasta nesse caminho."
            ),
        )

    if not pasta_path.parent.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "A pasta de destino não existe."
            ),
        )

    # ========================================================
    # CRIA
    # ========================================================

    pasta_path.mkdir(
        exist_ok=False
    )

    return {
        "status": "success",
        "message":
            "Pasta criada com sucesso.",

        "project_id":
            project_id,

        "path":
            request.path,
    }


# ============================================================
# RENOMEAR ITEM
# ============================================================

def renomear_item_workspace_service(
    project_id: int,
    request: WorkspaceItemRename,
    db: Session,
    usuario,
) -> dict:
    """
    Renomeia um arquivo ou pasta existente.

    O item permanece no mesmo diretório.
    """

    # ========================================================
    # PROJETO
    # ========================================================

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
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT
    # ========================================================

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    workspace_path = garantir_workspace(
        project_id
    )

    # ========================================================
    # PROTEÇÃO DA RAIZ DE UMA WORKING COPY
    # ========================================================

    protect_draft_root(
        request.path,
        db,
        project_id,
    )

    item_path = resolver_caminho_workspace(
        workspace_path,
        request.path,
    )

    raiz = workspace_path.resolve()

    # ========================================================
    # PROTEGE RAIZ DO WORKSPACE
    # ========================================================

    if item_path == raiz:

        raise HTTPException(
            status_code=400,
            detail=(
                "A raiz do workspace não pode ser renomeada."
            ),
        )

    if not item_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Arquivo ou pasta não encontrado."
            ),
        )

    # ========================================================
    # CAMINHO RELATIVO ATUAL
    # ========================================================

    caminho_relativo_atual = (
        item_path
        .relative_to(
            raiz
        )
        .as_posix()
    )

    # ========================================================
    # PROTEGE MAIN.PY
    # ========================================================
    #
    # main.py é o entrypoint utilizado pela arquitetura atual
    # de execução dos Robots.
    # ========================================================

    if caminho_relativo_atual == "main.py":

        raise HTTPException(
            status_code=400,
            detail=(
                "O arquivo main.py é o ponto de entrada "
                "do robô e não pode ser renomeado."
            ),
        )

    # ========================================================
    # NOVO NOME
    # ========================================================

    novo_nome = validar_nome_item_workspace(
        request.new_name
    )

    novo_path = (
        item_path.parent /
        novo_nome
    ).resolve()

    # ========================================================
    # SEGURANÇA DO DESTINO
    # ========================================================

    if (
        novo_path != raiz
        and raiz not in novo_path.parents
    ):

        raise HTTPException(
            status_code=400,
            detail="Destino fora do workspace.",
        )

    if novo_path.exists():

        raise HTTPException(
            status_code=409,
            detail=(
                "Já existe um arquivo ou pasta "
                "com esse nome neste local."
            ),
        )

    tipo_item = (
        "folder"
        if item_path.is_dir()
        else "file"
    )

    # ========================================================
    # RENOMEIA
    # ========================================================

    try:

        item_path.rename(
            novo_path
        )

        novo_caminho_relativo = (
            novo_path
            .relative_to(
                raiz
            )
            .as_posix()
        )

        logger.info(
            "Item do workspace renomeado",
            extra={
                "event":
                    "workspace_item_renamed",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "old_path":
                    caminho_relativo_atual,

                "new_path":
                    novo_caminho_relativo,

                "item_type":
                    tipo_item,

                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message":
                "Item renomeado com sucesso.",

            "project_id":
                project_id,

            "type":
                tipo_item,

            "old_path":
                caminho_relativo_atual,

            "new_path":
                novo_caminho_relativo,
        }

    except HTTPException:
        raise

    except Exception as error:

        logger.exception(
            "Falha ao renomear item do workspace",
            extra={
                "event":
                    "workspace_item_rename_failed",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "workspace_path":
                    caminho_relativo_atual,

                "status":
                    "error",

                "error_type":
                    type(error).__name__,

                "error_message":
                    str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível renomear "
                "o arquivo ou pasta."
            ),
        )


# ============================================================
# EXCLUIR ITEM
# ============================================================

def excluir_item_workspace_service(
    project_id: int,
    path: str,
    recursive: bool,
    db: Session,
    usuario,
) -> dict:
    """
    Exclui arquivo ou pasta do Workspace.

    recursive=False:
        pastas somente podem ser removidas quando vazias.

    recursive=True:
        permite remover a pasta e todo seu conteúdo.

    O frontend deve solicitar confirmação explícita antes
    de utilizar exclusão recursiva.
    """

    # ========================================================
    # PROJETO
    # ========================================================

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
            detail="Projeto não encontrado.",
        )

    # ========================================================
    # CHECKOUT
    # ========================================================

    exigir_checkout_workspace(
        project_id=project_id,
        user_id=usuario.id,
        db=db,
    )

    workspace_path = garantir_workspace(
        project_id
    )

    # ========================================================
    # PROTEÇÃO DA WORKING COPY
    # ========================================================

    protect_draft_root(
        path,
        db,
        project_id,
    )

    item_path = resolver_caminho_workspace(
        workspace_path,
        path,
    )

    raiz = workspace_path.resolve()

    # ========================================================
    # PROTEGE RAIZ DO WORKSPACE
    # ========================================================

    if item_path == raiz:

        raise HTTPException(
            status_code=400,
            detail=(
                "A raiz do workspace não pode ser excluída."
            ),
        )

    if not item_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Arquivo ou pasta não encontrado."
            ),
        )

    # ========================================================
    # CAMINHO RELATIVO
    # ========================================================

    caminho_relativo = (
        item_path
        .relative_to(
            raiz
        )
        .as_posix()
    )

    # ========================================================
    # PROTEGE MAIN.PY
    # ========================================================

    if caminho_relativo == "main.py":

        raise HTTPException(
            status_code=400,
            detail=(
                "O arquivo main.py é o ponto de entrada "
                "do robô e não pode ser excluído."
            ),
        )

    tipo_item = (
        "folder"
        if item_path.is_dir()
        else "file"
    )

    # ========================================================
    # EXCLUSÃO
    # ========================================================

    try:

        # ----------------------------------------------------
        # ARQUIVO
        # ----------------------------------------------------

        if item_path.is_file():

            item_path.unlink()

        # ----------------------------------------------------
        # PASTA
        # ----------------------------------------------------

        elif item_path.is_dir():

            possui_conteudo = any(
                item_path.iterdir()
            )

            if (
                possui_conteudo
                and not recursive
            ):

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A pasta não está vazia. "
                        "Confirme a exclusão recursiva "
                        "para remover todo o conteúdo."
                    ),
                )

            if recursive:

                shutil.rmtree(
                    item_path
                )

            else:

                item_path.rmdir()

        # ----------------------------------------------------
        # OUTRO TIPO
        # ----------------------------------------------------

        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Tipo de item não suportado."
                ),
            )

        # ====================================================
        # AUDITORIA
        # ====================================================

        logger.info(
            "Item do workspace excluído",
            extra={
                "event":
                    "workspace_item_deleted",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "workspace_path":
                    caminho_relativo,

                "item_type":
                    tipo_item,

                "recursive":
                    recursive,

                "status":
                    "success",
            },
        )

        return {
            "status": "success",
            "message":
                "Item excluído com sucesso.",

            "project_id":
                project_id,

            "type":
                tipo_item,

            "path":
                caminho_relativo,
        }

    except HTTPException:
        raise

    except Exception as error:

        logger.exception(
            "Falha ao excluir item do workspace",
            extra={
                "event":
                    "workspace_item_delete_failed",

                "user_id":
                    usuario.id,

                "project_id":
                    project_id,

                "workspace_path":
                    caminho_relativo,

                "status":
                    "error",

                "error_type":
                    type(error).__name__,

                "error_message":
                    str(error),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível excluir "
                "o arquivo ou pasta."
            ),
        )