# ============================================================
# SERVICE - VAULT FOLDERS
# ============================================================
#
# Responsabilidade:
#
#     Concentrar as regras de negócio relacionadas às
#     pastas do Vault.
#
# Este módulo:
#
#     - valida pasta pai;
#     - cria pastas;
#     - impede exclusão de pasta não vazia;
#     - monta a árvore de pastas;
#     - controla commit/rollback;
#     - registra auditoria operacional sem credenciais.
#
# A autorização RBAC permanece na camada HTTP.
#
# ============================================================

import logging

from sqlalchemy.orm import Session

from schemas.vault import VaultFolderCreateRequest

from vault.folders_repository import (
    buscar_pasta_por_id,
    buscar_primeira_credencial_da_pasta,
    buscar_primeira_subpasta,
    criar_pasta,
    excluir_pasta,
    listar_pastas,
)


# ============================================================
# LOGGER
# ============================================================
#
# Utiliza o logger central do Control Room.
#
# Nenhum segredo ou conteúdo de credencial deve ser escrito
# neste logger.
# ============================================================

logger = logging.getLogger("control_room")


# ============================================================
# CRIAR PASTA
# ============================================================

def criar_pasta_vault_service(
    request: VaultFolderCreateRequest,
    usuario,
    db: Session,
) -> dict:
    """
    Cria uma pasta no Vault.

    Regras preservadas do fluxo atual:

        - parent_id=None cria na raiz;
        - quando parent_id é informado, a pasta pai precisa existir;
        - o nome é normalizado com strip();
        - a criação é persistida em uma única transação.

    A autorização Vault:create NÃO é verificada aqui.
    Essa responsabilidade pertence ao router.
    """

    # --------------------------------------------------------
    # VALIDAR PASTA PAI
    # --------------------------------------------------------

    if request.parent_id is not None:

        pasta_pai = buscar_pasta_por_id(
            db=db,
            folder_id=request.parent_id,
        )

        if not pasta_pai:

            # Mantém o contrato funcional atual.
            return {
                "status": "error",
                "message": "Pasta pai não encontrada.",
            }

    # --------------------------------------------------------
    # NORMALIZAR NOME
    # --------------------------------------------------------

    nome = request.name.strip()

    # --------------------------------------------------------
    # CRIAR OBJETO
    # --------------------------------------------------------

    pasta = criar_pasta(
        db=db,
        nome=nome,
        parent_id=request.parent_id,
    )

    try:

        # O repository somente adiciona o objeto à sessão.
        # O limite transacional permanece no service.
        db.commit()

        db.refresh(
            pasta
        )

    except Exception:

        db.rollback()

        # Não devolvemos str(error) ao cliente nesta camada.
        # A exceção é propagada para o tratamento HTTP/global.
        raise

    # --------------------------------------------------------
    # AUDITORIA
    # --------------------------------------------------------
    #
    # Somente metadados não sensíveis da pasta são registrados.
    # --------------------------------------------------------

    logger.info(
        "[VAULT] Pasta criada | "
        f"Usuário: {usuario.username} | "
        f"ID: {pasta.id} | "
        f"Nome: {pasta.name} | "
        f"Parent ID: {pasta.parent_id}"
    )

    # --------------------------------------------------------
    # RESPOSTA
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": "Pasta criada com sucesso.",
        "folder": {
            "id": pasta.id,
            "name": pasta.name,
            "parent_id": pasta.parent_id,
        },
    }


# ============================================================
# EXCLUIR PASTA
# ============================================================

