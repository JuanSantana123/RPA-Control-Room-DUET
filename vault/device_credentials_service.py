# ============================================================
# VAULT - DEVICE CREDENTIALS SERVICE
# ============================================================
#
# Regras de negócio responsáveis EXCLUSIVAMENTE pelas
# credenciais Windows utilizadas pelos Devices/Agents do DUET.
#
# RESPONSABILIDADES DESTE ARQUIVO:
#
# - criar credenciais Windows de Device;
# - listar credenciais Windows de Device;
# - consultar uma credencial Windows de Device;
# - editar domínio, usuário e senha;
# - excluir credenciais Windows de Device;
# - criptografar a senha antes da persistência;
# - nunca devolver a senha em texto claro para a camada HTTP;
# - preservar o ciphertext atual quando a senha não for alterada.
#
# ESTE MÓDULO NÃO DEVE:
#
# - registrar rotas FastAPI;
# - definir Depends();
# - validar permissões RBAC;
# - autenticar usuários;
# - associar credenciais a Agents;
# - iniciar/desbloquear sessão Windows;
# - enviar credenciais para o RPA-Agent;
# - resolver credenciais para execução de Robot.
#
# Essas responsabilidades pertencem a outros domínios:
#
#     api/vault_device_credentials.py
#         HTTP + RBAC
#
#     agents/
#         associação Agent -> credential_id
#
#     execução / autenticação de sessão
#         uso temporário do segredo durante a execução
#
#
# MODELO PERSISTIDO
# -----------------
#
# VaultCredential:
#
#     scope = "device"
#     credential_type = "windows"
#     folder_id = None
#
# VaultField:
#
#     domain
#     username
#     password
#
# Somente "password" é secreto.
# ============================================================

from datetime import datetime
import logging

from database import SessionLocal

from models import (
    VaultCredential,
    VaultField,
)

from schemas.vault_device_credentials import (
    DeviceCredentialCreateRequest,
    DeviceCredentialUpdateRequest,
)

from vault.crypto import criptografar


# ============================================================
# CONSTANTES DO DOMÍNIO
# ============================================================

DEVICE_SCOPE = "device"
WINDOWS_CREDENTIAL_TYPE = "windows"

FIELD_DOMAIN = "domain"
FIELD_USERNAME = "username"
FIELD_PASSWORD = "password"

MASKED_SECRET_VALUE = "********"


# ============================================================
# LOGGER
# ============================================================
#
# Nunca registrar:
#
# - password;
# - ciphertext;
# - qualquer valor secreto.
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# HELPERS INTERNOS
# ============================================================

def _normalizar_texto(
    valor: str,
) -> str:
    """
    Remove espaços externos de valores administrativos.

    Não utilizar esta função para senha, porque espaços podem
    fazer parte legitimamente do segredo.
    """

    return valor.strip()


def _buscar_credencial_device_windows(
    db,
    credential_id: int,
):
    """
    Localiza exclusivamente uma credencial pertencente ao
    domínio Device/Windows.

    Isso impede que este service altere acidentalmente uma
    credencial tradicional de Automação.
    """

    return (
        db.query(VaultCredential)
        .filter(
            VaultCredential.id == credential_id,
            VaultCredential.scope == DEVICE_SCOPE,
            VaultCredential.credential_type
            == WINDOWS_CREDENTIAL_TYPE,
        )
        .first()
    )


def _carregar_campos(
    db,
    credential_id: int,
) -> list[VaultField]:
    """
    Carrega todos os VaultFields da credencial informada.
    """

    return (
        db.query(VaultField)
        .filter(
            VaultField.credential_id
            == credential_id
        )
        .order_by(
            VaultField.id
        )
        .all()
    )


def _indexar_campos_por_nome(
    campos: list[VaultField],
) -> dict[str, VaultField]:
    """
    Indexa campos pelo nome técnico.

    Como as credenciais Windows criadas por este service usam
    nomes técnicos estáveis, isso simplifica edição e consulta.
    """

    return {
        campo.name: campo
        for campo in campos
    }


def _montar_resposta_credencial(
    credencial: VaultCredential,
    campos: list[VaultField],
) -> dict:
    """
    Constrói a representação segura enviada às camadas acima.

    A senha nunca é descriptografada aqui.
    """

    campos_por_nome = _indexar_campos_por_nome(
        campos
    )

    domain_field = campos_por_nome.get(
        FIELD_DOMAIN
    )

    username_field = campos_por_nome.get(
        FIELD_USERNAME
    )

    password_field = campos_por_nome.get(
        FIELD_PASSWORD
    )

    return {
        "id": credencial.id,
        "name": credencial.name,
        "scope": credencial.scope,
        "credential_type": credencial.credential_type,
        "folder_id": credencial.folder_id,
        "domain": (
            domain_field.value
            if domain_field
            else ""
        ),
        "username": (
            username_field.value
            if username_field
            else ""
        ),
        # A API pode informar visualmente que existe uma senha,
        # mas nunca recebe o conteúdo criptografado nem plaintext.
        "password": (
            MASKED_SECRET_VALUE
            if password_field
            else ""
        ),
        "has_password": (
            password_field is not None
            and bool(password_field.value)
        ),
        "created_at": credencial.created_at,
        "updated_at": credencial.updated_at,
    }


