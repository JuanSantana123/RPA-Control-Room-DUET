# ============================================================
# DUET CORE - DEVICE CREDENTIAL RUNTIME
# ============================================================
#
# Responsabilidade:
#
# - resolver uma Credencial de Dispositivo Windows já validada
#   administrativamente;
# - carregar domain / username / password do Vault;
# - descriptografar a senha SOMENTE em memória;
# - devolver um objeto de runtime para o fluxo de execução.
#
# ESTE MÓDULO NÃO:
#
# - associa credenciais a Agents;
# - altera banco de dados;
# - executa commit / rollback;
# - envia dados ao Agent;
# - autentica sessão Windows;
# - registra senha ou ciphertext em log;
# - possui rota HTTP.
#
# Segurança:
#
# A senha existe em plaintext somente durante o runtime.
# O atributo password foi definido com repr=False para reduzir
# o risco de exposição acidental em prints/logs do objeto.
# ============================================================

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from models import VaultCredential, VaultField
from vault.crypto import descriptografar


# ============================================================
# CONSTANTES DO DOMÍNIO
# ============================================================

DEVICE_SCOPE = "device"
WINDOWS_CREDENTIAL_TYPE = "windows"

FIELD_DOMAIN = "domain"
FIELD_USERNAME = "username"
FIELD_PASSWORD = "password"


# ============================================================
# EXCEÇÃO DO DOMÍNIO
# ============================================================

class DeviceExecutionCredentialError(RuntimeError):
    """
    Erro controlado ao resolver uma credencial Windows de Device.

    A mensagem nunca deve conter password nem ciphertext.
    """



# ============================================================
# IDENTIDADE WINDOWS DE EXECUÇÃO
# ============================================================
#
# Representa somente os metadados necessários para descobrir
# qual usuário Windows o Agent deve possuir.
#
# IMPORTANTE:
#
# Esta estrutura NÃO contém password.
# Ela pode ser usada antes de qualquer descriptografia para
# comparar a sessão Windows atual com a identidade configurada.
# ============================================================

@dataclass(slots=True)
class DeviceWindowsExecutionIdentity:
    """
    Identidade Windows configurada para determinado Device.

    Contém somente dados não secretos:
        - credential_id;
        - name;
        - domain;
        - username.
    """

    credential_id: int
    name: str
    domain: str
    username: str

# ============================================================
# OBJETO DE RUNTIME
# ============================================================

@dataclass(slots=True)
class DeviceWindowsExecutionCredential:
    """
    Material temporário utilizado durante a execução.

    password:
        Mantido fora do repr() para evitar exposição acidental
        quando o objeto for exibido em logs de diagnóstico.
    """

    credential_id: int
    name: str
    domain: str
    username: str

    password: str = field(
        repr=False
    )


# ============================================================
# RESOLVER CREDENCIAL WINDOWS
# ============================================================

