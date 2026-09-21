# ============================================================
# SERVICE - INSTALADOR DO AGENT
# ============================================================
#
# Responsável pela geração do instalador personalizado
# do RPA Agent.
#
# O service:
#
# - localiza o RPA-Agent.exe;
# - localiza o compilador Inno Setup;
# - cria config.json temporário;
# - cria installer.iss;
# - executa ISCC.exe;
# - retorna o instalador gerado.
#
# O comportamento atual é preservado nesta etapa.
# ============================================================

import json
import logging
import os
import shutil
import subprocess
import tempfile

from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from agents.repository import buscar_agent_por_id
from agents.bootstrap_service import CONTROL_ROOM_URL
# Descriptografa a credencial somente durante a construção
# do config.json temporário do instalador.
from agents.token_security import descriptografar_agent_token

logger = logging.getLogger("control_room")


# ============================================================
# DIRETÓRIO BASE DO CONTROL ROOM
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# EXECUTÁVEL BASE DO AGENT
# ============================================================

AGENT_EXE_PATH = os.path.join(
    BASE_DIR,
    "agent",
    "RPA-Agent.exe",
)


def gerar_instalador_agent_service(
    agent_id: str,
    db: Session,
):
    """
    Gera o instalador personalizado de determinado Agent.

    Parâmetros:
        agent_id:
            Identificador do Agent.

        db:
            Sessão SQLAlchemy fornecida pelo endpoint.

    Retorno:
        FileResponse com o instalador ou o mesmo contrato
        de erro utilizado atualmente pela API.
    """

    # Diretório temporário utilizado durante a construção do
    # instalador.
    #
    # Inicializamos antes do try para permitir que o bloco finally
    # faça a limpeza mesmo quando ocorrer uma exceção no meio do
    # processo.
    temp_dir = None

    try:

        # --------------------------------------------------------
        # 1. BUSCA O AGENT
        # --------------------------------------------------------

        agent = buscar_agent_por_id(
            db,
            agent_id,
        )

        if not agent:
            return {
                "status": "error",
                "message": "Agent não encontrado.",
            }

        # --------------------------------------------------------
        # BLOQUEIA INSTALADOR DE AGENT DESATIVADO
        # --------------------------------------------------------
        #
        # O instalador contém o config.json com agent_token.
        # Portanto, não deve ser possível gerar novamente material
        # de autenticação para um Agent removido logicamente.
        # --------------------------------------------------------

        if agent.is_active != 1:
            return {
                "status": "error",
                "message": "Agent não está ativo.",
            }

        # --------------------------------------------------------
        # 2. VERIFICA O EXECUTÁVEL BASE
        # --------------------------------------------------------

        if not os.path.exists(AGENT_EXE_PATH):

            logger.error(
                "Executável base do Agent não encontrado",
                extra={
                    "event": (
                        "agent_installer_executable_not_found"
                    ),
                    "agent_id": agent_id,
                    "error_message": (
                        f"Arquivo não encontrado: "
                        f"{AGENT_EXE_PATH}"
                    ),
                },
            )

            # O caminho físico permanece disponível no log do
            # Control Room, mas não é exposto pela API.
            return {
                "status": "error",
                "message": (
                    "Executável RPA-Agent.exe não encontrado."
                ),
            }

        # --------------------------------------------------------
        # 3. LOCALIZA O INNO SETUP
        # --------------------------------------------------------

        iscc_path = shutil.which("ISCC.exe")

        if not iscc_path:

            # Caminho alternativo existente no projeto atual.
            caminho_inno = (
                r"C:\Users\Usuario\AppData\Local"
                r"\Programs\Inno Setup 7\ISCC.exe"
            )

            if os.path.exists(caminho_inno):
                iscc_path = caminho_inno

        if not iscc_path:

            logger.error(
                "Compilador do Inno Setup não encontrado",
                extra={
                    "event": (
                        "agent_installer_compiler_not_found"
                    ),
                    "agent_id": agent_id,
                },
            )

            return {
                "status": "error",
                "message": (
                    "Compilador do Inno Setup não encontrado."
                ),
            }

        # --------------------------------------------------------
        # 4. DIRETÓRIO DOS INSTALADORES
        # --------------------------------------------------------

        installers_directory = os.path.join(
            BASE_DIR,
            "generated_installers",
        )

        os.makedirs(
            installers_directory,
            exist_ok=True,
        )

        # --------------------------------------------------------
        # 5. DIRETÓRIO TEMPORÁRIO
        # --------------------------------------------------------

        temp_dir = tempfile.mkdtemp(
            prefix=f"{agent.agent_id}_"
        )

        config_path = os.path.join(
            temp_dir,
            "config.json",
        )

        iss_path = os.path.join(
            temp_dir,
            "installer.iss",
        )

        # --------------------------------------------------------
        # 6. CONFIGURAÇÃO DO AGENT
        # --------------------------------------------------------
        #
        # rpa_directory já representa o diretório configurado
        # para os RPAs. Não adicionamos "\rpas" novamente.
        # --------------------------------------------------------

        rpa_directory = agent.rpa_directory

        # Recupera a credencial somente em memória.
        # O plaintext existe apenas durante a geração
        # deste config.json temporário.
        agent_token = descriptografar_agent_token(
            agent.agent_token_encrypted
        )

        config = {
            "agent_id": agent.agent_id,
            "agent_token": agent_token,
            "control_room_url": CONTROL_ROOM_URL,
            "port": agent.port,
            "rpa_directory": rpa_directory,
        }

        # --------------------------------------------------------
        # 7. GRAVA CONFIG.JSON
        # --------------------------------------------------------

        with open(
            config_path,
            "w",
            encoding="utf-8",
        ) as arquivo:

            json.dump(
                config,
                arquivo,
                indent=4,
                ensure_ascii=False,
            )

        # --------------------------------------------------------
        # 8. NOME DO INSTALADOR
        # --------------------------------------------------------

        installer_filename = (
            f"RPA-Agent-{agent.agent_id}.exe"
        )

        installer_path = os.path.join(
            installers_directory,
            installer_filename,
        )

        # --------------------------------------------------------
        # 9. SCRIPT DO INNO SETUP
        # --------------------------------------------------------
        #
        # Mantemos o template utilizado atualmente pelo
        # Control Room para não alterar o instalador nesta
        # etapa de modularização.
        # --------------------------------------------------------

        iss_content = f'''
            #define MyAppName "RPA Agent - {agent.agent_id}"
            #define MyAppVersion "1.0"
            #define MyAppPublisher "DUET"
            #define MyAppExeName "RPA-Agent.exe"

            [Setup]
            AppId={{{{BFD46468-5320-4174-81AA-B5D94C9892EA}}
            AppName={{#MyAppName}}
            AppVersion={{#MyAppVersion}}
            AppPublisher={{#MyAppPublisher}}

            DefaultDirName=C:\\RPA-Agent
            DisableDirPage=yes

            ArchitecturesAllowed=x64compatible
            ArchitecturesInstallIn64BitMode=x64compatible

            PrivilegesRequired=admin

            OutputDir="{installers_directory}"
            OutputBaseFilename="RPA-Agent-{agent.agent_id}"

            SolidCompression=yes
            WizardStyle=modern

            [Languages]
            Name: "english"; MessagesFile: "compiler:Default.isl"

            [Files]
            Source: "{AGENT_EXE_PATH}"; DestDir: "{{app}}"; Flags: ignoreversion
            Source: "{config_path}"; DestDir: "{{app}}"; Flags: ignoreversion
            Source: "{os.path.join(BASE_DIR, 'rpa', '*')}"; DestDir: "{{app}}\\rpa"; Flags: ignoreversion recursesubdirs createallsubdirs

            [Dirs]
            Name: "{{app}}\\logs"
            Name: "{{app}}\\temp"
            Name: "{{app}}\\rpas"
        '''

        # --------------------------------------------------------
        # 10. GRAVA INSTALLER.ISS
        # --------------------------------------------------------

        with open(
            iss_path,
            "w",
            encoding="utf-8",
        ) as arquivo:

            arquivo.write(
                iss_content
            )

        # --------------------------------------------------------
        # 11. COMPILA O INSTALADOR
        # --------------------------------------------------------

        resultado = subprocess.run(
            [
                iscc_path,
                "/Qp",
                iss_path,
            ],
            capture_output=True,
            text=True,
        )

        # --------------------------------------------------------
        # 12. VALIDA COMPILAÇÃO
        # --------------------------------------------------------

        if resultado.returncode != 0:

            logger.error(
                "Falha ao compilar instalador do Agent",
                extra={
                    "event": (
                        "agent_installer_compilation_failed"
                    ),
                    "agent_id": agent_id,
                    "reason": (
                        f"returncode={resultado.returncode}"
                    ),
                    "error_message": resultado.stderr.strip(),
                },
            )

            # stderr permanece registrado no log interno.
            # Não devolvemos detalhes do compilador ao cliente.
            return {
                "status": "error",
                "message": (
                    "Não foi possível gerar o instalador."
                ),
            }

        # --------------------------------------------------------
        # 13. CONFIRMA ARQUIVO GERADO
        # --------------------------------------------------------

        if not os.path.exists(installer_path):

            logger.error(
                (
                    "Compilação terminou sem gerar "
                    "o instalador esperado"
                ),
                extra={
                    "event": (
                        "agent_installer_output_not_found"
                    ),
                    "agent_id": agent_id,
                    "error_message": (
                        f"Instalador não encontrado: "
                        f"{installer_path}"
                    ),
                },
            )

            # O caminho esperado permanece registrado no log,
            # mas não é exposto pela resposta HTTP.
            return {
                "status": "error",
                "message": (
                    "O Inno Setup terminou, mas o "
                    "instalador não foi encontrado."
                ),
            }

        logger.info(
            "Instalador do Agent gerado com sucesso",
            extra={
                "event": "agent_installer_generated",
                "agent_id": agent_id,
            },
        )

        # --------------------------------------------------------
        # 14. RETORNA O EXECUTÁVEL
        # --------------------------------------------------------

        return FileResponse(
            path=installer_path,
            media_type="application/octet-stream",
            filename=installer_filename,
        )

    except Exception as error:

        # O detalhe técnico fica restrito ao log interno.
        logger.exception(
            "Erro inesperado ao gerar instalador do Agent",
            extra={
                "event": (
                    "agent_installer_generation_failed"
                ),
                "agent_id": agent_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        return {
            "status": "error",
            "message": "Erro ao gerar instalador do Agent.",
        }

    finally:

        # --------------------------------------------------------
        # LIMPEZA DO MATERIAL TEMPORÁRIO
        # --------------------------------------------------------
        #
        # O diretório temporário contém config.json com o
        # agent_token em texto puro durante a construção.
        #
        # A limpeza acontece tanto em sucesso quanto em erro.
        #
        # O instalador final NÃO fica neste diretório; ele é
        # gerado em generated_installers, portanto pode continuar
        # sendo entregue normalmente pelo FileResponse.
        # --------------------------------------------------------

        if temp_dir and os.path.isdir(temp_dir):

            try:
                shutil.rmtree(temp_dir)

            except Exception as cleanup_error:

                # Falha de limpeza não deve substituir o resultado
                # principal da geração do instalador.
                #
                # Registramos o incidente para auditoria.
                logger.error(
                    "Não foi possível remover diretório temporário "
                    "do instalador do Agent",
                    extra={
                        "event": (
                            "agent_installer_temp_cleanup_failed"
                        ),
                        "agent_id": agent_id,
                        "error_type": type(cleanup_error).__name__,
                        "error_message": str(cleanup_error),
                    },
                )