def _validar_identidade_windows(
    *,
    domain: str,
    username: str,
) -> tuple[str, str]:
    """
    Valida e normaliza domínio e usuário Windows.

    Retorna:
        (domain_normalizado, username_normalizado)
    """

    domain_normalizado = _normalizar_texto(
        domain
    )

    username_normalizado = _normalizar_texto(
        username
    )

    if not domain_normalizado:

        raise ValueError(
            "Informe o domínio ou nome da máquina Windows."
        )

    if not username_normalizado:

        raise ValueError(
            "Informe o usuário Windows."
        )

    return (
        domain_normalizado,
        username_normalizado,
    )


# ============================================================
# CRIAR CREDENCIAL DE DEVICE
# ============================================================

def criar_credencial_dispositivo_service(
    request: DeviceCredentialCreateRequest,
    usuario,
):
    """
    Cria uma credencial Windows utilizada por Devices.

    O frontend informa somente:

        name
        domain
        username
        password

    O backend define obrigatoriamente:

        scope = "device"
        credential_type = "windows"
        folder_id = None

    A senha é criptografada utilizando a mesma camada
    criptográfica já homologada pelo Vault.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. NORMALIZA E VALIDA DADOS ADMINISTRATIVOS
        # ====================================================

        nome = _normalizar_texto(
            request.name
        )

        if not nome:

            return {
                "status": "error",
                "message": (
                    "Informe o nome da credencial."
                ),
            }


        try:

            domain, username = (
                _validar_identidade_windows(
                    domain=request.domain,
                    username=request.username,
                )
            )

        except ValueError as error:

            return {
                "status": "error",
                "message": str(error),
            }


        if request.password == "":

            return {
                "status": "error",
                "message": (
                    "Informe a senha da conta Windows."
                ),
            }


        # ====================================================
        # 2. VERIFICA DUPLICIDADE
        # ====================================================
        #
        # Credenciais de Device não pertencem a pastas.
        #
        # Portanto o nome precisa ser único dentro do escopo
        # Device/Windows, e não "único por folder_id".
        # ====================================================

        credencial_existente = (
            db.query(VaultCredential)
            .filter(
                VaultCredential.scope
                == DEVICE_SCOPE,
                VaultCredential.credential_type
                == WINDOWS_CREDENTIAL_TYPE,
                VaultCredential.name
                == nome,
            )
            .first()
        )


        if credencial_existente:

            logger.warning(
                "[VAULT DEVICE] Criação bloqueada | "
                f"Nome: {nome} | "
                "Motivo: credencial Windows já existe"
            )

            return {
                "status": "error",
                "message": (
                    "Já existe uma credencial de Device "
                    "com esse nome."
                ),
            }


        # ====================================================
        # 3. CRIA O REGISTRO PRINCIPAL
        # ====================================================

        agora = datetime.now()


        credencial = VaultCredential(
            name=nome,
            scope=DEVICE_SCOPE,
            credential_type=WINDOWS_CREDENTIAL_TYPE,
            folder_id=None,
            created_at=agora,
            updated_at=agora,
        )


        db.add(
            credencial
        )


        # Precisamos do ID antes de criptografar a senha,
        # pois o ID participa do associated_data.
        db.flush()


        # ====================================================
        # 4. CRIPTOGRAFA A SENHA
        # ====================================================
        #
        # Mantemos exatamente o mesmo associated_data utilizado
        # pelas credenciais tradicionais do Vault.
        #
        # Isso evita criar um segundo formato criptográfico.
        # ====================================================

        password_criptografado = criptografar(
            request.password,
            associated_data=(
                f"vault_field:{credencial.id}"
            ),
        )


        # ====================================================
        # 5. CRIA OS TRÊS CAMPOS PADRONIZADOS
        # ====================================================

        campos = [
            VaultField(
                credential_id=credencial.id,
                name=FIELD_DOMAIN,
                value=domain,
                is_secret=False,
                encryption_version=1,
                created_at=agora,
                updated_at=agora,
            ),
            VaultField(
                credential_id=credencial.id,
                name=FIELD_USERNAME,
                value=username,
                is_secret=False,
                encryption_version=1,
                created_at=agora,
                updated_at=agora,
            ),
            VaultField(
                credential_id=credencial.id,
                name=FIELD_PASSWORD,
                value=password_criptografado,
                is_secret=True,
                encryption_version=1,
                created_at=agora,
                updated_at=agora,
            ),
        ]


        db.add_all(
            campos
        )


        # ====================================================
        # 6. COMMIT
        # ====================================================

        db.commit()

        db.refresh(
            credencial
        )


        # ====================================================
        # 7. AUDITORIA SEGURA
        # ====================================================

        logger.info(
            "[VAULT DEVICE] Credencial Windows criada | "
            f"Usuário DUET: {usuario.username} | "
            f"Credential ID: {credencial.id} | "
            f"Nome: {credencial.name}"
        )


        # ====================================================
        # 8. RETORNO
        # ====================================================

        return {
            "status": "success",
            "message": (
                "Credencial de Device criada com sucesso."
            ),
            "credential": _montar_resposta_credencial(
                credencial,
                campos,
            ),
        }


    except Exception as error:

        db.rollback()


        logger.error(
            "[VAULT DEVICE] Erro ao criar credencial | "
            f"Nome: {getattr(request, 'name', '')} | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                "Erro ao criar credencial de Device."
            ),
        }


    finally:

        db.close()


# ============================================================
# LISTAR CREDENCIAIS DE DEVICE
# ============================================================

def listar_credenciais_dispositivo_service():
    """
    Lista somente credenciais:

        scope = device
        credential_type = windows

    Nenhum segredo é descriptografado durante a operação.
    """

    db = SessionLocal()

    try:

        credenciais = (
            db.query(VaultCredential)
            .filter(
                VaultCredential.scope
                == DEVICE_SCOPE,
                VaultCredential.credential_type
                == WINDOWS_CREDENTIAL_TYPE,
            )
            .order_by(
                VaultCredential.name
            )
            .all()
        )


        resultado = []


        for credencial in credenciais:

            campos = _carregar_campos(
                db,
                credencial.id,
            )


            resultado.append(
                _montar_resposta_credencial(
                    credencial,
                    campos,
                )
            )


        return {
            "status": "success",
            "credentials": resultado,
        }


    except Exception as error:

        logger.error(
            "[VAULT DEVICE] Erro ao listar credenciais | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                "Erro ao listar credenciais de Device."
            ),
            "credentials": [],
        }


    finally:

        db.close()


# ============================================================
# CONSULTAR CREDENCIAL DE DEVICE
# ============================================================

def consultar_credencial_dispositivo_service(
    credential_id: int,
):
    """
    Consulta uma credencial Windows específica.

    A senha permanece mascarada.
    """

    db = SessionLocal()

    try:

        credencial = _buscar_credencial_device_windows(
            db,
            credential_id,
        )


        if not credencial:

            return {
                "status": "error",
                "message": (
                    "Credencial de Device não encontrada."
                ),
            }


        campos = _carregar_campos(
            db,
            credential_id,
        )


        return {
            "status": "success",
            "credential": _montar_resposta_credencial(
                credencial,
                campos,
            ),
        }


    except Exception as error:

        logger.error(
            "[VAULT DEVICE] Erro ao consultar credencial | "
            f"Credential ID: {credential_id} | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                "Erro ao consultar credencial de Device."
            ),
        }


    finally:

        db.close()


# ============================================================
# EDITAR CREDENCIAL DE DEVICE
# ============================================================

def editar_credencial_dispositivo_service(
    credential_id: int,
    request: DeviceCredentialUpdateRequest,
    usuario,
):
    """
    Atualiza domínio, usuário e eventualmente a senha.

    A senha existente não é descriptografada quando o usuário
    escolhe preservá-la.

    Nesse caso o ciphertext atual é reutilizado diretamente.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. LOCALIZA SOMENTE DEVICE/WINDOWS
        # ====================================================

        credencial = _buscar_credencial_device_windows(
            db,
            credential_id,
        )


        if not credencial:

            return {
                "status": "error",
                "message": (
                    "Credencial de Device não encontrada."
                ),
            }


        # ====================================================
        # 2. NORMALIZA IDENTIDADE
        # ====================================================

        try:

            domain, username = (
                _validar_identidade_windows(
                    domain=request.domain,
                    username=request.username,
                )
            )

        except ValueError as error:

            return {
                "status": "error",
                "message": str(error),
            }


        # ====================================================
        # 3. CARREGA CAMPOS EXISTENTES
        # ====================================================

        campos_existentes = _carregar_campos(
            db,
            credential_id,
        )


        campos_por_nome = _indexar_campos_por_nome(
            campos_existentes
        )


        password_existente = campos_por_nome.get(
            FIELD_PASSWORD
        )


        # ====================================================
        # 4. DEFINE A SENHA QUE SERÁ PERSISTIDA
        # ====================================================

        if request.keep_existing_password:

            if (
                password_existente is None
                or
                not password_existente.is_secret
                or
                not password_existente.value
            ):

                return {
                    "status": "error",
                    "message": (
                        "A credencial não possui uma senha "
                        "existente válida para preservar."
                    ),
                }


            password_armazenado = (
                password_existente.value
            )


            password_encryption_version = (
                password_existente.encryption_version
            )


        else:

            if request.password == "":

                return {
                    "status": "error",
                    "message": (
                        "Informe a nova senha ou escolha "
                        "manter a senha atual."
                    ),
                }


            password_armazenado = criptografar(
                request.password,
                associated_data=(
                    f"vault_field:{credential_id}"
                ),
            )


            password_encryption_version = 1


        # ====================================================
        # 5. SUBSTITUI OS CAMPOS PADRONIZADOS
        # ====================================================
        #
        # O domínio Device/Windows possui exatamente os três
        # campos controlados por este service.
        #
        # Nenhum campo arbitrário é aceito nesta credencial.
        # ====================================================

        db.query(VaultField).filter(
            VaultField.credential_id
            == credential_id
        ).delete(
            synchronize_session=False
        )


        agora = datetime.now()


        novos_campos = [
            VaultField(
                credential_id=credential_id,
                name=FIELD_DOMAIN,
                value=domain,
                is_secret=False,
                encryption_version=1,
                created_at=agora,
                updated_at=agora,
            ),
            VaultField(
                credential_id=credential_id,
                name=FIELD_USERNAME,
                value=username,
                is_secret=False,
                encryption_version=1,
                created_at=agora,
                updated_at=agora,
            ),
            VaultField(
                credential_id=credential_id,
                name=FIELD_PASSWORD,
                value=password_armazenado,
                is_secret=True,
                encryption_version=(
                    password_encryption_version
                ),
                created_at=agora,
                updated_at=agora,
            ),
        ]


        db.add_all(
            novos_campos
        )


        credencial.updated_at = agora


        # ====================================================
        # 6. COMMIT
        # ====================================================

        db.commit()

        db.refresh(
            credencial
        )


        # ====================================================
        # 7. AUDITORIA SEGURA
        # ====================================================

        logger.info(
            "[VAULT DEVICE] Credencial Windows alterada | "
            f"Usuário DUET: {usuario.username} | "
            f"Credential ID: {credential_id} | "
            f"Nome: {credencial.name} | "
            "Senha alterada: "
            f"{not request.keep_existing_password}"
        )


        return {
            "status": "success",
            "message": (
                "Credencial de Device atualizada com sucesso."
            ),
            "credential": _montar_resposta_credencial(
                credencial,
                novos_campos,
            ),
        }


    except Exception as error:

        db.rollback()


        logger.error(
            "[VAULT DEVICE] Erro ao alterar credencial | "
            f"Credential ID: {credential_id} | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                "Erro ao atualizar credencial de Device."
            ),
        }


    finally:

        db.close()


