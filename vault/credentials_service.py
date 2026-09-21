# ============================================================
# VAULT - CREDENTIALS SERVICE
# ============================================================
#
# Regras de negócio responsáveis pelo gerenciamento das
# credenciais armazenadas no Vault.
#
# Responsabilidades:
#
# - criar credenciais;
# - listar credenciais;
# - editar campos de uma credencial;
# - excluir credenciais;
# - criptografar campos secretos antes da persistência;
# - mascarar campos secretos durante consultas;
# - preservar segredos existentes durante edição.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra rotas FastAPI;
# - define Depends();
# - define permissões RBAC;
# - autentica usuários;
# - registra valores secretos em logs.
#
# RBAC e autenticação continuam pertencendo à camada HTTP.
# ============================================================

from datetime import datetime
import logging

from database import SessionLocal

from models import (
    VaultCredential,
    VaultField,
    VaultFolder,
)

from schemas.vault_credentials import (
    VaultCredentialCreateRequest,
    VaultCredentialUpdateRequest,
)

from vault.crypto import criptografar


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# CRIAR CREDENCIAL
# ============================================================

def criar_credencial_service(
    request: VaultCredentialCreateRequest,
    usuario,
):
    """
    Cria uma nova credencial dentro de uma pasta do Vault.

    Parâmetros
    ----------
    request:
        Dados da credencial e seus respectivos campos.

    usuario:
        Usuário autenticado responsável pela operação.

        Utilizado para auditoria administrativa.

    Segurança
    ---------
    Campos marcados com is_secret=True são criptografados
    antes de serem persistidos.

    Nenhum valor de campo é registrado nos logs.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. VALIDA A PASTA
        # ====================================================

        pasta = (
            db.query(VaultFolder)
            .filter(
                VaultFolder.id == request.folder_id
            )
            .first()
        )


        if not pasta:

            return {
                "status": "error",
                "message": "Pasta do Vault não encontrada.",
            }


        # ====================================================
        # 2. VERIFICA DUPLICIDADE
        # ====================================================
        #
        # O nome da credencial precisa ser único dentro
        # da pasta.
        #
        # Preservamos a comparação atual exatamente como está.
        # ====================================================

        credencial_existente = (
            db.query(VaultCredential)
            .filter(
                VaultCredential.folder_id == request.folder_id,
                VaultCredential.name == request.name,
            )
            .first()
        )


        if credencial_existente:

            # ------------------------------------------------
            # AUDITORIA DA TENTATIVA BLOQUEADA
            # ------------------------------------------------
            #
            # Nenhum valor de campo é registrado.
            # ------------------------------------------------

            logger.warning(
                "[VAULT] Criação de credencial bloqueada | "
                f"Nome: {request.name} | "
                f"Folder ID: {request.folder_id} | "
                "Motivo: credencial já existe nesta pasta"
            )

            return {
                "status": "error",
                "message": (
                    "Já existe uma credencial com esse nome "
                    "nesta pasta."
                ),
            }


        # ====================================================
        # 3. CRIA A CREDENCIAL
        # ====================================================

        agora = datetime.now()

        credencial = VaultCredential(
            name=request.name,
            folder_id=request.folder_id,
            created_at=agora,
            updated_at=agora,
        )

        db.add(
            credencial
        )


        # ----------------------------------------------------
        # FLUSH
        # ----------------------------------------------------
        #
        # Precisamos do ID antes de criar os VaultFields.
        #
        # Esse ID também participa do associated_data usado
        # pela criptografia.
        # ----------------------------------------------------

        db.flush()


        # ====================================================
        # 4. CRIA OS CAMPOS
        # ====================================================

        for campo in request.fields:

            valor = campo.value


            # ------------------------------------------------
            # CAMPO SECRETO
            # ------------------------------------------------
            #
            # O texto original nunca é persistido.
            # ------------------------------------------------

            if campo.is_secret:

                valor = criptografar(
                    valor,
                    associated_data=(
                        f"vault_field:{credencial.id}"
                    ),
                )


            # ------------------------------------------------
            # PERSISTE O CAMPO
            # ------------------------------------------------

            campo_vault = VaultField(
                credential_id=credencial.id,
                name=campo.name,
                value=valor,
                is_secret=campo.is_secret,
                encryption_version=1,
                created_at=agora,
                updated_at=agora,
            )

            db.add(
                campo_vault
            )


        # ====================================================
        # 5. COMMIT
        # ====================================================

        db.commit()

        db.refresh(
            credencial
        )


        # ====================================================
        # 6. AUDITORIA
        # ====================================================
        #
        # Não registrar:
        #
        # - username/password armazenados;
        # - tokens;
        # - segredos;
        # - qualquer outro valor de VaultField.
        # ====================================================

        logger.info(
            "[VAULT] Credencial criada | "
            f"Usuário: {usuario.username} | "
            f"ID: {credencial.id} | "
            f"Nome: {credencial.name} | "
            f"Folder ID: {credencial.folder_id}"
        )


        # ====================================================
        # 7. RETORNO
        # ====================================================

        return {
            "status": "success",
            "message": "Credencial criada com sucesso.",
            "credential": {
                "id": credencial.id,
                "name": credencial.name,
                "folder_id": credencial.folder_id,
            },
        }


    except Exception as error:

        # ====================================================
        # ROLLBACK
        # ====================================================

        db.rollback()


        # ====================================================
        # LOG DO ERRO
        # ====================================================
        #
        # Preservamos somente informações administrativas.
        # ====================================================

        logger.error(
            "[VAULT] Erro ao criar credencial | "
            f"Nome: {request.name} | "
            f"Folder ID: {request.folder_id} | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                f"Erro ao criar credencial: {str(error)}"
            ),
        }


    finally:

        db.close()


# ============================================================
# LISTAR CREDENCIAIS
# ============================================================

def listar_credenciais_service(
    folder_id: int | None = None,
):
    """
    Lista as credenciais cadastradas no Vault.

    Parâmetros
    ----------
    folder_id:
        Quando informado, retorna somente credenciais
        pertencentes à pasta indicada.

        Quando None, retorna credenciais de todas as pastas.

    Segurança
    ---------
    Valores secretos nunca são descriptografados nesta operação.

    O frontend recebe:

        ********

    para qualquer VaultField marcado como secreto.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. MONTA QUERY
        # ====================================================

        query = db.query(
            VaultCredential
        )


        if folder_id is not None:

            query = query.filter(
                VaultCredential.folder_id == folder_id
            )


        # ====================================================
        # 2. LISTA CREDENCIAIS
        # ====================================================

        credenciais = (
            query
            .order_by(
                VaultCredential.name
            )
            .all()
        )


        resultado = []


        # ====================================================
        # 3. CARREGA OS CAMPOS
        # ====================================================

        for credencial in credenciais:

            campos = (
                db.query(VaultField)
                .filter(
                    VaultField.credential_id == credencial.id
                )
                .order_by(
                    VaultField.id
                )
                .all()
            )


            campos_resultado = []


            for campo in campos:

                # --------------------------------------------
                # CAMPO SECRETO
                # --------------------------------------------
                #
                # Nunca descriptografamos durante listagem.
                # --------------------------------------------

                if campo.is_secret:

                    valor = "********"


                # --------------------------------------------
                # CAMPO NÃO SECRETO
                # --------------------------------------------

                else:

                    valor = campo.value


                campos_resultado.append({
                    "id": campo.id,
                    "name": campo.name,
                    "value": valor,
                    "is_secret": campo.is_secret,
                })


            resultado.append({
                "id": credencial.id,
                "name": credencial.name,
                "folder_id": credencial.folder_id,
                "created_at": credencial.created_at,
                "updated_at": credencial.updated_at,
                "fields": campos_resultado,
            })


        # ====================================================
        # 4. RETORNO
        # ====================================================

        return {
            "status": "success",
            "credentials": resultado,
        }


    finally:

        db.close()


