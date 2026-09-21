# ============================================================
# API - VAULT CREDENTIALS
# ============================================================
#
# Camada HTTP do domínio de credenciais do Vault.
#
# Responsabilidades deste arquivo:
#
# - registrar endpoints FastAPI;
# - declarar autenticação;
# - declarar permissões RBAC;
# - receber parâmetros HTTP;
# - delegar regras de negócio aos services.
#
# As regras de negócio foram separadas em:
#
#     vault/master_key_service.py
#     vault/agent_auth.py
#     vault/agent_service.py
#     vault/credentials_service.py
#
# Os contratos Pydantic estão em:
#
#     schemas/vault_credentials.py
#
# IMPORTANTE:
#
# Existem três contextos de segurança diferentes:
#
# 1. /vault/credentials
#       sessão normal de usuário;
#
# 2. /vault/master-key
#       sessão normal + RBAC administrativo;
#
# 3. /vault/agent
#       autenticação técnica por agent_token,
#       SEM get_usuario_atual.
#
# Essa separação deve ser preservada.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)

from auth.dependencies import get_usuario_atual
from auth.permissions import require_permission

from schemas.vault_credentials import (
    VaultCredentialCreateRequest,
    VaultCredentialUpdateRequest,
)

from vault.agent_auth import validar_agent_token

from vault.agent_service import (
    resolver_credencial_agent_service,
)

from vault.credentials_service import (
    criar_credencial_service,
    editar_credencial_service,
    excluir_credencial_service,
    listar_credenciais_service,
)

from vault.master_key_service import (
    exportar_master_key_vault_service,
    importar_master_key_vault_service,
)


# ============================================================
# ROUTER - CREDENCIAIS
# ============================================================
#
# Todas as rotas deste router exigem sessão normal
# de usuário do Control Room.
# ============================================================

router = APIRouter(
    prefix="/vault/credentials",
    tags=["Vault - Credentials"],
    dependencies=[
        Depends(get_usuario_atual)
    ],
)


# ============================================================
# ROUTER - MASTER KEY
# ============================================================
#
# Administração criptográfica da Master Key.
#
# Também exige sessão normal de usuário.
#
# As permissões administrativas específicas permanecem
# declaradas individualmente nos endpoints.
# ============================================================

master_key_router = APIRouter(
    prefix="/vault/master-key",
    tags=["Vault - Master Key"],
    dependencies=[
        Depends(get_usuario_atual)
    ],
)


# ============================================================
# ROUTER - AGENT
# ============================================================
#
# IMPORTANTE:
#
# Este router propositalmente NÃO possui:
#
#     Depends(get_usuario_atual)
#
# O Agent não possui sessão de usuário.
#
# Sua autenticação é realizada através do agent_token.
# ============================================================

agent_router = APIRouter(
    prefix="/vault/agent",
    tags=["Vault - Agent"],
)


# ============================================================
# MASTER KEY - EXPORTAR
# ============================================================

@master_key_router.post(
    "/export",
    summary="Exportar Master Key do Vault",
    description=(
        "Gera um arquivo portátil vault-backup.key contendo "
        "a Master Key do Vault protegida por uma senha de recuperação. "
        "Requer a permissão "
        "'Vault - Control Room:export_master_key'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Vault - Control Room",
                "export_master_key",
            )
        )
    ],
)
def exportar_master_key_vault(
    senha_recuperacao: str = Form(...),
    usuario=Depends(get_usuario_atual),
):
    """
    Endpoint HTTP responsável pela exportação da Master Key.

    A implementação criptográfica e o tratamento operacional
    permanecem no master_key_service.
    """

    return exportar_master_key_vault_service(
        senha_recuperacao=senha_recuperacao,
        usuario=usuario,
    )


# ============================================================
# MASTER KEY - IMPORTAR
# ============================================================

@master_key_router.post(
    "/import",
    summary="Importar Master Key do Vault",
    description=(
        "Importa uma Master Key a partir de um arquivo "
        "vault-backup.key protegido por senha. "
        "Requer a permissão "
        "'Vault - Control Room:import_master_key'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Vault - Control Room",
                "import_master_key",
            )
        )
    ],
)
async def importar_master_key_vault(
    arquivo: UploadFile = File(...),
    senha_recuperacao: str = Form(...),
    usuario=Depends(get_usuario_atual),
):
    """
    Endpoint HTTP responsável pela importação da Master Key.
    """

    return await importar_master_key_vault_service(
        arquivo=arquivo,
        senha_recuperacao=senha_recuperacao,
        usuario=usuario,
    )