# ============================================================
# EXCLUIR CREDENCIAL DE DEVICE
# ============================================================

def excluir_credencial_dispositivo_service(
    credential_id: int,
    usuario,
):
    """
    Exclui somente uma credencial Device/Windows.

    A responsabilidade de associação Agent -> credential_id
    NÃO pertence a este arquivo.

    A FK criada no banco com ON DELETE SET NULL garante a
    integridade referencial caso a credencial esteja associada
    a algum Agent.

    Portanto este service cuida apenas da credencial e de seus
    VaultFields.
    """

    db = SessionLocal()

    try:

        credencial = _buscar_credencial_device_windows(
            db,
            credential_id,
        )


        if not credencial:

            return {
                "status": "error",
                "message": (
                    "Credencial de Device não encontrada."
                ),
            }


        nome_credencial = credencial.name


        # ====================================================
        # REMOVE OS CAMPOS
        # ====================================================

        db.query(VaultField).filter(
            VaultField.credential_id
            == credential_id
        ).delete(
            synchronize_session=False
        )


        # ====================================================
        # REMOVE A CREDENCIAL
        # ====================================================

        db.delete(
            credencial
        )


        db.commit()


        logger.info(
            "[VAULT DEVICE] Credencial Windows excluída | "
            f"Usuário DUET: {usuario.username} | "
            f"Credential ID: {credential_id} | "
            f"Nome: {nome_credencial}"
        )


        return {
            "status": "success",
            "message": (
                "Credencial de Device excluída com sucesso."
            ),
            "credential_id": credential_id,
        }


    except Exception as error:

        db.rollback()


        logger.error(
            "[VAULT DEVICE] Erro ao excluir credencial | "
            f"Credential ID: {credential_id} | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                "Erro ao excluir credencial de Device."
            ),
        }


    finally:

        db.close()
