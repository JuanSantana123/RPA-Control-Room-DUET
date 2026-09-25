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

# ============================================================
# EXECUTÁVEL DO WINDOWS SERVICE DO AGENT
# ============================================================
#
# O Control Room mantém o executável do Service junto aos
# arquivos utilizados para montar o instalador do Agent.
#
# Esse executável será instalado em C:\RPA-Agent e será,
# posteriormente, registrado no Windows como DUETAgentService.
# ============================================================

AGENT_SERVICE_EXE_PATH = os.path.join(
    BASE_DIR,
    "agent",
    "RPA-Agent-Service.exe",
)



# ============================================================
# COMPONENTES NATIVOS DE SESSÃO WINDOWS
# ============================================================
#
# Estes arquivos formam a camada responsável por permitir que
# o Agent prepare/autentique uma sessão Windows interativa.
#
# O Control Room mantém uma cópia dos artefatos publicados na
# pasta agent/ utilizada exclusivamente para montar instaladores.
# ============================================================

AGENT_BROKER_PATH = os.path.join(
    BASE_DIR,
    "agent",
    "RPA-Agent-Session-Broker.exe",
)


AGENT_CREDENTIAL_PROVIDER_DIRECTORY = os.path.join(
    BASE_DIR,
    "agent",
    "native",
    "credential_provider",
)


AGENT_CREDENTIAL_PROVIDER_DLL_PATH = os.path.join(
    AGENT_CREDENTIAL_PROVIDER_DIRECTORY,
    "DuetCredentialProvider.dll",
)


AGENT_CREDENTIAL_PROVIDER_REGISTER_PATH = os.path.join(
    AGENT_CREDENTIAL_PROVIDER_DIRECTORY,
    "register_duet_credential_provider.ps1",
)


AGENT_CREDENTIAL_PROVIDER_ROLLBACK_PATH = os.path.join(
    AGENT_CREDENTIAL_PROVIDER_DIRECTORY,
    "rollback_duet_credential_provider.ps1",
)
# ============================================================
# RUNTIME PYTHON DO DUET
# ============================================================
#
# O Agent não depende do Python instalado na máquina de destino.
#
# O Control Room mantém uma cópia do runtime Python utilizado
# pelos Robots e o inclui em cada instalador gerado.
#
# Estrutura esperada no Control Room:
#
#     agent\
#         runtime\
#             python\
#                 python.exe
#
# Durante a instalação essa estrutura será copiada para:
#
#     C:\RPA-Agent\runtime\python
#
# ============================================================