# ============================================================
# AGENT - RESOLVER CREDENCIAL
# ============================================================
#
# Não utiliza sessão de usuário.
#
# validar_agent_token() autentica tecnicamente o Agent.
#
# O service utiliza execution_id para identificar o usuário
# humano responsável pela execução e realizar a autorização.
# ============================================================

@agent_router.get(
    "/credentials/{credential_path:path}",
    summary="Resolver Credencial para Agent",
    description=(
        "Permite que um Agent obtenha uma credencial do Vault "
        "utilizando o caminho completo da credencial. "
        "O Agent não precisa conhecer o credential_id. "
        "É necessário informar o execution_id associado à execução "
        "do robô. "
        "A autenticação é realizada através do agent_token."
    ),
)
def resolver_credencial_agent(
    credential_path: str,
    execution_id: int,
    agent=Depends(validar_agent_token),
):
    """
    Resolve uma credencial para uma execução autenticada
    tecnicamente pelo Agent.
    """

    return resolver_credencial_agent_service(
        credential_path=credential_path,
        execution_id=execution_id,
        agent=agent,
    )


# ============================================================
# CREDENCIAIS - CRIAR
# ============================================================

@router.post(
    "",
    summary="Criar Credencial",
    description=(
        "Cria uma nova credencial dentro de uma pasta do Vault. "
        "A credencial é composta por um ou mais campos. "
        "Campos marcados como secretos são armazenados de forma "
        "criptografada. O nome da credencial deve ser único dentro "
        "da pasta informada. "
        "Requer a permissão 'Vault:create'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Vault",
                "create",
            )
        )
    ],
)
def criar_credencial(
    request: VaultCredentialCreateRequest,
    usuario=Depends(get_usuario_atual),
):
    """
    Cria uma credencial no Vault.
    """

    return criar_credencial_service(
        request=request,
        usuario=usuario,
    )


# ============================================================
# CREDENCIAIS - LISTAR
# ============================================================

@router.get(
    "",
    summary="Listar Credenciais",
    description=(
        "Lista as credenciais cadastradas no Vault. "
        "Opcionalmente, é possível informar 'folder_id' para "
        "retornar somente as credenciais pertencentes a uma "
        "determinada pasta. "
        "Valores de campos secretos nunca são retornados em texto "
        "claro e são apresentados como '********'. "
        "Requer a permissão 'Vault:view'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Vault",
                "view",
            )
        )
    ],
)
def listar_credenciais(
    folder_id: int | None = None,
    usuario=Depends(get_usuario_atual),
):
    """
    Lista credenciais do Vault.

    O parâmetro usuario permanece na assinatura para preservar
    o contrato/dependência HTTP existente.
    """

    return listar_credenciais_service(
        folder_id=folder_id,
    )


# ============================================================
# CREDENCIAIS - EDITAR
# ============================================================

@router.put(
    "/{credential_id}",
    summary="Editar Credencial",
    description=(
        "Atualiza os campos de uma credencial existente. "
        "O nome da credencial não pode ser alterado. "
        "Campos secretos podem manter o valor existente utilizando "
        "'keep_existing=true' ou receber um novo valor. "
        "Requer a permissão 'Vault:edit'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Vault",
                "edit",
            )
        )
    ],
)
def editar_credencial(
    credential_id: int,
    request: VaultCredentialUpdateRequest,
    usuario=Depends(get_usuario_atual),
):
    """
    Atualiza os campos pertencentes a uma credencial.
    """

    return editar_credencial_service(
        credential_id=credential_id,
        request=request,
        usuario=usuario,
    )


# ============================================================
# CREDENCIAIS - EXCLUIR
# ============================================================

@router.delete(
    "/{credential_id}",
    summary="Excluir Credencial",
    description=(
        "Exclui uma credencial do Vault. "
        "A operação também remove os campos associados à credencial. "
        "A credencial precisa existir. "
        "Requer a permissão 'Vault:delete'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "Vault",
                "delete",
            )
        )
    ],
)
def excluir_credencial(
    credential_id: int,
    usuario=Depends(get_usuario_atual),
):
    """
    Exclui a credencial e seus respectivos campos.
    """

    return excluir_credencial_service(
        credential_id=credential_id,
        usuario=usuario,
    )