def excluir_pasta_vault_service(
    folder_id: int,
    usuario,
    db: Session,
) -> dict:
    """
    Exclui uma pasta do Vault.

    Regras:

        - a pasta precisa existir;
        - não pode possuir subpastas;
        - não pode possuir credenciais;
        - exclusão ocorre em uma única transação.

    O service não lê nem registra o conteúdo de credenciais.
    """

    # --------------------------------------------------------
    # BUSCAR PASTA
    # --------------------------------------------------------

    pasta = buscar_pasta_por_id(
        db=db,
        folder_id=folder_id,
    )

    if not pasta:

        # Preserva o contrato atualmente utilizado pela API.
        return {
            "status": "error",
            "message": "Pasta não encontrada.",
        }

    # --------------------------------------------------------
    # VERIFICAR SUBPASTAS
    # --------------------------------------------------------

    subpasta = buscar_primeira_subpasta(
        db=db,
        folder_id=folder_id,
    )

    if subpasta:

        logger.warning(
            "[VAULT] Exclusão de pasta bloqueada | "
            f"ID: {folder_id} | "
            f"Nome: {pasta.name} | "
            f"Motivo: possui subpastas"
        )

        return {
            "status": "error",
            "message": (
                "Não é possível excluir esta pasta "
                "porque ela possui subpastas."
            ),
        }

    # --------------------------------------------------------
    # VERIFICAR CREDENCIAIS
    # --------------------------------------------------------

    credencial = buscar_primeira_credencial_da_pasta(
        db=db,
        folder_id=folder_id,
    )

    if credencial:

        logger.warning(
            "[VAULT] Exclusão de pasta bloqueada | "
            f"ID: {folder_id} | "
            f"Nome: {pasta.name} | "
            f"Motivo: possui credenciais"
        )

        return {
            "status": "error",
            "message": (
                "Não é possível excluir esta pasta "
                "porque ela possui credenciais. "
                "Exclua as credenciais primeiro."
            ),
        }

    # --------------------------------------------------------
    # EXCLUIR
    # --------------------------------------------------------

    nome_pasta = pasta.name

    excluir_pasta(
        db=db,
        pasta=pasta,
    )

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise

    # --------------------------------------------------------
    # AUDITORIA
    # --------------------------------------------------------

    logger.info(
        "[VAULT] Pasta excluída | "
        f"Usuário: {usuario.username} | "
        f"ID: {folder_id} | "
        f"Nome: {nome_pasta}"
    )

    return {
        "status": "success",
        "message": "Pasta excluída com sucesso.",
        "folder": {
            "id": folder_id,
            "name": nome_pasta,
        },
    }


# ============================================================
# LISTAR PASTAS
# ============================================================

def listar_pastas_vault_service(
    db: Session,
) -> dict:
    """
    Retorna a estrutura hierárquica das pastas do Vault.

    O banco retorna uma lista plana e a transformação
    para árvore é realizada nesta camada.
    """

    pastas = listar_pastas(
        db=db
    )

    # --------------------------------------------------------
    # INDEXAR FILHOS POR PARENT_ID
    # --------------------------------------------------------
    #
    # Exemplo:
    #
    # {
    #     None: [Empresa 1, Empresa 2],
    #     10:   [Financeiro, RH],
    # }
    #
    # Isso evita novas consultas ao banco durante a recursão.
    # --------------------------------------------------------

    filhos = {}

    for pasta in pastas:

        parent_id = pasta.parent_id

        if parent_id not in filhos:
            filhos[parent_id] = []

        filhos[parent_id].append(
            pasta
        )

    # --------------------------------------------------------
    # MONTAR ÁRVORE
    # --------------------------------------------------------

    def montar_arvore(
        parent_id: int | None,
    ) -> list[dict]:
        """
        Monta recursivamente os filhos pertencentes
        ao parent_id informado.
        """

        resultado = []

        for pasta in filhos.get(parent_id, []):

            resultado.append(
                {
                    "id": pasta.id,
                    "name": pasta.name,
                    "parent_id": pasta.parent_id,
                    "children": montar_arvore(
                        pasta.id
                    ),
                }
            )

        return resultado

    # parent_id=None representa as pastas raiz.
    arvore = montar_arvore(
        None
    )

    return {
        "status": "success",
        "folders": arvore,
    }