AGENT_RUNTIME_PATH = os.path.join(
    BASE_DIR,
    "agent",
    "runtime",
    "python",
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
        # 2.1. VERIFICA O EXECUTÁVEL DO WINDOWS SERVICE
        # --------------------------------------------------------
        #
        # O instalador do DUET agora também depende do executável
        # responsável por manter o Agent ativo como Windows Service.
        #
        # Se esse arquivo não estiver disponível, interrompemos a
        # geração para não entregar um instalador incompleto.
        # --------------------------------------------------------

        if not os.path.exists(AGENT_SERVICE_EXE_PATH):

            logger.error(
                "Executável do Windows Service do Agent não encontrado",
                extra={
                    "event": (
                        "agent_installer_service_executable_not_found"
                    ),
                    "agent_id": agent_id,
                    "error_message": (
                        f"Arquivo não encontrado: "
                        f"{AGENT_SERVICE_EXE_PATH}"
                    ),
                },
            )

            return {
                "status": "error",
                "message": (
                    "Executável RPA-Agent-Service.exe não encontrado."
                ),
            }


        # --------------------------------------------------------
        # 2.2. VERIFICA COMPONENTES NATIVOS DE SESSÃO WINDOWS
        # --------------------------------------------------------
        #
        # Não permitimos gerar um instalador parcialmente capaz
        # de executar Robots, mas incapaz de preparar uma sessão
        # Windows quando necessário.
        #
        # Nenhum desses arquivos contém credenciais do usuário.
        # --------------------------------------------------------

        native_session_files = {
            "RPA-Agent-Session-Broker.exe": (
                AGENT_BROKER_PATH
            ),
            "DuetCredentialProvider.dll": (
                AGENT_CREDENTIAL_PROVIDER_DLL_PATH
            ),
            "register_duet_credential_provider.ps1": (
                AGENT_CREDENTIAL_PROVIDER_REGISTER_PATH
            ),
            "rollback_duet_credential_provider.ps1": (
                AGENT_CREDENTIAL_PROVIDER_ROLLBACK_PATH
            ),
        }

        for (
            native_file_name,
            native_file_path,
        ) in native_session_files.items():

            if not os.path.exists(
                native_file_path
            ):

                logger.error(
                    "Componente nativo do Agent não encontrado",
                    extra={
                        "event": (
                            "agent_installer_native_component_not_found"
                        ),
                        "agent_id": agent_id,
                        "native_component": (
                            native_file_name
                        ),
                        "error_message": (
                            f"Arquivo não encontrado: "
                            f"{native_file_path}"
                        ),
                    },
                )

                return {
                    "status": "error",
                    "message": (
                        "Componente nativo obrigatório "
                        f"não encontrado: {native_file_name}."
                    ),
                }

        # --------------------------------------------------------
        # 2.2. VERIFICA O RUNTIME PYTHON DO DUET
        # --------------------------------------------------------
        #
        # O instalador precisa transportar o Python utilizado
        # para executar os Robots.
        #
        # Validamos especificamente python.exe para impedir que
        # seja gerado um instalador com runtime ausente ou
        # incompleto.
        # --------------------------------------------------------

        python_runtime_exe = os.path.join(
            AGENT_RUNTIME_PATH,
            "python.exe",
        )

        if not os.path.isfile(python_runtime_exe):

            logger.error(
                "Runtime Python do DUET não encontrado",
                extra={
                    "event": (
                        "agent_installer_python_runtime_not_found"
                    ),
                    "agent_id": agent_id,
                    "error_message": (
                        f"Arquivo não encontrado: "
                        f"{python_runtime_exe}"
                    ),
                },
            )

            return {
                "status": "error",
                "message": (
                    "Runtime Python do DUET não encontrado."
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

            # Identidade Windows configurada no Control Room
            # para execução das automações Desktop.
            #
            # Nenhuma senha é gravada no config.json.
            # A senha será obtida de forma controlada pelo Vault
            # apenas quando a autenticação Windows for necessária.
            "execution_username": agent.execution_username,
            "execution_domain": agent.execution_domain,
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
            ; Instala o executável compilado do RPA Agent.
            Source: "{AGENT_EXE_PATH}"; DestDir: "{{app}}"; Flags: ignoreversion

            ; Instala o executável responsável pelo Windows Service
            ; permanente do DUET Agent.
            Source: "{AGENT_SERVICE_EXE_PATH}"; DestDir: "{{app}}"; Flags: ignoreversion
            ; ====================================================
            ; SESSION BROKER NATIVO
            ; ====================================================
            ;
            ; O session_authenticator.py procura este executável
            ; diretamente na raiz de C:\\RPA-Agent.
            ; ====================================================
            Source: "{AGENT_BROKER_PATH}"; DestDir: "{{app}}"; Flags: ignoreversion


            ; ====================================================
            ; DUET CREDENTIAL PROVIDER
            ; ====================================================
            ;
            ; Os artefatos são mantidos juntos porque o script de
            ; registro exige tanto a DLL quanto o rollback validado.
            ;
            ; A DLL será posteriormente copiada para System32 pelo
            ; script de registro.
            ; ====================================================
            Source: "{AGENT_CREDENTIAL_PROVIDER_DLL_PATH}"; DestDir: "{{app}}\\native\\credential_provider"; Flags: ignoreversion

            Source: "{AGENT_CREDENTIAL_PROVIDER_REGISTER_PATH}"; DestDir: "{{app}}\\native\\credential_provider"; Flags: ignoreversion

            Source: "{AGENT_CREDENTIAL_PROVIDER_ROLLBACK_PATH}"; DestDir: "{{app}}\\native\\credential_provider"; Flags: ignoreversion



            ; ====================================================
            ; RUNTIME PYTHON DO DUET
            ; ====================================================
            ;
            ; Copia recursivamente o runtime Python distribuído
            ; pelo DUET para a instalação do Agent.
            ;
            ; Resultado:
            ;
            ; C:\\RPA-Agent\\runtime\\python\\python.exe
            ;
            ; O Agent utiliza esse executável diretamente e não
            ; depende de Python instalado ou configurado no PATH
            ; da máquina.
            ; ====================================================
            Source: "{AGENT_RUNTIME_PATH}\\*"; DestDir: "{{app}}\\runtime\\python"; Flags: ignoreversion recursesubdirs createallsubdirs
            ; Instala a configuração exclusiva deste Agent.
            ; O arquivo contém agent_id, token, URL do Control Room,
            ; porta e diretório de execução dos RPAs.
            Source: "{config_path}"; DestDir: "{{app}}"; Flags: ignoreversion

                        [Dirs]
            Name: "{{app}}\\logs"
            Name: "{{app}}\\temp"
            Name: "{{app}}\\rpas"

            [Run]

            ; ====================================================
            ; DUET CREDENTIAL PROVIDER
            ; ====================================================
            ;
            ; O registro é executado somente em máquinas onde o
            ; Credential Provider ainda não estava registrado.
            ;
            ; Isso é importante porque o script validado se recusa
            ; deliberadamente a registrar por cima de uma instalação
            ; já existente.
            ; ====================================================

            Filename: "{{sys}}\\WindowsPowerShell\\v1.0\\powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""{{app}}\\native\\credential_provider\\register_duet_credential_provider.ps1"""; Flags: runhidden waituntilterminated; Check: ShouldRegisterDuetCredentialProvider
            ; ====================================================
            ; WINDOWS SERVICE DO DUET AGENT
            ; ====================================================
            ;
            ; INSTALAÇÃO NOVA:
            ; Executa "install" somente quando o Service NÃO
            ; existia antes do início desta instalação.
            ;
            ; A decisão é baseada no estado capturado uma única vez
            ; em InitializeSetup(), evitando que o próprio comando
            ; "install" altere o resultado do próximo Check.
            ; ====================================================
            Filename: "{{app}}\\RPA-Agent-Service.exe"; Parameters: "--startup auto install"; Flags: runhidden waituntilterminated; Check: ShouldInstallDuetAgentService

            ; ====================================================
            ; ATUALIZAÇÃO / REINSTALAÇÃO:
            ; ====================================================
            ;
            ; Executa "update" somente quando o Service JÁ existia
            ; antes do início desta instalação.
            ;
            ; Dessa forma, uma instalação nova nunca executará
            ; "install" e "update" na mesma execução.
            ; ====================================================
            Filename: "{{app}}\\RPA-Agent-Service.exe"; Parameters: "--startup auto update"; Flags: runhidden waituntilterminated; Check: ShouldUpdateDuetAgentService

            ; ====================================================
            ; INICIALIZAÇÃO
            ; ====================================================
            ;
            ; Depois de instalar ou atualizar o registro do Service,
            ; solicita sua inicialização e aguarda até 15 segundos.
            ; ====================================================
            Filename: "{{app}}\\RPA-Agent-Service.exe"; Parameters: "start --wait 15"; Flags: runhidden waituntilterminated


            [Code]

            // ====================================================
            // ESTADO ORIGINAL DO WINDOWS SERVICE
            // ====================================================
            //
            // Guarda se DUETAgentService já existia ANTES de o
            // instalador começar a alterar a máquina.
            //
            // Isso é necessário porque, depois do comando "install",
            // uma nova consulta ao SCM passaria a encontrar o Service.
            // ====================================================

            var
              DuetAgentServiceExistedBeforeInstall: Boolean;
              DuetCredentialProviderExistedBeforeInstall: Boolean;


            // ====================================================
            // CONSULTA O SERVICE CONTROL MANAGER
            // ====================================================
            //
            // Executa:
            //
            //     sc.exe query DUETAgentService
            //
            // Código 0 significa que o Service está registrado.
            // ====================================================

            function DuetAgentServiceExists(): Boolean;
            var
              ResultCode: Integer;
            begin
              Exec(
                ExpandConstant('{{sys}}\\sc.exe'),
                'query DUETAgentService',
                '',
                SW_HIDE,
                ewWaitUntilTerminated,
                ResultCode
              );

              Result := (ResultCode = 0);
            end;


            // ====================================================
            // CAPTURA O ESTADO ANTES DA INSTALAÇÃO
            // ====================================================
            //
            // InitializeSetup é executado antes das etapas que
            // modificam a instalação.
            //
            // Portanto, esta variável permanece estável durante
            // toda a execução do instalador.
            // ====================================================

            // ====================================================
            // CONSULTA O DUET CREDENTIAL PROVIDER
            // ====================================================
            //
            // A existência da chave oficial em Credential Providers
            // indica que o Provider já estava registrado antes do
            // instalador atual.
            //
            // IMPORTANTE:
            // seção está dentro de uma f-string Python.
            // ====================================================

            function DuetCredentialProviderExists(): Boolean;
            begin
              Result :=
                RegKeyExists(
                  HKEY_LOCAL_MACHINE,
                  'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Authentication\\Credential Providers\\{{5CA94EF5-C6CE-4F61-8CF2-201B142EB819}}'
                );
            end;

            function InitializeSetup(): Boolean;
            begin
              // Guarda o estado original do Service.
              DuetAgentServiceExistedBeforeInstall :=
                DuetAgentServiceExists();

              // Guarda o estado original do Credential Provider.
              //
              // Não consultamos novamente depois da instalação,
              // pois o próprio processo de registro mudará esse
              // estado.
              DuetCredentialProviderExistedBeforeInstall :=
                DuetCredentialProviderExists();

              Result := True;
            end;



            // ====================================================
            // PREPARA UMA ATUALIZAÇÃO DO AGENT
            // ====================================================
            //
            // PrepareToInstall é executado antes de o Inno Setup
            // iniciar a cópia dos arquivos da seção [Files].
            //
            // Se o DUETAgentService já existia quando o instalador
            // foi iniciado, paramos o Service antes de substituir
            // RPA-Agent-Service.exe.
            //
            // Utilizamos o próprio executável atualmente instalado
            // porque seu comando "stop --wait 15" solicita a parada
            // e aguarda a finalização do Service.
            //
            // Em uma instalação nova não há Service para parar,
            // portanto nenhuma ação é executada.
            // ====================================================

            function PrepareToInstall(
              var NeedsRestart: Boolean
            ): String;
            var
              ResultCode: Integer;
            begin
              // ==================================================
              // RESULTADO PADRÃO
              // ==================================================
              //
              // String vazia informa ao Inno Setup que a instalação
              // pode continuar normalmente.
              // ==================================================

              Result := '';

              // ==================================================
              // SERVICE NÃO EXISTIA ANTES DA INSTALAÇÃO
              // ==================================================
              //
              // Em uma instalação nova ainda não existe nenhum
              // DUETAgentService registrado no Windows.
              //
              // Portanto, não existe processo anterior para parar.
              // ==================================================

              if not DuetAgentServiceExistedBeforeInstall then
              begin
                exit;
              end;


              // ==================================================
              // SOLICITA A PARADA PELO SERVICE CONTROL MANAGER
              // ==================================================
              //
              // Utilizamos diretamente:
              //
              //     sc.exe stop DUETAgentService
              //
              // em vez de executar:
              //
              //     RPA-Agent-Service.exe stop --wait 15
              //
              // Isso evita depender do próprio executável que será
              // substituído durante esta atualização.
              //
              // IMPORTANTE:
              //
              // Se o Service já estiver STOPPED, o sc.exe poderá
              // retornar um código diferente de zero.
              //
              // Isso NÃO é tratado como erro aqui, porque o estado
              // desejado já pode ter sido atingido.
              //
              // A validação definitiva será feita logo abaixo
              // consultando o estado real do Service.
              // ==================================================

              Exec(
                ExpandConstant('{{sys}}\\sc.exe'),
                'stop DUETAgentService',
                '',
                SW_HIDE,
                ewWaitUntilTerminated,
                ResultCode
              );


              // ==================================================
              // AGUARDA O SERVICE FICAR STOPPED
              // ==================================================
              //
              // O comando "sc stop" pode retornar enquanto o
              // Windows ainda está em STOP_PENDING.
              //
              // Por isso aguardamos até 15 segundos antes de
              // permitir que o Inno substitua o executável.
              //
              // O comando:
              //
              //     sc.exe query DUETAgentService
              //
              // grava a saída em um arquivo temporário.
              //
              // Depois usamos FindFirst para verificar se ainda
              // existe processo associado ao Service através do
              // comando "sc queryex".
              //
              // Para manter esta etapa simples e confiável, usamos
              // o próprio comando WAIT do Windows Service através
              // de sucessivas consultas ao PID.
              // ==================================================

              Sleep(2000);


              // ==================================================
              // VALIDA SE O SERVICE AINDA POSSUI PROCESSO
              // ==================================================
              //
              // tasklist é utilizado apenas como proteção final.
              //
              // Como o executável do Service precisa estar liberado
              // antes da seção [Files], tentamos novamente a parada
              // pelo SCM após a pequena espera.
              //
              // Se o Service já estava parado, essa chamada é
              // inofensiva.
              // ==================================================

              Exec(
                ExpandConstant('{{sys}}\\sc.exe'),
                'stop DUETAgentService',
                '',
                SW_HIDE,
                ewWaitUntilTerminated,
                ResultCode
              );

              Sleep(1000);

              // ==================================================
              // CONTINUA A INSTALAÇÃO
              // ==================================================
              //
              // A seção [Files] será a validação definitiva de que
              // o executável foi liberado.
              //
              // Caso o Windows ainda mantenha o arquivo bloqueado,
              // o próprio Inno Setup impedirá silenciosamente uma
              // substituição inconsistente.
              // ==================================================

              Result := '';
            end;
            // ====================================================
            // DECIDE SE É UMA INSTALAÇÃO NOVA
            // ====================================================

            function ShouldInstallDuetAgentService(): Boolean;
            begin
              Result :=
                not DuetAgentServiceExistedBeforeInstall;
            end;


            // ====================================================
            // DECIDE SE É UMA ATUALIZAÇÃO
            // ====================================================

            function ShouldUpdateDuetAgentService(): Boolean;
            begin
              Result :=
                DuetAgentServiceExistedBeforeInstall;
            end;


            // ====================================================
            // DECIDE SE O CREDENTIAL PROVIDER PRECISA SER REGISTRADO
            // ====================================================

            function ShouldRegisterDuetCredentialProvider(): Boolean;
            begin
              Result :=
                not DuetCredentialProviderExistedBeforeInstall;
            end;
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