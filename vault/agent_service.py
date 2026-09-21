# ============================================================
# VAULT - AGENT SERVICE
# ============================================================
#
# Regras de negócio utilizadas pelo Agent para consumir
# credenciais do Vault durante uma execução de RPA.
#
# Fluxo preservado:
#
#     Agent autenticado
#          │
#          ▼
#     execution_id
#          │
#          ▼
#     valida Execution
#          │
#          ▼
#     valida Agent da Execution
#          │
#          ▼
#     identifica User da Execution
#          │
#          ▼
#     valida usuário ativo
#          │
#          ▼
#     valida permissão can_use do Vault
#          │
#          ▼
#     resolve credential_path
#          │
#          ▼
#     localiza VaultCredential
#          │
#          ▼
#     carrega VaultFields
#          │
#          ▼
#     descriptografa somente campos secretos
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra rotas FastAPI;
# - autentica o agent_token;
# - utiliza get_usuario_atual;
# - recebe Depends();
# - registra valores secretos em log.
#
# A autenticação técnica do Agent permanece em:
#
#     vault/agent_auth.py
#
# ============================================================

import logging

from fastapi import HTTPException

# Consulta centralizada das permissões RBAC.
#
# O Agent não autentica um usuário diretamente. O usuário é
# descoberto através da Execution e sua autorização é então
# validada pelo mesmo mecanismo RBAC utilizado pelo restante
# do Control Room.
from auth.permissions import usuario_tem_permissao

from database import SessionLocal
from models import (
    Execution,
    User,
    VaultCredential,
    VaultField,
    VaultFolder,
)
from vault.crypto import descriptografar


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# RESOLVER CREDENCIAL PARA O AGENT
# ============================================================

