# ============================================================
# DUET - BOOTSTRAP DO RUNTIME PYTHON DO AGENT
# ============================================================
#
# Responsabilidades:
#
# - receber a versão Python selecionada no instalador;
# - utilizar o uv distribuído pelo DUET;
# - instalar o Python dentro da estrutura do Agent;
# - não alterar o PATH global do Windows;
# - não registrar Python globalmente;
# - criar o registry utilizado pelo RuntimeManager;
# - preparar environments e cache.
#
# Compatível com Windows PowerShell 5.1.
# ============================================================


param(
    # Diretório onde o DUET Agent está instalado.
    [Parameter(Mandatory = $true)]
    [string]$AgentRoot,

    # Versão Python escolhida no instalador.
    #
    # Exemplos:
    #   3.12
    #   3.12.3
    #   3.14
    #
    # Nenhuma versão específica fica hardcoded neste script.
    [Parameter(Mandatory = $true)]
    [string]$PythonVersion
)


# ============================================================
# COMPORTAMENTO DE ERRO
# ============================================================

$ErrorActionPreference = "Stop"


try {

    Write-Host "============================================================"
    Write-Host "DUET - PREPARACAO DO RUNTIME PYTHON"
    Write-Host "============================================================"


    # ========================================================
    # NORMALIZA PARAMETROS
    # ========================================================

    $AgentRoot = [System.IO.Path]::GetFullPath($AgentRoot)

    $PythonVersion = $PythonVersion.Trim()


    if ([string]::IsNullOrWhiteSpace($PythonVersion)) {

        throw "A versao Python nao foi informada."
    }


    Write-Host "Agent Root : $AgentRoot"
    Write-Host "Python     : $PythonVersion"


    # ========================================================
    # CAMINHOS CONTROLADOS PELO DUET
    # ========================================================

    $UvExecutable = Join-Path $AgentRoot "tools\uv.exe"

    $RuntimeRoot = Join-Path $AgentRoot "runtimes\python"

    $EnvironmentRoot = Join-Path $AgentRoot "environments"

    $CacheRoot = Join-Path $AgentRoot "cache\uv"

    $DataRoot = Join-Path $AgentRoot "data"

    $RegistryFile = Join-Path $DataRoot "python_runtimes.json"


    # ========================================================
    # VALIDA UV
    # ========================================================

    if (-not (Test-Path -LiteralPath $UvExecutable -PathType Leaf)) {

        throw "uv.exe nao encontrado: $UvExecutable"
    }


    # ========================================================
    # CRIA ESTRUTURA DO AGENT
    # ========================================================

    $Directories = @(
        $RuntimeRoot,
        $EnvironmentRoot,
        $CacheRoot,
        $DataRoot
    )


    foreach ($Directory in $Directories) {

        if (-not (Test-Path -LiteralPath $Directory)) {

            New-Item `
                -ItemType Directory `
                -Path $Directory `
                -Force | Out-Null
        }
    }


    # ========================================================
    # CONFIGURACAO ISOLADA DO UV
    # ========================================================
    #
    # Tudo fica dentro de C:\RPA-Agent.
    #
    # O DUET nao depende:
    #
    # - do Python instalado no Windows;
    # - do PATH;
    # - do registro global do Python;
    # - do cache do usuario Windows.
    # ========================================================

    $env:UV_PYTHON_INSTALL_DIR = $RuntimeRoot

    $env:UV_CACHE_DIR = $CacheRoot

    $env:UV_PYTHON_INSTALL_BIN = "false"

    $env:UV_PYTHON_INSTALL_REGISTRY = "false"

    $env:UV_PYTHON_NO_REGISTRY = "true"

    $env:UV_NO_CONFIG = "true"


    # ========================================================
    # INSTALA / GARANTE O RUNTIME
    # ========================================================

    Write-Host ""
    Write-Host "[DUET] Preparando Python $PythonVersion..."


    & $UvExecutable python install --install-dir $RuntimeRoot $PythonVersion


    if ($LASTEXITCODE -ne 0) {

        throw (
            "uv falhou ao preparar o Python. Codigo de saida: " +
            $LASTEXITCODE
        )
    }


    # ========================================================
    # LOCALIZA O PYTHON GERENCIADO
    # ========================================================

    $PythonExecutableOutput = & $UvExecutable python find --managed-python $PythonVersion


    if ($LASTEXITCODE -ne 0) {

        throw "uv nao conseguiu localizar o runtime Python instalado."
    }


    # O uv normalmente devolve somente um caminho.
    # Pegamos explicitamente a primeira linha para evitar qualquer
    # ruido futuro na saida do comando.
    $PythonExecutable = (
        $PythonExecutableOutput |
        Select-Object -First 1
    )


    if ($null -eq $PythonExecutable) {

        throw "uv nao retornou o caminho do python.exe."
    }


    $PythonExecutable = $PythonExecutable.ToString().Trim()


    if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {

        throw (
            "python.exe gerenciado nao encontrado: " +
            $PythonExecutable
        )
    }


    # ========================================================
    # DESCOBRE A VERSAO REAL INSTALADA
    # ========================================================

    $ResolvedVersion = & $PythonExecutable -c "import platform; print(platform.python_version())"


    if ($LASTEXITCODE -ne 0) {

        throw "Nao foi possivel descobrir a versao do Python."
    }


    $ResolvedVersion = $ResolvedVersion.ToString().Trim()


    # ========================================================
    # DESCOBRE ARQUITETURA
    # ========================================================

    $Architecture = & $PythonExecutable -c "import platform; print(platform.machine())"


    if ($LASTEXITCODE -ne 0) {

        throw "Nao foi possivel descobrir a arquitetura do Python."
    }


    $Architecture = $Architecture.ToString().Trim()


    # ========================================================
    # DESCOBRE IMPLEMENTACAO
    # ========================================================

    $Implementation = & $PythonExecutable -c "import platform; print(platform.python_implementation())"


    if ($LASTEXITCODE -ne 0) {

        throw "Nao foi possivel descobrir a implementacao do Python."
    }


    $Implementation = $Implementation.ToString().Trim()


    # ========================================================
    # DIRETORIO DO RUNTIME RESOLVIDO
    # ========================================================

    $InstallDirectory = Split-Path -Parent $PythonExecutable


    # ========================================================
    # MONTA REGISTRO DO RUNTIME
    # ========================================================
    #
    # Este JSON possui exatamente a estrutura utilizada pelo
    # RuntimeRegistry Python do Agent.
    # ========================================================

    $RuntimeData = [ordered]@{
        version_request   = $PythonVersion
        resolved_version  = $ResolvedVersion
        executable        = $PythonExecutable
        install_directory = $InstallDirectory
        architecture      = $Architecture
        implementation    = $Implementation
        managed_by        = "uv"
        status            = "installed"
    }


    $Runtimes = [ordered]@{}

    $Runtimes[$PythonVersion] = $RuntimeData


    $Registry = [ordered]@{
        schema_version  = 1
        default_version = $PythonVersion
        runtimes        = $Runtimes
    }


    # ========================================================
    # CONVERTE PARA JSON
    # ========================================================

    $RegistryJson = $Registry | ConvertTo-Json -Depth 10


    # ========================================================
    # GRAVACAO ATOMICA
    # ========================================================
    #
    # Gravamos primeiro em um arquivo temporario e somente depois
    # substituimos o arquivo definitivo.
    #
    # Tambem utilizamos UTF-8 sem BOM para manter compatibilidade
    # com o RuntimeRegistry Python.
    # ========================================================

    $TemporaryRegistryFile = $RegistryFile + ".tmp"

    $Utf8WithoutBom = New-Object `
        -TypeName System.Text.UTF8Encoding `
        -ArgumentList $false


    [System.IO.File]::WriteAllText(
        $TemporaryRegistryFile,
        $RegistryJson,
        $Utf8WithoutBom
    )


    Move-Item `
        -LiteralPath $TemporaryRegistryFile `
        -Destination $RegistryFile `
        -Force


    # ========================================================
    # RESULTADO
    # ========================================================

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "DUET - RUNTIME PREPARADO COM SUCESSO"
    Write-Host "============================================================"

    Write-Host "Solicitado : $PythonVersion"
    Write-Host "Resolvido  : $ResolvedVersion"
    Write-Host "Executavel : $PythonExecutable"
    Write-Host "Registry   : $RegistryFile"


    exit 0
}
catch {

    $ErrorMessage = $_.Exception.Message

    Write-Error (
        "[DUET] Falha ao preparar runtime Python: " +
        $ErrorMessage
    )

    exit 1
}