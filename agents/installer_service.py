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
import uuid

from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session

from agents.repository import buscar_agent_por_id
from agents.bootstrap_service import CONTROL_ROOM_URL
# Descriptografa a credencial somente durante a construção
# do config.json temporário do instalador.
from agents.token_security import descriptografar_agent_token

logger = logging.getLogger("control_room")


# ============================================================
# LIMPEZA SEGURA DE INSTALADOR TEMPORÁRIO
# ============================================================
#
# Cada requisição de download passa a gerar um arquivo físico
# exclusivo. Isso evita que duas requisições simultâneas tentem
# sobrescrever o mesmo .exe enquanto uma delas ainda está sendo
# transmitida ao navegador.
#
# O arquivo é removido somente DEPOIS que o FileResponse termina
# de enviá-lo ao cliente.
# ============================================================

def _remover_instalador_apos_download(
    installer_path: str,
) -> None:
    """
    Remove o instalador físico gerado para uma única requisição.

    A falha de limpeza não pode quebrar uma resposta que já foi
    entregue ao usuário, por isso ela é apenas registrada em log.
    """

    try:
        if os.path.isfile(installer_path):
            os.remove(installer_path)

    except Exception as cleanup_error:
        logger.warning(
            "Não foi possível remover instalador temporário após download",
            extra={
                "event": "agent_installer_cleanup_failed",
                "installer_path": installer_path,
                "error_message": str(cleanup_error),
            },
        )


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
# TOOLING PYTHON DO DUET
# ============================================================
#
# O DUET NÃO distribui, instala, atualiza ou gerencia Python.
# Python é um pré-requisito externo da máquina de destino e pode
# estar instalado para a máquina ou somente para um usuário.
#
# O uv.exe acompanha o Agent somente para:
# - criar environments isoladas dos Robots;
# - instalar dependências de requirements.txt;
# - reutilizar o cache local de pacotes.
#
# O EnvironmentInstaller usa o uv com proteção para não baixar
# nem gerenciar runtimes Python.
# ============================================================

AGENT_UV_PATH = os.path.join(
    BASE_DIR,
    "agent",
    "tools",
    "uv.exe",
)

# ============================================================
# SDK OFICIAL DO DUET RPA
# ============================================================
#
# O SDK é disponibilizado automaticamente para todos os Robots
# executados pelo DUET Agent.
#
# O desenvolvedor pode utilizar:
#
#     from rpa import vault
#
# sem adicionar a SDK ao requirements.txt.
#
# A cópia publicada da SDK utilizada pelo instalador fica em:
#
#     RPA-Control-Room\agent\sdk\rpa
#
# Durante a instalação ela será copiada para:
#
#     C:\RPA-Agent\sdk\rpa
#
# O Agent adiciona C:\RPA-Agent\sdk ao PYTHONPATH do Robot.
# ============================================================