def resolver_credencial_windows_device(
    *,
    credential_id: int,
    db: Session,
) -> DeviceWindowsExecutionCredential:
    """
    Resolve uma Credencial de Dispositivo Windows para uso runtime.

    Parameters
    ----------
    credential_id:
        ID da VaultCredential que será resolvida.

    db:
        Sessão SQLAlchemy já aberta pelo chamador.

    Returns
    -------
    DeviceWindowsExecutionCredential
        Objeto transitório contendo domínio, usuário e senha.

    Raises
    ------
    DeviceExecutionCredentialError
        Quando a credencial não existe, não pertence ao escopo
        correto, possui campos incompletos ou não pode ser
        descriptografada.

    IMPORTANTE
    ----------
    Esta função NÃO executa commit nem rollback porque realiza
    somente leitura.
    """

    # ========================================================
    # 1. LOCALIZA A CREDENCIAL PRINCIPAL
    # ========================================================

    credential = (
        db.query(VaultCredential)
        .filter(
            VaultCredential.id == credential_id
        )
        .first()
    )

    if credential is None:
        raise DeviceExecutionCredentialError(
            "Credencial de dispositivo não encontrada."
        )


    # ========================================================
    # 2. VALIDA O DOMÍNIO DA CREDENCIAL
    # ========================================================

    if credential.scope != DEVICE_SCOPE:
        raise DeviceExecutionCredentialError(
            "A credencial informada não pertence ao escopo device."
        )

    if (
        credential.credential_type
        != WINDOWS_CREDENTIAL_TYPE
    ):
        raise DeviceExecutionCredentialError(
            "A credencial informada não é do tipo windows."
        )


    # ========================================================
    # 3. CARREGA OS CAMPOS
    # ========================================================
    #
    # Os três campos pertencem à mesma VaultCredential.
    # ========================================================

    fields = (
        db.query(VaultField)
        .filter(
            VaultField.credential_id == credential.id
        )
        .all()
    )

    fields_by_name = {
        vault_field.name: vault_field
        for vault_field in fields
    }

    domain_field = fields_by_name.get(
        FIELD_DOMAIN
    )

    username_field = fields_by_name.get(
        FIELD_USERNAME
    )

    password_field = fields_by_name.get(
        FIELD_PASSWORD
    )


    # ========================================================
    # 4. VALIDA CAMPOS NÃO SECRETOS
    # ========================================================

    if (
        domain_field is None
        or
        not domain_field.value
    ):
        raise DeviceExecutionCredentialError(
            "A credencial Windows não possui domínio configurado."
        )

    if (
        username_field is None
        or
        not username_field.value
    ):
        raise DeviceExecutionCredentialError(
            "A credencial Windows não possui usuário configurado."
        )


    # ========================================================
    # 5. VALIDA O CAMPO DE SENHA
    # ========================================================

    if password_field is None:
        raise DeviceExecutionCredentialError(
            "A credencial Windows não possui senha configurada."
        )

    if password_field.is_secret is not True:
        raise DeviceExecutionCredentialError(
            "O campo password da credencial Windows não está "
            "marcado como segredo."
        )

    if not password_field.value:
        raise DeviceExecutionCredentialError(
            "O segredo password da credencial Windows está vazio."
        )


    # ========================================================
    # 6. DESCRIPTOGRAFA SOMENTE EM MEMÓRIA
    # ========================================================
    #
    # A criação da Device Credential utiliza:
    #
    #     associated_data = f"vault_field:{credential.id}"
    #
    # O mesmo AAD precisa ser usado para abrir o AES-GCM.
    # ========================================================

    try:

        password = descriptografar(
            password_field.value,
            associated_data=(
                f"vault_field:{credential.id}"
            ),
        )

    except Exception as error:

        # Nunca propagamos ciphertext ou conteúdo secreto.
        raise DeviceExecutionCredentialError(
            "Não foi possível descriptografar a senha da "
            "credencial Windows."
        ) from error


    if not password:
        raise DeviceExecutionCredentialError(
            "A senha descriptografada da credencial Windows "
            "está vazia."
        )


    # ========================================================
    # 7. DEVOLVE MATERIAL TRANSITÓRIO
    # ========================================================

    return DeviceWindowsExecutionCredential(
        credential_id=credential.id,
        name=credential.name,
        domain=domain_field.value.strip(),
        username=username_field.value.strip(),
        password=password,
    )


# ============================================================
# RESOLVER SOMENTE A IDENTIDADE WINDOWS
# ============================================================

def resolver_identidade_windows_device(
    *,
    credential_id: int,
    db: Session,
) -> DeviceWindowsExecutionIdentity:
    """
    Resolve somente domínio e usuário da Credencial de Device.

    Esta função é utilizada antes da autenticação para comparar
    a identidade configurada no Control Room com a sessão
    realmente observada pelo Agent.

    Segurança
    ---------
    - não consulta o campo password;
    - não descriptografa segredo;
    - não executa commit;
    - não altera a credencial.
    """

    # ========================================================
    # 1. LOCALIZA A CREDENCIAL
    # ========================================================

    credential = (
        db.query(VaultCredential)
        .filter(
            VaultCredential.id == credential_id
        )
        .first()
    )

    if credential is None:
        raise DeviceExecutionCredentialError(
            "Credencial de dispositivo não encontrada."
        )

    # ========================================================
    # 2. VALIDA ESCOPO E TIPO
    # ========================================================

    if credential.scope != DEVICE_SCOPE:
        raise DeviceExecutionCredentialError(
            "A credencial informada não pertence ao escopo device."
        )

    if (
        credential.credential_type
        != WINDOWS_CREDENTIAL_TYPE
    ):
        raise DeviceExecutionCredentialError(
            "A credencial informada não é do tipo windows."
        )

    # ========================================================
    # 3. CARREGA SOMENTE CAMPOS NÃO SECRETOS
    # ========================================================
    #
    # O password nem sequer participa desta consulta.
    # ========================================================

    fields = (
        db.query(VaultField)
        .filter(
            VaultField.credential_id == credential.id,
            VaultField.name.in_(
                (
                    FIELD_DOMAIN,
                    FIELD_USERNAME,
                )
            ),
        )
        .all()
    )

    fields_by_name = {
        vault_field.name: vault_field
        for vault_field in fields
    }

    domain_field = fields_by_name.get(
        FIELD_DOMAIN
    )

    username_field = fields_by_name.get(
        FIELD_USERNAME
    )

    # ========================================================
    # 4. VALIDA OS CAMPOS
    # ========================================================

    if (
        domain_field is None
        or
        not domain_field.value
    ):
        raise DeviceExecutionCredentialError(
            "A credencial Windows não possui domínio configurado."
        )

    if (
        username_field is None
        or
        not username_field.value
    ):
        raise DeviceExecutionCredentialError(
            "A credencial Windows não possui usuário configurado."
        )

    # ========================================================
    # 5. RETORNA SOMENTE METADADOS NÃO SECRETOS
    # ========================================================

    return DeviceWindowsExecutionIdentity(
        credential_id=credential.id,
        name=credential.name,
        domain=domain_field.value.strip(),
        username=username_field.value.strip(),
    )