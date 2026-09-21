# ============================================================
# ROUTER DO VAULT
# ============================================================
#
# Responsável pelas pastas do Vault.
#
# Estrutura:
#
# Credenciais
# ├── Empresa 1
# │   ├── Financeiro
# │   └── RH
# └── Empresa 2
#     └── SAP
#
# As credenciais serão implementadas posteriormente.
# ============================================================

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from database import SessionLocal

from auth.dependencies import get_usuario_atual
from auth.permissions import require_permission

# Contrato HTTP utilizado na criação de pastas do Vault.
from schemas.vault import VaultFolderCreateRequest

# Services responsáveis pelas regras de negócio das pastas.
from vault.folders_service import (
    criar_pasta_vault_service,
    excluir_pasta_vault_service,
    listar_pastas_vault_service,
)

# ============================================================
# DEPENDÊNCIA DO BANCO
# ============================================================

def get_db():
    """
    Abre uma sessão SQLAlchemy para a requisição HTTP.

    A sessão é compartilhada com o service chamado pelo endpoint
    e sempre é fechada ao término do processamento.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/vault",
    tags=["Vault"],
    dependencies=[
        Depends(get_usuario_atual)
    ]
)


# ============================================================
# CRIAR PASTA DO VAULT
# ============================================================

@router.post(
    "/folders",
    summary="Criar Pasta Vault",
    description=(
        "Cria uma nova pasta no Vault. "
        "A pasta pode ser criada na raiz do Vault ou dentro "
        "de uma pasta existente através do parâmetro 'parent_id'. "
        "O nome da pasta é obrigatório. "
        "Requer a permissão 'Vault:create'."
    ),
)
def criar_pasta_vault(
    request: VaultFolderCreateRequest,

    # A sessão pertence ao ciclo de vida da requisição.
    db: Session = Depends(get_db),

    # Criar estrutura dentro do Vault exige explicitamente
    # a permissão RBAC Vault:create.
    usuario=Depends(
        require_permission(
            "Vault",
            "create",
        )
    ),
):
    """
    Cria uma nova pasta no Vault.

    Responsabilidades deste endpoint:

        - receber e validar o contrato HTTP;
        - exigir Vault:create;
        - delegar a regra de negócio ao service.

    Persistência e transação permanecem fora do router.
    """

    return criar_pasta_vault_service(
        request=request,
        usuario=usuario,
        db=db,
    )
# EXCLUIR PASTA DO VAULT
# ============================================================
#
# Além da autenticação normal do usuário, este endpoint exige
# explicitamente a permissão RBAC:
#
#     Vault:delete
#
# A verificação interna de "can_delete" continua temporariamente
# porque ela agora utiliza o mesmo RBAC genérico.
# ============================================================


# ============================================================
# EXCLUIR PASTA DO VAULT
# ============================================================

@router.delete(
    "/folders/{folder_id}",
    summary="Excluir Pasta Vault",
    description=(
        "Exclui uma pasta do Vault. "
        "A pasta somente poderá ser excluída quando estiver vazia. "
        "Não é permitido excluir uma pasta que possua subpastas "
        "ou credenciais associadas. "
        "É necessário informar o ID da pasta. "
        "Requer a permissão 'Vault:delete'."
    ),
)
def excluir_pasta_vault(
    folder_id: int,

    # Sessão utilizada pelo service durante toda a operação.
    db: Session = Depends(get_db),

    # Exclusão de estrutura do Vault exige Vault:delete.
    usuario=Depends(
        require_permission(
            "Vault",
            "delete",
        )
    ),
):
    """
    Exclui uma pasta vazia do Vault.

    O endpoint não executa consultas nem controla transações.
    """

    return excluir_pasta_vault_service(
        folder_id=folder_id,
        usuario=usuario,
        db=db,
    )
# ============================================================
# LISTAR PASTAS DO VAULT
# ============================================================
#
# Além de exigir um usuário autenticado, este endpoint exige
# explicitamente a permissão RBAC:
#
#     Vault:view
#
# A autorização passa a ficar declarada diretamente no
# endpoint, seguindo o mesmo padrão utilizado pelos demais
# módulos do Control Room.
# ============================================================

# ============================================================
# LISTAR PASTAS DO VAULT
# ============================================================

@router.get(
    "/folders",
    summary="Listar Pastas Vault",
    description=(
        "Retorna a estrutura hierárquica das pastas do Vault. "
        "As pastas são organizadas em uma árvore utilizando "
        "o relacionamento entre 'id' e 'parent_id'. "
        "Requer a permissão 'Vault:view'."
    ),
)
def listar_pastas_vault(
    # Sessão utilizada para consultar a estrutura do Vault.
    db: Session = Depends(get_db),

    # Visualização da estrutura exige Vault:view.
    usuario=Depends(
        require_permission(
            "Vault",
            "view",
        )
    ),
):
    """
    Lista a árvore de pastas do Vault.

    O service recebe a lista plana do repository e monta
    a estrutura hierárquica devolvida pela API.
    """

    return listar_pastas_vault_service(
        db=db
    )