AGENT_SDK_DIRECTORY = os.path.join(
    BASE_DIR,
    "agent",
    "sdk",
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
        # 2.2. VERIFICA O UV.EXE DO DUET
        # --------------------------------------------------------
        #
        # O DUET não transporta Python. Entretanto, o instalador
        # precisa transportar o uv.exe usado para criar environments
        # isoladas dos Robots que possuem requirements.txt.
        # --------------------------------------------------------

        if not os.path.isfile(AGENT_UV_PATH):

            logger.error(
                "uv.exe do DUET não encontrado",
                extra={
                    "event": "agent_installer_uv_not_found",
                    "agent_id": agent_id,
                    "error_message": (
                        f"Arquivo não encontrado: {AGENT_UV_PATH}"
                    ),
                },
            )

            return {
                "status": "error",
                "message": (
                    "Componente obrigatório uv.exe não encontrado."
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

            # Configuração do Python definida pelo usuário durante
            # a instalação do Agent.
            #
            # Os placeholders abaixo são substituídos pelo próprio
            # instalador Inno Setup após copiar o config.json.
            "python_mode": "__DUET_PYTHON_MODE__",
            "python_executable": "__DUET_PYTHON_EXECUTABLE__",
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

        # Nome apresentado ao usuário no download.
        #
        # Este nome permanece estável e amigável.
        installer_filename = (
            f"RPA-Agent-{agent.agent_id}.exe"
        )

        # Nome físico exclusivo desta compilação.
        #
        # NÃO reutilizamos mais RPA-Agent-{agent_id}.exe como arquivo
        # físico de build. Duas requisições simultâneas poderiam fazer
        # o ISCC sobrescrever o arquivo enquanto o FileResponse ainda
        # o estivesse enviando, causando Content-Length inconsistente.
        installer_build_id = uuid.uuid4().hex

        installer_output_base = (
            f"RPA-Agent-{agent.agent_id}-{installer_build_id}"
        )

        installer_path = os.path.join(
            installers_directory,
            f"{installer_output_base}.exe",
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
            OutputBaseFilename="{installer_output_base}"

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
            ; SDK OFICIAL DO DUET RPA
            ; ====================================================
            ;
            ; Disponibiliza a API Python nativa da plataforma para
            ; todos os Robots executados pelo Agent.
            ;
            ; Exemplo:
            ;
            ;     from rpa import vault
            ;
            ; A SDK não faz parte do requirements.txt do Robot.
            ; Ela é uma capacidade fornecida pela plataforma DUET.
            ;
            ; recursesubdirs:
            ;     copia também todos os módulos e subdiretórios
            ;     adicionados futuramente à SDK.
            ;
            ; createallsubdirs:
            ;     preserva toda a estrutura interna da SDK.
            ; ====================================================

            Source: "{AGENT_SDK_DIRECTORY}\\*"; DestDir: "{{app}}\\sdk"; Flags: ignoreversion recursesubdirs createallsubdirs

            ; ====================================================
            ; UV.EXE - TOOLING DO DUET
            ; ====================================================
            ;
            ; Python NÃO é distribuído pelo DUET.
            ; O uv.exe acompanha o Agent somente para criar/reutilizar
            ; environments e instalar dependências dos Robots.
            ; ====================================================
            Source: "{AGENT_UV_PATH}"; DestDir: "{{app}}\\tools"; Flags: ignoreversion


            ; Instala a configuração exclusiva deste Agent.
            ; O arquivo contém agent_id, token, URL do Control Room,
            ; porta e diretório de execução dos RPAs.
            Source: "{config_path}"; DestDir: "{{app}}"; Flags: ignoreversion; AfterInstall: PersistPythonConfiguration

                        [Dirs]
            Name: "{{app}}\\logs"
            Name: "{{app}}\\temp"
            Name: "{{app}}\\rpas"

            ; Estrutura de execução e isolamento dos Robots.
            Name: "{{app}}\\work"
            Name: "{{app}}\\tools"
            ; SDK oficial do DUET disponibilizada para os Robots.
            Name: "{{app}}\\sdk"
            Name: "{{app}}\\environments"
            Name: "{{app}}\\cache"
            Name: "{{app}}\\cache\\uv"
            Name: "{{app}}\\data"

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

              // Página do instalador responsável pela escolha do
              // runtime Python usado pelo DUET Agent.
              PythonModePage: TInputOptionWizardPage;
              PythonPathPage: TInputFileWizardPage;

              // Caminho localizado no modo Automático.
              // Ele será gravado no config.json para que o Service não
              // dependa do PATH/HKCU do usuário após a instalação.
              DetectedPythonPath: String;

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

            // ====================================================
            // PYTHON EXTERNO DA MÁQUINA / USUÁRIO
            // ====================================================
            //
            // O DUET não instala, baixa ou atualiza Python.
            //
            // Durante a instalação o usuário pode escolher:
            //
            //   1. Automático:
            //      o DUET procura uma instalação Python válida tanto
            //      para a máquina quanto para usuários do Windows.
            //
            //   2. Personalizado:
            //      o usuário aponta explicitamente para python.exe.
            //
            // No modo Automático o caminho REAL detectado é gravado no
            // config.json. Assim o DUETAgentService, que roda como
            // LocalSystem, não depende do PATH/HKCU do usuário.
            // ====================================================

            function IsWindowsAppsPython(
              const PythonPath: String
            ): Boolean;
            var
              NormalizedPath: String;
            begin
              NormalizedPath := LowerCase(PythonPath);
              StringChangeEx(
                NormalizedPath,
                '/',
                '\\',
                True
              );

              Result :=
                Pos('\\windowsapps\\', NormalizedPath) > 0;
            end;


            function ValidatePythonExecutable(
              const PythonPath: String
            ): Boolean;
            var
              ResultCode: Integer;
            begin
              Result := False;

              if Trim(PythonPath) = '' then
              begin
                exit;
              end;

              // App Execution Alias / Microsoft Store não é utilizado
              // como runtime base do Windows Service.
              if IsWindowsAppsPython(PythonPath) then
              begin
                exit;
              end;

              if not FileExists(PythonPath) then
              begin
                exit;
              end;

              Result := Exec(
                PythonPath,
                '-c "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)"',
                '',
                SW_HIDE,
                ewWaitUntilTerminated,
                ResultCode
              ) and (ResultCode = 0);
            end;


            function AcceptPythonCandidate(
              const Candidate: String;
              var PythonPath: String
            ): Boolean;
            begin
              Result := ValidatePythonExecutable(
                Candidate
              );

              if Result then
              begin
                PythonPath := Candidate;
              end;
            end;


            function FindPythonInRegistryBase(
              const RootKey: HKEY;
              const BaseKey: String;
              var PythonPath: String
            ): Boolean;
            var
              Companies: TArrayOfString;
              Tags: TArrayOfString;
              CompanyIndex: Integer;
              TagIndex: Integer;
              CompanyKey: String;
              InstallKey: String;
              ExecutablePath: String;
              InstallDirectory: String;
            begin
              Result := False;

              if not RegGetSubkeyNames(
                RootKey,
                BaseKey,
                Companies
              ) then
              begin
                exit;
              end;

              for CompanyIndex := 0 to GetArrayLength(Companies) - 1 do
              begin
                CompanyKey :=
                  BaseKey + '\\' + Companies[CompanyIndex];

                if not RegGetSubkeyNames(
                  RootKey,
                  CompanyKey,
                  Tags
                ) then
                begin
                  continue;
                end;

                // Percorremos do último para o primeiro para favorecer
                // tags mais novas na organização usual do PythonCore.
                for TagIndex := GetArrayLength(Tags) - 1 downto 0 do
                begin
                  InstallKey :=
                    CompanyKey + '\\' + Tags[TagIndex] + '\\InstallPath';

                  ExecutablePath := '';

                  if RegQueryStringValue(
                    RootKey,
                    InstallKey,
                    'ExecutablePath',
                    ExecutablePath
                  ) then
                  begin
                    if AcceptPythonCandidate(
                      ExecutablePath,
                      PythonPath
                    ) then
                    begin
                      Result := True;
                      exit;
                    end;
                  end;

                  InstallDirectory := '';

                  if RegQueryStringValue(
                    RootKey,
                    InstallKey,
                    '',
                    InstallDirectory
                  ) then
                  begin
                    ExecutablePath := PathCombine(
                      InstallDirectory,
                      'python.exe'
                    );

                    if AcceptPythonCandidate(
                      ExecutablePath,
                      PythonPath
                    ) then
                    begin
                      Result := True;
                      exit;
                    end;
                  end;
                end;
              end;
            end;


            function FindPythonInMachineRegistry(
              var PythonPath: String
            ): Boolean;
            begin
              Result := False;

              // Instalações 64 bits registradas para a máquina.
              if IsWin64 then
              begin
                if FindPythonInRegistryBase(
                  HKEY_LOCAL_MACHINE_64,
                  'SOFTWARE\\Python',
                  PythonPath
                ) then
                begin
                  Result := True;
                  exit;
                end;
              end;

              // Instalações 32 bits registradas para a máquina.
              if FindPythonInRegistryBase(
                HKEY_LOCAL_MACHINE_32,
                'SOFTWARE\\Python',
                PythonPath
              ) then
              begin
                Result := True;
                exit;
              end;
            end;


            function FindPythonInLoadedUserRegistry(
              var PythonPath: String
            ): Boolean;
            var
              UserSids: TArrayOfString;
              UserIndex: Integer;
              UserBaseKey: String;
            begin
              Result := False;

              // O instalador do Agent exige elevação para registrar o
              // Windows Service. Por isso HKCU pode representar a conta
              // administrativa usada no UAC, e não o usuário RPA.
              //
              // HKEY_USERS permite consultar os hives dos usuários que
              // estão carregados no Windows, inclusive um usuário comum
              // que instalou Python somente no próprio perfil.
              if not RegGetSubkeyNames(
                HKEY_USERS,
                '',
                UserSids
              ) then
              begin
                exit;
              end;

              for UserIndex := 0 to GetArrayLength(UserSids) - 1 do
              begin
                if Pos(
                  '_classes',
                  LowerCase(UserSids[UserIndex])
                ) > 0 then
                begin
                  continue;
                end;

                UserBaseKey :=
                  UserSids[UserIndex] + '\\SOFTWARE\\Python';

                if IsWin64 then
                begin
                  if FindPythonInRegistryBase(
                    HKEY_USERS_64,
                    UserBaseKey,
                    PythonPath
                  ) then
                  begin
                    Result := True;
                    exit;
                  end;
                end;

                if FindPythonInRegistryBase(
                  HKEY_USERS_32,
                  UserBaseKey,
                  PythonPath
                ) then
                begin
                  Result := True;
                  exit;
                end;
              end;
            end;


            function FindPythonInKnownLocations(
              var PythonPath: String
            ): Boolean;
            var
              MinorVersion: Integer;
              Candidate: String;
              WindowsDrive: String;
            begin
              Result := False;

              WindowsDrive := ExtractFileDrive(
                ExpandConstant('{{win}}')
              );

              // Layouts de sistema conhecidos:
              // C:\\Program Files\\Python312\\python.exe
              // C:\\Python312\\python.exe
              for MinorVersion := 20 downto 8 do
              begin
                if IsWin64 then
                begin
                  Candidate := PathCombine(
                    ExpandConstant('{{commonpf64}}'),
                    'Python3' + IntToStr(MinorVersion) + '\\python.exe'
                  );

                  if AcceptPythonCandidate(
                    Candidate,
                    PythonPath
                  ) then
                  begin
                    Result := True;
                    exit;
                  end;
                end;

                Candidate := PathCombine(
                  ExpandConstant('{{commonpf32}}'),
                  'Python3' + IntToStr(MinorVersion) + '\\python.exe'
                );

                if AcceptPythonCandidate(
                  Candidate,
                  PythonPath
                ) then
                begin
                  Result := True;
                  exit;
                end;

                Candidate := PathCombine(
                  WindowsDrive + '\\',
                  'Python3' + IntToStr(MinorVersion) + '\\python.exe'
                );

                if AcceptPythonCandidate(
                  Candidate,
                  PythonPath
                ) then
                begin
                  Result := True;
                  exit;
                end;
              end;
            end;


            function ExpandProfileImagePath(
              ProfilePath: String
            ): String;
            begin
              // ProfileImagePath normalmente contém %SystemDrive%.
              StringChangeEx(
                ProfilePath,
                '%SystemDrive%',
                ExpandConstant('{{sd}}'),
                False
              );

              Result := ProfilePath;
            end;


            function FindPythonInUserProfiles(
              var PythonPath: String
            ): Boolean;
            var
              ProfileSids: TArrayOfString;
              ProfileIndex: Integer;
              ProfileKey: String;
              ProfilePath: String;
              PythonRoot: String;
              Candidate: String;
              MinorVersion: Integer;
            begin
              Result := False;

              // ProfileList funciona mesmo quando o usuário não possui
              // privilégios administrativos. O Python oficial instalado
              // somente para o usuário normalmente fica em:
              //
              // C:\\Users\\usuario\\AppData\\Local\\Programs\\Python\\Python312\\python.exe
              if not RegGetSubkeyNames(
                HKEY_LOCAL_MACHINE,
                'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList',
                ProfileSids
              ) then
              begin
                exit;
              end;

              for ProfileIndex := 0 to GetArrayLength(ProfileSids) - 1 do
              begin
                ProfileKey :=
                  'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\' +
                  ProfileSids[ProfileIndex];

                ProfilePath := '';

                if not RegQueryStringValue(
                  HKEY_LOCAL_MACHINE,
                  ProfileKey,
                  'ProfileImagePath',
                  ProfilePath
                ) then
                begin
                  continue;
                end;

                ProfilePath := ExpandProfileImagePath(
                  ProfilePath
                );

                PythonRoot := PathCombine(
                  ProfilePath,
                  'AppData\\Local\\Programs\\Python'
                );

                for MinorVersion := 20 downto 8 do
                begin
                  Candidate := PathCombine(
                    PythonRoot,
                    'Python3' + IntToStr(MinorVersion) + '\\python.exe'
                  );

                  if AcceptPythonCandidate(
                    Candidate,
                    PythonPath
                  ) then
                  begin
                    Result := True;
                    exit;
                  end;

                  // Também cobre instalações 32 bits com sufixo -32.
                  Candidate := PathCombine(
                    PythonRoot,
                    'Python3' + IntToStr(MinorVersion) + '-32\\python.exe'
                  );

                  if AcceptPythonCandidate(
                    Candidate,
                    PythonPath
                  ) then
                  begin
                    Result := True;
                    exit;
                  end;
                end;
              end;
            end;


            function FindPythonInPath(
              var PythonPath: String
            ): Boolean;
            var
              ResultCode: Integer;
              OutputFile: String;
              Lines: TArrayOfString;
              LineIndex: Integer;
              Candidate: String;
            begin
              Result := False;

              OutputFile := ExpandConstant(
                '{{tmp}}\\duet_python_where.txt'
              );

              DeleteFile(
                OutputFile
              );

              // `where` pode retornar mais de um python.exe. Cada linha é
              // validada e aliases WindowsApps são descartados.
              if not Exec(
                ExpandConstant('{{cmd}}'),
                '/C where.exe python > "' + OutputFile + '" 2>NUL',
                '',
                SW_HIDE,
                ewWaitUntilTerminated,
                ResultCode
              ) then
              begin
                exit;
              end;

              if not LoadStringsFromFile(
                OutputFile,
                Lines
              ) then
              begin
                exit;
              end;

              for LineIndex := 0 to GetArrayLength(Lines) - 1 do
              begin
                Candidate := Trim(
                  Lines[LineIndex]
                );

                if AcceptPythonCandidate(
                  Candidate,
                  PythonPath
                ) then
                begin
                  Result := True;
                  DeleteFile(OutputFile);
                  exit;
                end;
              end;

              DeleteFile(
                OutputFile
              );
            end;


            function FindPythonAutomatically(
              var PythonPath: String
            ): Boolean;
            begin
              PythonPath := '';

              // Instalações de máquina têm prioridade porque são as mais
              // estáveis para um Windows Service.
              if FindPythonInMachineRegistry(PythonPath) then
              begin
                Result := True;
                exit;
              end;

              if FindPythonInKnownLocations(PythonPath) then
              begin
                Result := True;
                exit;
              end;

              // Depois aceitamos instalações reais por usuário.
              if FindPythonInLoadedUserRegistry(PythonPath) then
              begin
                Result := True;
                exit;
              end;

              if FindPythonInUserProfiles(PythonPath) then
              begin
                Result := True;
                exit;
              end;

              // Por último, qualquer instalação real disponível no PATH
              // do processo do instalador.
              if FindPythonInPath(PythonPath) then
              begin
                Result := True;
                exit;
              end;

              Result := False;
            end;


            procedure InitializeWizard();
            begin
              PythonModePage := CreateInputOptionPage(
                wpWelcome,
                'Configuração do Python',
                'Escolha como o DUET deve localizar o Python.',
                'O DUET não instala Python. Selecione Detecção automática ' +
                'ou informe uma instalação específica já existente na máquina.',
                True,
                False
              );

              PythonModePage.Add(
                '&Detectar automaticamente (recomendado)'
              );

              PythonModePage.Add(
                '&Usar uma instalação específica'
              );

              PythonModePage.SelectedValueIndex := 0;

              PythonPathPage := CreateInputFilePage(
                PythonModePage.ID,
                'Python personalizado',
                'Selecione o executável Python que o DUET deve utilizar.',
                'Escolha o arquivo python.exe da instalação desejada.'
              );

              PythonPathPage.Add(
                '&Executável do Python:',
                'Executáveis (*.exe)|*.exe|Todos os arquivos (*.*)|*.*',
                '.exe'
              );
            end;


            function ShouldSkipPage(
              PageID: Integer
            ): Boolean;
            begin
              Result := False;

              if Assigned(PythonPathPage) then
              begin
                if PageID = PythonPathPage.ID then
                begin
                  Result :=
                    PythonModePage.SelectedValueIndex = 0;
                end;
              end;
            end;


            function NextButtonClick(
              CurPageID: Integer
            ): Boolean;
            var
              PythonPath: String;
            begin
              Result := True;

              // Modo automático selecionado.
              if CurPageID = PythonModePage.ID then
              begin
                if PythonModePage.SelectedValueIndex = 0 then
                begin
                  DetectedPythonPath := '';

                  if not FindPythonAutomatically(
                    DetectedPythonPath
                  ) then
                  begin
                    MsgBox(
                      'Nenhuma instalação Python 3 válida foi encontrada automaticamente.' + #13#10 + #13#10 +
                      'O Python pode estar instalado para a máquina ou somente para um usuário.' + #13#10 +
                      'Instale uma versão Python 3 real ou volte e selecione ' +
                      '"Usar uma instalação específica".',
                      mbError,
                      MB_OK
                    );

                    Result := False;
                    exit;
                  end;

                  Log(
                    'DUET Python automático detectado: ' +
                    DetectedPythonPath
                  );
                end;
              end;

              // Modo personalizado selecionado.
              if CurPageID = PythonPathPage.ID then
              begin
                PythonPath := Trim(
                  PythonPathPage.Values[0]
                );

                if PythonPath = '' then
                begin
                  MsgBox(
                    'Selecione o arquivo python.exe que o DUET deve utilizar.',
                    mbError,
                    MB_OK
                  );

                  Result := False;
                  exit;
                end;

                if IsWindowsAppsPython(PythonPath) then
                begin
                  MsgBox(
                    'O caminho selecionado pertence ao WindowsApps/App Execution Alias.' + #13#10 + #13#10 +
                    'Selecione o python.exe de uma instalação Python real.',
                    mbError,
                    MB_OK
                  );

                  Result := False;
                  exit;
                end;

                if not ValidatePythonExecutable(PythonPath) then
                begin
                  MsgBox(
                    'O executável selecionado não é uma instalação Python 3 válida:' + #13#10 + #13#10 +
                    PythonPath,
                    mbError,
                    MB_OK
                  );

                  Result := False;
                  exit;
                end;
              end;
            end;


            procedure PersistPythonConfiguration();
            var
              ConfigPath: String;
              ConfigLines: TArrayOfString;
              LineIndex: Integer;
              PythonPath: String;
            begin
              ConfigPath := ExpandConstant(
                '{{app}}\\config.json'
              );

              // LoadStringsFromFile reconhece UTF-8 com ou sem BOM.
              if not LoadStringsFromFile(
                ConfigPath,
                ConfigLines
              ) then
              begin
                RaiseException(
                  'Não foi possível ler o config.json do DUET Agent.'
                );
              end;

              if PythonModePage.SelectedValueIndex = 0 then
              begin
                PythonPath := Trim(
                  DetectedPythonPath
                );

                // Defesa adicional caso o estado da página tenha sido
                // alterado antes da cópia do config.json.
                if PythonPath = '' then
                begin
                  if not FindPythonAutomatically(
                    PythonPath
                  ) then
                  begin
                    RaiseException(
                      'Não foi possível localizar o Python automático durante a instalação.'
                    );
                  end;
                end;

                // O caminho detectado é salvo mesmo no modo auto.
                // O Agent tentará este caminho primeiro e somente fará
                // redetecção se ele deixar de existir ou ficar inválido.
                StringChangeEx(
                  PythonPath,
                  '\\',
                  '\\\\',
                  True
                );

                StringChangeEx(
                  PythonPath,
                  '"',
                  '\\"',
                  True
                );

                for LineIndex := 0 to GetArrayLength(ConfigLines) - 1 do
                begin
                  StringChangeEx(
                    ConfigLines[LineIndex],
                    '"__DUET_PYTHON_MODE__"',
                    '"auto"',
                    True
                  );

                  StringChangeEx(
                    ConfigLines[LineIndex],
                    '"__DUET_PYTHON_EXECUTABLE__"',
                    '"' + PythonPath + '"',
                    True
                  );
                end;
              end
              else
              begin
                PythonPath := Trim(
                  PythonPathPage.Values[0]
                );

                // Escapa barras e aspas para manter JSON válido.
                StringChangeEx(
                  PythonPath,
                  '\\',
                  '\\\\',
                  True
                );

                StringChangeEx(
                  PythonPath,
                  '"',
                  '\\"',
                  True
                );

                for LineIndex := 0 to GetArrayLength(ConfigLines) - 1 do
                begin
                  StringChangeEx(
                    ConfigLines[LineIndex],
                    '"__DUET_PYTHON_MODE__"',
                    '"custom"',
                    True
                  );

                  StringChangeEx(
                    ConfigLines[LineIndex],
                    '"__DUET_PYTHON_EXECUTABLE__"',
                    '"' + PythonPath + '"',
                    True
                  );
                end;
              end;

              if not SaveStringsToUTF8FileWithoutBOM(
                ConfigPath,
                ConfigLines,
                False
              ) then
              begin
                RaiseException(
                  'Não foi possível salvar a configuração Python do DUET Agent.'
                );
              end;
            end;


            function InitializeSetup(): Boolean;
            begin
              // O Python é validado nas páginas do instalador, depois
              // que o usuário escolhe Automático ou Personalizado.

              // Guarda o estado original do Service.
              DuetAgentServiceExistedBeforeInstall :=
                DuetAgentServiceExists();

              // Guarda o estado original do Credential Provider.
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

            # O ISCC pode escrever mensagens úteis tanto em stdout
            # quanto em stderr. Registramos os dois para que um erro
            # de compilação nunca volte a aparecer apenas como uma
            # mensagem genérica no log do Control Room.
            compiler_output = "\n".join(
                output
                for output in (
                    resultado.stdout.strip(),
                    resultado.stderr.strip(),
                )
                if output
            )

            logger.error(
                (
                    "Falha ao compilar instalador do Agent | "
                    "agent_id=%s | returncode=%s | output=%s"
                ),
                agent_id,
                resultado.returncode,
                compiler_output or "(sem saída do ISCC)",
                extra={
                    "event": (
                        "agent_installer_compilation_failed"
                    ),
                    "agent_id": agent_id,
                    "reason": (
                        f"returncode={resultado.returncode}"
                    ),
                    "error_message": compiler_output,
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

            # O arquivo físico possui nome exclusivo por requisição.
            # Ele só é removido após o término da transmissão HTTP,
            # impedindo que outro download altere seu Content-Length.
            background=BackgroundTask(
                _remover_instalador_apos_download,
                installer_path,
            ),
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