# ============================================================
# EDITAR CREDENCIAL
# ============================================================

def editar_credencial_service(
    credential_id: int,
    request: VaultCredentialUpdateRequest,
    usuario,
):
    """
    Atualiza os campos de uma credencial existente.

    O nome da credencial permanece imutável.

    A lista recebida representa a lista completa de campos
    que deverá existir depois da operação.

    Segredos existentes
    -------------------
    Quando:

        keep_existing=True

    e o ID recebido pertence a um campo secreto existente,
    reutilizamos diretamente o valor criptografado armazenado.

    Portanto:

    - não descriptografamos;
    - não recriptografamos;
    - não enviamos o segredo ao frontend.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. LOCALIZA A CREDENCIAL
        # ====================================================

        credencial = (
            db.query(VaultCredential)
            .filter(
                VaultCredential.id == credential_id
            )
            .first()
        )


        if not credencial:

            return {
                "status": "error",
                "message": "Credencial não encontrada.",
            }


        # ====================================================
        # 2. CARREGA OS CAMPOS ATUAIS
        # ====================================================
        #
        # Precisamos carregar os objetos antes da exclusão.
        #
        # Isso permite reutilizar o ciphertext de um segredo
        # quando keep_existing=True.
        # ====================================================

        campos_existentes = (
            db.query(VaultField)
            .filter(
                VaultField.credential_id == credential_id
            )
            .all()
        )


        campos_por_id = {
            campo.id: campo
            for campo in campos_existentes
        }


        # ====================================================
        # 3. VALIDA LISTA RECEBIDA
        # ====================================================

        if len(request.fields) == 0:

            return {
                "status": "error",
                "message": (
                    "A credencial precisa possuir "
                    "pelo menos um campo."
                ),
            }


        # ====================================================
        # 4. REMOVE OS CAMPOS ATUAIS
        # ====================================================
        #
        # IMPORTANTE:
        #
        # Os objetos anteriores continuam disponíveis em
        # campos_por_id durante esta operação.
        # ====================================================

        db.query(VaultField).filter(
            VaultField.credential_id == credential_id
        ).delete(
            synchronize_session=False
        )


        # ====================================================
        # 5. RECRIA OS CAMPOS
        # ====================================================

        agora = datetime.now()


        for campo in request.fields:

            # ------------------------------------------------
            # LOCALIZA EVENTUAL CAMPO EXISTENTE
            # ------------------------------------------------

            campo_existente = None


            if campo.id is not None:

                campo_existente = campos_por_id.get(
                    campo.id
                )


                # --------------------------------------------
                # PROTEÇÃO CONTRA ID DE OUTRA CREDENCIAL
                # --------------------------------------------

                if campo_existente is None:

                    return {
                        "status": "error",
                        "message": (
                            f"O campo ID {campo.id} "
                            "não pertence a esta credencial."
                        ),
                    }


            # =================================================
            # CAMPO SECRETO
            # =================================================

            if campo.is_secret:

                # --------------------------------------------
                # PRESERVA SEGREDO EXISTENTE
                # --------------------------------------------
                #
                # Reutilizamos diretamente o ciphertext.
                #
                # Não é necessário descriptografar.
                # --------------------------------------------

                if (
                    campo.keep_existing
                    and campo_existente is not None
                    and campo_existente.is_secret
                ):

                    valor = campo_existente.value

                    encryption_version = (
                        campo_existente.encryption_version
                    )


                # --------------------------------------------
                # NOVO SEGREDO
                # --------------------------------------------

                else:

                    # Um segredo novo não pode possuir
                    # valor vazio.

                    if campo.value == "":

                        return {
                            "status": "error",
                            "message": (
                                f"Informe um novo valor para "
                                f"o campo secreto '{campo.name}' "
                                "ou mantenha o valor atual."
                            ),
                        }


                    valor = criptografar(
                        campo.value,
                        associated_data=(
                            f"vault_field:{credential_id}"
                        ),
                    )

                    encryption_version = 1


            # =================================================
            # CAMPO NÃO SECRETO
            # =================================================

            else:

                valor = campo.value

                encryption_version = 1


            # =================================================
            # CRIA NOVO VAULT FIELD
            # =================================================

            campo_vault = VaultField(
                credential_id=credential_id,
                name=campo.name,
                value=valor,
                is_secret=campo.is_secret,
                encryption_version=encryption_version,
                created_at=agora,
                updated_at=agora,
            )

            db.add(
                campo_vault
            )


        # ====================================================
        # 6. ATUALIZA CREDENCIAL
        # ====================================================
        #
        # O nome continua imutável.
        # ====================================================

        credencial.updated_at = agora


        # ====================================================
        # 7. COMMIT
        # ====================================================

        db.commit()

        db.refresh(
            credencial
        )


        # ====================================================
        # 8. AUDITORIA
        # ====================================================

        logger.info(
            "[VAULT] Credencial alterada | "
            f"Usuário: {usuario.username} | "
            f"ID: {credencial.id} | "
            f"Nome: {credencial.name} | "
            f"Folder ID: {credencial.folder_id}"
        )


        # ====================================================
        # 9. RETORNO
        # ====================================================

        return {
            "status": "success",
            "message": "Credencial atualizada com sucesso.",
            "credential": {
                "id": credencial.id,
                "name": credencial.name,
                "folder_id": credencial.folder_id,
            },
        }


    except Exception as error:

        db.rollback()


        logger.error(
            "[VAULT] Erro ao alterar credencial | "
            f"ID: {credential_id} | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                f"Erro ao atualizar credencial: {str(error)}"
            ),
        }


    finally:

        db.close()


# ============================================================
# EXCLUIR CREDENCIAL
# ============================================================

def excluir_credencial_service(
    credential_id: int,
    usuario,
):
    """
    Exclui uma credencial do Vault.

    Antes da exclusão da VaultCredential, todos os VaultFields
    associados são removidos.

    Nenhum valor pertencente aos campos é registrado no log.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # 1. LOCALIZA A CREDENCIAL
        # ====================================================

        credencial = (
            db.query(VaultCredential)
            .filter(
                VaultCredential.id == credential_id
            )
            .first()
        )


        if not credencial:

            return {
                "status": "error",
                "message": "Credencial não encontrada.",
            }


        # ====================================================
        # 2. REMOVE OS CAMPOS
        # ====================================================
        #
        # Isso remove inclusive os ciphertexts armazenados
        # nos campos secretos.
        # ====================================================

        db.query(VaultField).filter(
            VaultField.credential_id == credential_id
        ).delete(
            synchronize_session=False
        )


        # ====================================================
        # 3. REMOVE A CREDENCIAL
        # ====================================================

        db.delete(
            credencial
        )


        # ====================================================
        # 4. COMMIT
        # ====================================================

        db.commit()


        # ====================================================
        # 5. AUDITORIA
        # ====================================================

        logger.info(
            "[VAULT] Credencial excluída | "
            f"Usuário: {usuario.username} | "
            f"ID: {credential_id} | "
            f"Nome: {credencial.name} | "
            f"Folder ID: {credencial.folder_id}"
        )


        # ====================================================
        # 6. RETORNO
        # ====================================================

        return {
            "status": "success",
            "message": "Credencial excluída com sucesso.",
            "credential_id": credential_id,
        }


    except Exception as error:

        db.rollback()


        logger.error(
            "[VAULT] Erro ao excluir credencial | "
            f"ID: {credential_id} | "
            f"Erro: {error}"
        )


        return {
            "status": "error",
            "message": (
                f"Erro ao excluir credencial: {str(error)}"
            ),
        }


    finally:

        db.close()