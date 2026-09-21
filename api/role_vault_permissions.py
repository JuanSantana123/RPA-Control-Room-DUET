# ============================================================
# API - ROLE VAULT PERMISSIONS
# ============================================================
#
# Camada HTTP responsável pelas rotas de compatibilidade para
# configuração das permissões do Vault associadas às Roles.
#
# RESPONSABILIDADES DESTE ARQUIVO:
#
# - registrar as rotas HTTP;
# - validar a sessão do usuário;
# - receber e validar os parâmetros HTTP;
# - fornecer a sessão de banco;
# - delegar a regra de negócio ao service.
#
# A consulta ao banco e a manipulação de RolePermission não
# ficam mais implementadas diretamente no router.
#
# IMPORTANTE:
#
# Nesta etapa estamos preservando exatamente o modelo de
# autenticação/autorização existente no arquivo original.
#
# A revisão de segurança dessas rotas será realizada somente
# depois da comprovação de equivalência.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from database import SessionLocal

# Dependência responsável por validar a sessão do usuário.
from auth.dependencies import get_usuario_atual


# ============================================================
# AUTORIZAÇÃO RBAC
# ============================================================
#
# As rotas deste módulo consultam ou alteram permissões
# associadas a Roles.
#
# Utilizamos as mesmas permissões administrativas já adotadas
# pelo domínio principal de Roles:
#
#     consulta            -> Roles:view
#     alteração de RBAC   -> Roles:edit
#
# Isso impede que um usuário apenas autenticado utilize este
# endpoint legado como caminho alternativo para modificar
# RolePermission.
# ============================================================

from auth.permissions import require_permission
# Contrato HTTP utilizado pelo POST e PUT.
from schemas.role_vault_permissions import (
    RoleVaultPermissionRequest,
)

# Regras de negócio do domínio.
from role_vault_permissions.service import (
    configurar_permissoes_role_service,
    consultar_permissoes_role_service,
    alterar_permissoes_role_service,
)


# ============================================================
# DEPENDÊNCIA DO BANCO
# ============================================================

def get_db():
    """
    Abre uma sessão SQLAlchemy para a requisição.

    A sessão é sempre encerrada no finally, inclusive quando
    o endpoint ou o service gera uma exceção.
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
    prefix="/role-vault-permissions",
    tags=["Role Vault Permissions"],
)


# ============================================================
# CONFIGURAR PERMISSÕES DA ROLE
# ============================================================

@router.post(
    "/roles/{role_id}",
    summary="Configurar Permissões da Role",
    description=(
        "Configura as permissões do Vault para uma Role. "
        "As permissões disponíveis são Vault:view, Vault:create, "
        "Vault:edit, Vault:delete e Vault:use. "
        "As permissões marcadas como True serão vinculadas à Role "
        "e as marcadas como False não serão vinculadas. "
        "Requer autenticação do usuário."
    ),
)
def configurar_permissoes_role(
    role_id: int,
    dados: RoleVaultPermissionRequest,
    db: Session = Depends(get_db),

    # Além de estar autenticado, o usuário precisa possuir
    # autorização administrativa para editar Roles.
    #
    # Isso protege a criação/remoção de RolePermission.
    usuario=Depends(
        require_permission(
            "Roles",
            "edit",
        )
    ),
):
    """
    Configura as permissões do Vault para uma Role.

    A autenticação continua sendo realizada pela dependency
    get_usuario_atual, preservando o contrato original.
    """

    return configurar_permissoes_role_service(
        role_id=role_id,
        dados=dados,
        db=db,
    )


# ============================================================
# CONSULTAR PERMISSÕES DA ROLE
# ============================================================

@router.get(
    "/roles/{role_id}",
    summary="Consultar Permissões da Role",
    description=(
        "Consulta as permissões do Vault atualmente configuradas "
        "para uma Role. "
        "É necessário informar o ID da Role. "
        "O resultado indica quais permissões estão habilitadas "
        "ou desabilitadas. "
        "Requer autenticação do usuário."
    ),
)
def consultar_permissoes_role(
    role_id: int,
    db: Session = Depends(get_db),

    # Consultar a configuração de permissões de uma Role exige
    # a mesma autorização utilizada pelo domínio principal
    # para visualizar Roles.
    usuario=Depends(
        require_permission(
            "Roles",
            "view",
        )
    ),
):
    """
    Consulta as permissões do Vault associadas à Role.
    """

    return consultar_permissoes_role_service(
        role_id=role_id,
        db=db,
    )


# ============================================================
# ALTERAR PERMISSÕES DA ROLE
# ============================================================

@router.put(
    "/roles/{role_id}",
    summary="Alterar Permissões da Role",
    description=(
        "Altera as permissões do Vault de uma Role. "
        "As permissões são definidas pelos campos can_view, "
        "can_create, can_edit, can_delete e can_use. "
        "Permissões marcadas como True serão vinculadas à Role "
        "e permissões marcadas como False serão removidas. "
        "Requer autenticação do usuário."
    ),
)
def alterar_permissoes_role(
    role_id: int,
    dados: RoleVaultPermissionRequest,
    db: Session = Depends(get_db),

    # Alterar permissões vinculadas à Role modifica diretamente
    # o RBAC. Portanto, exige autorização Roles:edit.
    usuario=Depends(
        require_permission(
            "Roles",
            "edit",
        )
    ),
):
    """
    Altera as permissões do Vault associadas à Role.
    """

    return alterar_permissoes_role_service(
        role_id=role_id,
        dados=dados,
        db=db,
    )