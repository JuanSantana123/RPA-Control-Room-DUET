# ============================================================
# VAULT - MASTER KEY SERVICE
# ============================================================
#
# Regras de negócio relacionadas à administração criptográfica
# da Master Key do Vault.
#
# Responsabilidades deste módulo:
#
# - exportar a Master Key em formato portátil;
# - importar uma Master Key a partir de backup;
# - preservar o tratamento de erros atual;
# - registrar somente informações administrativas seguras.
#
# IMPORTANTE:
#
# Este módulo NÃO:
#
# - registra rotas FastAPI;
# - define RBAC;
# - recebe Depends();
# - registra senha de recuperação;
# - registra a Master Key;
# - registra o conteúdo do backup.
#
# A camada HTTP continuará em api/vault_credentials.py.
# ============================================================

import logging

from fastapi import HTTPException, UploadFile
from fastapi.responses import Response

from vault.crypto import (
    exportar_chave_mestra,
    importar_chave_mestra,
)


# ============================================================
# LOGGER
# ============================================================
#
# Utiliza o mesmo logger estruturado configurado pelo
# Control Room em main.py.
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# EXPORTAR MASTER KEY
# ============================================================

def exportar_master_key_vault_service(
    senha_recuperacao: str,
    usuario,
):
    """
    Exporta a Master Key atual do Vault.

    Parâmetros
    ----------
    senha_recuperacao:
        Senha utilizada para proteger o arquivo portátil.

    usuario:
        Usuário autenticado que solicitou a operação.

        É utilizado exclusivamente para auditoria administrativa.

    Retorno
    -------
    Response
        Arquivo binário:

            vault-backup.key

    Segurança
    ---------
    A senha de recuperação, a Master Key e o conteúdo do arquivo
    nunca são registrados nos logs.
    """

    try:

        # --------------------------------------------------------
        # GERA O BACKUP PORTÁTIL
        # --------------------------------------------------------
        #
        # A implementação criptográfica permanece isolada em
        # vault_crypto.py.
        # --------------------------------------------------------

        conteudo_backup = exportar_chave_mestra(
            senha_recuperacao
        )


        # --------------------------------------------------------
        # LOG ADMINISTRATIVO
        # --------------------------------------------------------
        #
        # Nunca registrar:
        #
        # - senha de recuperação;
        # - Master Key;
        # - conteúdo do arquivo.
        # --------------------------------------------------------

        logger.info(
            "[VAULT] Master Key exportada | "
            f"Usuário: {usuario.username}"
        )


        # --------------------------------------------------------
        # DEVOLVE O ARQUIVO PARA DOWNLOAD
        # --------------------------------------------------------
        #
        # Preservamos exatamente:
        #
        # - application/octet-stream;
        # - nome vault-backup.key.
        # --------------------------------------------------------

        return Response(
            content=conteudo_backup,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": (
                    'attachment; filename="vault-backup.key"'
                )
            },
        )


    except ValueError as error:

        # --------------------------------------------------------
        # ERRO DE VALIDAÇÃO
        # --------------------------------------------------------
        #
        # Exemplo:
        # senha de recuperação inválida ou insuficiente.
        # --------------------------------------------------------

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    except Exception as error:

        # --------------------------------------------------------
        # ERRO NÃO PREVISTO
        # --------------------------------------------------------
        #
        # O erro administrativo pode ser registrado.
        #
        # Nenhum segredo é incluído no log.
        # --------------------------------------------------------

        logger.error(
            "[VAULT] Erro ao exportar Master Key | "
            f"Usuário: {usuario.username} | "
            f"Erro: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível exportar a Master Key do Vault."
            ),
        )


# ============================================================
# IMPORTAR MASTER KEY
# ============================================================

async def importar_master_key_vault_service(
    arquivo: UploadFile,
    senha_recuperacao: str,
    usuario,
):
    """
    Importa uma Master Key portátil.

    Parâmetros
    ----------
    arquivo:
        UploadFile correspondente ao vault-backup.key.

    senha_recuperacao:
        Senha utilizada quando o backup foi exportado.

    usuario:
        Usuário autenticado responsável pela operação.

    Segurança
    ---------
    A função importar_chave_mestra() continua sendo responsável
    pelas proteções criptográficas e pela proteção contra
    sobrescrita indevida de uma Master Key existente.

    Este service preserva o comportamento HTTP atual.
    """

    try:

        # --------------------------------------------------------
        # VALIDA NOME DO ARQUIVO
        # --------------------------------------------------------

        if not arquivo.filename:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nenhum arquivo de backup foi informado."
                ),
            )


        # --------------------------------------------------------
        # LÊ O BACKUP RECEBIDO
        # --------------------------------------------------------

        conteudo_backup = await arquivo.read()


        if not conteudo_backup:

            raise HTTPException(
                status_code=400,
                detail=(
                    "O arquivo de backup está vazio."
                ),
            )


        # --------------------------------------------------------
        # IMPORTA A MASTER KEY
        # --------------------------------------------------------
        #
        # A lógica criptográfica continua em vault_crypto.py.
        # --------------------------------------------------------

        resultado = importar_chave_mestra(
            conteudo_backup=conteudo_backup,
            senha_recuperacao=senha_recuperacao,
        )


        # --------------------------------------------------------
        # LOG ADMINISTRATIVO
        # --------------------------------------------------------
        #
        # Não registrar:
        #
        # - senha;
        # - Master Key;
        # - conteúdo do arquivo.
        # --------------------------------------------------------

        logger.info(
            "[VAULT] Master Key importada | "
            f"Usuário: {usuario.username} | "
            f"Arquivo: {arquivo.filename}"
        )


        return resultado


    except HTTPException:

        # HTTPExceptions criadas pelo próprio service precisam
        # manter exatamente o status/detail original.

        raise


    except ValueError as error:

        # Erros de validação continuam sendo HTTP 400.

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    except RuntimeError as error:

        # --------------------------------------------------------
        # ERROS OPERACIONAIS ESPERADOS
        # --------------------------------------------------------
        #
        # RuntimeError pode representar:
        #
        # - senha incorreta;
        # - backup inválido;
        # - backup corrompido;
        # - master.key já existente;
        # - versão não suportada.
        # --------------------------------------------------------

        logger.warning(
            "[VAULT] Importação da Master Key bloqueada | "
            f"Usuário: {usuario.username} | "
            f"Arquivo: {arquivo.filename} | "
            f"Motivo: {error}"
        )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    except Exception as error:

        # --------------------------------------------------------
        # ERRO NÃO PREVISTO
        # --------------------------------------------------------

        logger.error(
            "[VAULT] Erro ao importar Master Key | "
            f"Usuário: {usuario.username} | "
            f"Arquivo: {arquivo.filename} | "
            f"Erro: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível importar a Master Key do Vault."
            ),
        )