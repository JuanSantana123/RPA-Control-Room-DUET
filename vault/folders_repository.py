# ============================================================
# REPOSITORY - VAULT FOLDERS
# ============================================================
#
# Responsabilidade:
#
#     Centralizar todas as operações de persistência
#     relacionadas às pastas do Vault.
#
# Este módulo NÃO:
#
#     - conhece FastAPI;
#     - verifica RBAC;
#     - monta respostas HTTP;
#     - executa commit;
#     - executa rollback.
#
# O limite transacional pertence ao service.
#
# ============================================================

from sqlalchemy.orm import Session

from models import (
    VaultCredential,
    VaultFolder,
)


# ============================================================
# BUSCAR PASTA
# ============================================================

def buscar_pasta_por_id(
    db: Session,
    folder_id: int,
) -> VaultFolder | None:
    """
    Busca uma pasta do Vault pelo identificador interno.

    Parâmetros:

        db:
            Sessão SQLAlchemy da operação.

        folder_id:
            Identificador da pasta.

    Retorno:

        VaultFolder:
            quando a pasta existe.

        None:
            quando a pasta não existe.
    """

    return (
        db.query(VaultFolder)
        .filter(
            VaultFolder.id == folder_id
        )
        .first()
    )


# ============================================================
# LISTAR PASTAS
# ============================================================

def listar_pastas(
    db: Session,
) -> list[VaultFolder]:
    """
    Retorna todas as pastas do Vault ordenadas pelo nome.

    A montagem da árvore NÃO pertence ao repository.
    """

    return (
        db.query(VaultFolder)
        .order_by(
            VaultFolder.name
        )
        .all()
    )


# ============================================================
# VERIFICAR SUBPASTAS
# ============================================================

def buscar_primeira_subpasta(
    db: Session,
    folder_id: int,
) -> VaultFolder | None:
    """
    Verifica se determinada pasta possui pelo menos
    uma subpasta.

    Não carregamos todas as subpastas porque, para a regra
    de exclusão, precisamos apenas saber se alguma existe.
    """

    return (
        db.query(VaultFolder)
        .filter(
            VaultFolder.parent_id == folder_id
        )
        .first()
    )


# ============================================================
# VERIFICAR CREDENCIAIS
# ============================================================

def buscar_primeira_credencial_da_pasta(
    db: Session,
    folder_id: int,
) -> VaultCredential | None:
    """
    Verifica se determinada pasta possui pelo menos
    uma credencial associada.

    O conteúdo da credencial não é lido nem retornado.
    """

    return (
        db.query(VaultCredential)
        .filter(
            VaultCredential.folder_id == folder_id
        )
        .first()
    )


# ============================================================
# CRIAR PASTA
# ============================================================

def criar_pasta(
    db: Session,
    nome: str,
    parent_id: int | None,
) -> VaultFolder:
    """
    Cria uma nova instância VaultFolder e adiciona
    o objeto à sessão SQLAlchemy.

    IMPORTANTE:

        Esta função NÃO executa commit.

        A transação permanece sob responsabilidade
        de vault/folders_service.py.
    """

    pasta = VaultFolder(
        name=nome,
        parent_id=parent_id,
    )

    db.add(
        pasta
    )

    return pasta


# ============================================================
# EXCLUIR PASTA
# ============================================================

def excluir_pasta(
    db: Session,
    pasta: VaultFolder,
) -> None:
    """
    Marca uma pasta para exclusão na sessão SQLAlchemy.

    NÃO executa commit.
    """

    db.delete(
        pasta
    )