def resolver_credencial_agent_service(
    credential_path: str,
    execution_id: int,
    agent,
):
    """
    Resolve uma credencial do Vault para uma execução de RPA.

    Parâmetros
    ----------
    credential_path:
        Caminho completo da credencial dentro da hierarquia
        de pastas do Vault.

        Exemplo:

            empresa1/SAP/SAP_FINANCEIRO

    execution_id:
        ID da Execution que está solicitando a credencial.

    agent:
        Agent previamente autenticado através do agent_token.

        Esse objeto é fornecido pela camada HTTP através de:

            validar_agent_token

    Retorno
    -------
    dict
        Identificação da execução, usuário responsável e campos
        pertencentes à credencial solicitada.

    Segurança
    ---------
    O valor de um campo secreto somente é descriptografado depois
    de todas as validações de execução, Agent, usuário e permissão.
    """

    # --------------------------------------------------------
    # SESSÃO DO BANCO
    # --------------------------------------------------------
    #
    # Preservamos o comportamento atual do endpoint, que abre
    # sua própria SessionLocal durante a resolução.
    # --------------------------------------------------------

    db = SessionLocal()

    try:

        # ====================================================
        # 1. LOCALIZA A EXECUÇÃO
        # ====================================================
        #
        # O Agent envia somente o execution_id.
        #
        # A partir dele o Control Room consegue descobrir:
        #
        # - qual Agent executa o processo;
        # - qual usuário iniciou a execução.
        # ====================================================

        execucao = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id
            )
            .first()
        )


        if not execucao:

            raise HTTPException(
                status_code=404,
                detail="Execução não encontrada.",
            )


        # ====================================================
        # 2. EXECUÇÃO PRECISA POSSUIR USUÁRIO
        # ====================================================

        if not execucao.user_id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "A execução não possui usuário associado."
                ),
            )


        # Guarda o usuário responsável pela execução.
        user_id = execucao.user_id


        # ====================================================
        # 3. VALIDA SE A EXECUÇÃO PERTENCE AO AGENT
        # ====================================================
        #
        # O agent_token identifica quem está fazendo a chamada.
        #
        # O execution_id identifica qual execução está tentando
        # acessar o Vault.
        #
        # Os dois precisam estar associados.
        # ====================================================

        if execucao.agent_id != agent.agent_id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "A execução não pertence a este Agent."
                ),
            )


        # ====================================================
        # 4. LOCALIZA O USUÁRIO DA EXECUÇÃO
        # ====================================================

        usuario = (
            db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )


        if not usuario:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Usuário da execução não encontrado."
                ),
            )


        # ====================================================
        # 5. VALIDA USUÁRIO ATIVO
        # ====================================================
        #
        # Uma execução antiga não deve permitir que um usuário
        # posteriormente desativado continue consumindo recursos
        # protegidos do Control Room.
        # ====================================================

        if not usuario.is_active:

            raise HTTPException(
                status_code=403,
                detail=(
                    "O usuário da execução está desativado."
                ),
            )


        # ====================================================
        # 6. VERIFICA PERMISSÃO DE USO DO VAULT
        # ====================================================
        #
        # A autorização é baseada no usuário responsável pela
        # Execution.
        #
        # O Agent somente transporta a solicitação.
        #
        # Ele NÃO decide se o usuário possui acesso ao Vault.
        # ====================================================

        # ----------------------------------------------------
        # Utiliza diretamente o RBAC central do Control Room.
        #
        # A antiga função usuario_pode_vault(..., "can_use")
        # apenas traduzia:
        #
        #     can_use -> Vault:use
        #
        # Portanto não existe mudança na permissão efetivamente
        # exigida pelo fluxo.
        # ----------------------------------------------------

        if not usuario_tem_permissao(
            usuario=usuario,
            db=db,
            resource="Vault",
            action="use",
        ):

            # ------------------------------------------------
            # AUDITORIA
            # ------------------------------------------------
            #
            # Preservamos o log existente.
            #
            # Nenhum valor dos campos da credencial aparece aqui.
            # ------------------------------------------------

            logger.warning(
                "[VAULT] Uso de credencial bloqueado | "
                f"Usuário: {usuario.username} | "
                f"Credencial: {credential_path} | "
                "Permissão necessária: can_use"
            )

            raise HTTPException(
                status_code=403,
                detail=(
                    "Usuário não possui permissão para "
                    "utilizar credenciais do Vault."
                ),
            )


        # ====================================================
        # 7. INTERPRETA O CAMINHO DA CREDENCIAL
        # ====================================================
        #
        # Exemplo:
        #
        #     empresa1/SAP/SAP_FINANCEIRO
        #
        # Resultado:
        #
        #     pastas:
        #         empresa1
        #         SAP
        #
        #     credencial:
        #         SAP_FINANCEIRO
        #
        # Segmentos vazios são ignorados, preservando o
        # comportamento atual.
        # ====================================================

        partes_caminho = [
            parte.strip()
            for parte in credential_path.split("/")
            if parte.strip()
        ]


        # O código atual exige pelo menos:
        #
        #     pasta/credencial
        #
        # Uma credencial diretamente sem pasta não é aceita
        # por este endpoint.

        if len(partes_caminho) < 2:

            raise HTTPException(
                status_code=400,
                detail=(
                    "O caminho da credencial deve informar "
                    "todas as pastas. Exemplo: "
                    "empresa1/SAP/SAP_FINANCEIRO"
                ),
            )


        # Último componente = credencial.
        nome_credencial = partes_caminho[-1]

        # Componentes anteriores = hierarquia de pastas.
        pastas = partes_caminho[:-1]


        # ====================================================
        # 8. LOCALIZA A PASTA RAIZ
        # ====================================================
        #
        # A primeira pasta precisa obrigatoriamente possuir:
        #
        #     parent_id IS NULL
        #
        # Isso impede encontrar acidentalmente uma subpasta
        # homônima em outro ponto da árvore.
        # ====================================================

        pasta_atual = (
            db.query(VaultFolder)
            .filter(
                VaultFolder.name == pastas[0],
                VaultFolder.parent_id.is_(None),
            )
            .first()
        )


        if not pasta_atual:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Pasta do Vault não encontrada."
                ),
            )


        # ====================================================
        # 9. PERCORRE AS SUBPASTAS
        # ====================================================
        #
        # Cada próxima pasta precisa ser filha exatamente da
        # pasta encontrada no nível anterior.
        # ====================================================

        for nome_pasta in pastas[1:]:

            pasta_atual = (
                db.query(VaultFolder)
                .filter(
                    VaultFolder.name == nome_pasta,
                    VaultFolder.parent_id == pasta_atual.id,
                )
                .first()
            )


            if not pasta_atual:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Caminho da pasta do Vault "
                        "não encontrado."
                    ),
                )


        # ====================================================
        # 10. LOCALIZA A CREDENCIAL
        # ====================================================
        #
        # O nome sozinho não basta.
        #
        # A credencial precisa existir exatamente dentro da
        # pasta resultante da navegação anterior.
        # ====================================================

        credencial = (
            db.query(VaultCredential)
            .filter(
                VaultCredential.name == nome_credencial,
                VaultCredential.folder_id == pasta_atual.id,
            )
            .first()
        )


        if not credencial:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Credencial não encontrada "
                    "no caminho informado."
                ),
            )


        # ====================================================
        # 11. CARREGA OS CAMPOS
        # ====================================================

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


        resultado = {}


        # ====================================================
        # 12. PREPARA OS VALORES
        # ====================================================

        for campo in campos:

            # ------------------------------------------------
            # CAMPO SECRETO
            # ------------------------------------------------
            #
            # A descriptografia acontece somente neste ponto,
            # depois de todas as validações anteriores.
            #
            # associated_data precisa continuar exatamente
            # vinculada ao ID da credencial.
            # ------------------------------------------------

            if campo.is_secret:

                valor = descriptografar(
                    campo.value,
                    associated_data=(
                        f"vault_field:{credencial.id}"
                    ),
                )


            # ------------------------------------------------
            # CAMPO NÃO SECRETO
            # ------------------------------------------------

            else:

                valor = campo.value


            resultado[campo.name] = valor


        # ====================================================
        # 13. RETORNO
        # ====================================================
        #
        # Preservamos a mesma estrutura retornada atualmente.
        #
        # O usuário retornado é apenas a identificação daquele
        # que originou a Execution.
        #
        # Nenhuma informação de autenticação do usuário é
        # exposta.
        # ====================================================

        return {
            "status": "success",
            "execution_id": execution_id,
            "user": {
                "id": usuario.id,
                "username": usuario.username,
                "name": usuario.name,
            },
            "credential": {
                "name": credencial.name,
                "fields": resultado,
            },
        }


    finally:

        # ====================================================
        # FECHA A SESSÃO
        # ====================================================

        db.close()