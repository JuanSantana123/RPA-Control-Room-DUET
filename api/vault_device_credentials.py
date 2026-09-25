# ============================================================
# API - VAULT DEVICE CREDENTIALS
# ============================================================
#
# Camada HTTP responsável EXCLUSIVAMENTE pelas credenciais
# Windows utilizadas pelos Devices/Agents do DUET.
#
# RESPONSABILIDADES DESTE ARQUIVO:
#
# - registrar endpoints FastAPI;
# - aplicar autenticação de usuário do Control Room;
# - aplicar permissões RBAC;
# - receber contratos Pydantic;
# - delegar regras de negócio ao service correto.
#
# ESTE MÓDULO NÃO DEVE:
#
# - acessar banco de dados diretamente;
# - criptografar ou descriptografar senha;
# - criar VaultCredential/VaultField diretamente;
# - associar credencial a Agent;
# - iniciar/desbloquear sessão Windows;
# - enviar senha ao RPA-Agent.
#
# Regras de negócio:
#
#     vault/device_credentials_service.py
#
# Contratos:
#
#     schemas/vault_device_credentials.py
#
# Associação Agent -> credential_id:
#
#     domínio Agents
#
# Segurança:
#
# - a senha nunca é retornada em texto claro;
# - a camada HTTP nunca descriptografa o segredo;
# - a API somente recebe a senha em criação/alteração;
# - logs de segredo não pertencem a esta camada.
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
)

from auth.dependencies import get_usuario_atual
from auth.permissions import require_permission

from schemas.vault_device_credentials import (
    DeviceCredentialCreateRequest,
    DeviceCredentialUpdateRequest,
)

from vault.device_credentials_service import (
    consultar_credencial_dispositivo_service,
    criar_credencial_dispositivo_service,
    editar_credencial_dispositivo_service,
    excluir_credencial_dispositivo_service,
    listar_credenciais_dispositivo_service,
)


# ============================================================
# ROUTER
# ============================================================
#
# Todas as rotas abaixo exigem uma sessão normal de usuário
# autenticado no Control Room.
#
# A autorização específica continua declarada endpoint a
# endpoint através de require_permission().
# ============================================================

router = APIRouter(
    prefix="/vault/device-credentials",
    tags=["Vault - Device Credentials"],
    dependencies=[
        Depends(
            get_usuario_atual
        ),
    ],
)


# ============================================================
# CRIAR CREDENCIAL DE DEVICE
# ============================================================

@router.post(
    "",
    summary="Criar credencial de Device",
    description=(
        "Cria uma credencial Windows utilizada por Devices/Agents. "
        "A senha é recebida somente para criação e é criptografada "
        "pelo service antes da persistência. "
        "Requer a permissão 'DeviceCredentials:create'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "DeviceCredentials",
                "create",
            )
        ),
    ],
)
def criar_credencial_dispositivo(
    request: DeviceCredentialCreateRequest,
    usuario=Depends(
        get_usuario_atual
    ),
):
    """
    Cria uma credencial Windows de Device.

    A camada HTTP apenas recebe e delega.

    A persistência, criptografia e validações de negócio
    pertencem a device_credentials_service.
    """

    return criar_credencial_dispositivo_service(
        request=request,
        usuario=usuario,
    )


# ============================================================
# LISTAR CREDENCIAIS DE DEVICE
# ============================================================

@router.get(
    "",
    summary="Listar credenciais de Device",
    description=(
        "Lista somente credenciais Windows destinadas a Devices. "
        "A senha nunca é retornada em texto claro. "
        "Requer a permissão 'DeviceCredentials:view'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "DeviceCredentials",
                "view",
            )
        ),
    ],
)
def listar_credenciais_dispositivo(
    usuario=Depends(
        get_usuario_atual
    ),
):
    """
    Lista as identidades Windows disponíveis para Devices.

    usuario permanece na assinatura para manter explicitamente
    o contexto autenticado da operação HTTP.
    """

    return listar_credenciais_dispositivo_service()


# ============================================================
# CONSULTAR CREDENCIAL DE DEVICE
# ============================================================
#
# IMPORTANTE:
#
# Esta rota precisa vir antes de qualquer rota futura que use
# segmentos textuais conflitantes sob o mesmo prefixo.
# ============================================================

@router.get(
    "/{credential_id}",
    summary="Consultar credencial de Device",
    description=(
        "Consulta uma credencial Windows específica. "
        "A senha permanece mascarada e nunca é descriptografada "
        "para o frontend. "
        "Requer a permissão 'DeviceCredentials:view'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "DeviceCredentials",
                "view",
            )
        ),
    ],
)
def consultar_credencial_dispositivo(
    credential_id: int,
    usuario=Depends(
        get_usuario_atual
    ),
):
    """
    Consulta uma credencial Windows pelo ID.
    """

    return consultar_credencial_dispositivo_service(
        credential_id=credential_id,
    )


# ============================================================
# EDITAR CREDENCIAL DE DEVICE
# ============================================================

@router.put(
    "/{credential_id}",
    summary="Editar credencial de Device",
    description=(
        "Atualiza domínio, usuário e opcionalmente a senha "
        "de uma credencial Windows. "
        "Quando keep_existing_password=true, a senha atual "
        "é preservada sem ser exposta ao frontend. "
        "Requer a permissão 'DeviceCredentials:edit'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "DeviceCredentials",
                "edit",
            )
        ),
    ],
)
def editar_credencial_dispositivo(
    credential_id: int,
    request: DeviceCredentialUpdateRequest,
    usuario=Depends(
        get_usuario_atual
    ),
):
    """
    Atualiza uma credencial Windows de Device.

    A camada HTTP não interpreta nem manipula ciphertext.
    """

    return editar_credencial_dispositivo_service(
        credential_id=credential_id,
        request=request,
        usuario=usuario,
    )


# ============================================================
# EXCLUIR CREDENCIAL DE DEVICE
# ============================================================

@router.delete(
    "/{credential_id}",
    summary="Excluir credencial de Device",
    description=(
        "Exclui uma credencial Windows de Device e seus campos. "
        "A associação com Agents é protegida pela integridade "
        "referencial configurada no banco. "
        "Requer a permissão 'DeviceCredentials:delete'."
    ),
    dependencies=[
        Depends(
            require_permission(
                "DeviceCredentials",
                "delete",
            )
        ),
    ],
)
def excluir_credencial_dispositivo(
    credential_id: int,
    usuario=Depends(
        get_usuario_atual
    ),
):
    """
    Exclui uma credencial Windows de Device.
    """

    return excluir_credencial_dispositivo_service(
        credential_id=credential_id,
        usuario=usuario,
    )
