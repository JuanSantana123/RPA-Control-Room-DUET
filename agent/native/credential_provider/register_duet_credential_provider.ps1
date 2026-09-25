<#
.SYNOPSIS
    Registra o DUET RPA Credential Provider no Windows.

.DESCRIPTION
    Registra SOMENTE o Credential Provider do DUET.

    O script:
      - exige Administrador;
      - exige PowerShell x64;
      - valida a DLL compilada;
      - exige que o rollback esteja disponível;
      - copia a DLL para C:\Windows\System32;
      - registra o CLSID COM do DUET;
      - configura ThreadingModel = Apartment;
      - registra o DUET em Credential Providers;
      - NÃO cria Credential Provider Filter;
      - NÃO altera providers nativos;
      - NÃO reinicia, bloqueia ou faz logoff;
      - valida o resultado após o registro.

    CLSID:
      {5CA94EF5-C6CE-4F61-8CF2-201B142EB819}
#>

$ErrorActionPreference = "Stop"

# ============================================================
# CONFIGURAÇÃO
# ============================================================

$DuetClsid = "{5CA94EF5-C6CE-4F61-8CF2-201B142EB819}"
$FriendlyName = "DUET RPA Credential Provider"

$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path

$SourceDll = Join-Path $ScriptDirectory "DuetCredentialProvider.dll"
$RollbackScript = Join-Path $ScriptDirectory "rollback_duet_credential_provider.ps1"

$DestinationDll = Join-Path $env:SystemRoot "System32\DuetCredentialProvider.dll"

$CredentialProviderKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Providers\$DuetClsid"
$ComClassKey = "HKLM:\SOFTWARE\Classes\CLSID\$DuetClsid"
$InprocServerKey = "$ComClassKey\InprocServer32"


# ============================================================
# FUNÇÕES
# ============================================================

function Test-IsAdministrator
{
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()

    $Principal = New-Object Security.Principal.WindowsPrincipal(
        $Identity
    )

    return $Principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}


function Get-RegistryDefaultValue
{
    param
    (
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return (Get-Item -LiteralPath $Path).GetValue("")
}


function Remove-PartialDuetRegistration
{
    Write-Host ""
    Write-Host "[ROLLBACK INTERNO] Removendo somente chaves do DUET..."

    foreach ($RegistryKey in @($CredentialProviderKey, $ComClassKey))
    {
        if (Test-Path -LiteralPath $RegistryKey)
        {
            Remove-Item -LiteralPath $RegistryKey -Recurse -Force
            Write-Host "[OK] Removido: $RegistryKey"
        }
    }
}


# ============================================================
# CABEÇALHO
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " DUET RPA - CREDENTIAL PROVIDER REGISTER"
Write-Host "============================================================"
Write-Host ""
Write-Host "CLSID:"
Write-Host "  $DuetClsid"
Write-Host ""
Write-Host "DLL origem:"
Write-Host "  $SourceDll"
Write-Host ""
Write-Host "DLL destino:"
Write-Host "  $DestinationDll"
Write-Host ""


# ============================================================
# PREFLIGHT
# ============================================================

if (-not (Test-IsAdministrator))
{
    Write-Host "[ERRO] Execute este script como Administrador."
    exit 1
}

Write-Host "[OK] Privilégios de Administrador."


if (-not [Environment]::Is64BitProcess)
{
    Write-Host ""
    Write-Host "[ERRO] Execute em PowerShell x64."
    exit 2
}

Write-Host "[OK] PowerShell x64."


if (-not [Environment]::Is64BitOperatingSystem)
{
    Write-Host ""
    Write-Host "[ERRO] Esta DLL foi preparada para Windows x64."
    exit 3
}

Write-Host "[OK] Windows x64."


if (-not (Test-Path -LiteralPath $SourceDll -PathType Leaf))
{
    Write-Host ""
    Write-Host "[ERRO] DuetCredentialProvider.dll não encontrada."
    Write-Host "Esperado:"
    Write-Host "  $SourceDll"
    exit 4
}

Write-Host "[OK] DLL compilada encontrada."


if (-not (Test-Path -LiteralPath $RollbackScript -PathType Leaf))
{
    Write-Host ""
    Write-Host "[ERRO] O rollback não está disponível."
    Write-Host "Esperado:"
    Write-Host "  $RollbackScript"
    Write-Host ""
    Write-Host "O DUET não será registrado sem rollback preparado."
    exit 5
}

Write-Host "[OK] Rollback disponível."


if (Test-Path -LiteralPath $CredentialProviderKey)
{
    Write-Host ""
    Write-Host "[ERRO] O DUET já está registrado em Credential Providers."
    Write-Host "Execute primeiro o rollback validado."
    exit 6
}


if (Test-Path -LiteralPath $ComClassKey)
{
    Write-Host ""
    Write-Host "[ERRO] O CLSID COM do DUET já existe."
    Write-Host "Execute primeiro o rollback validado."
    exit 7
}

Write-Host "[OK] Nenhum registro anterior do DUET encontrado."


# ============================================================
# HASH DA ORIGEM
# ============================================================

$SourceHash = (Get-FileHash -LiteralPath $SourceDll -Algorithm SHA256).Hash

Write-Host ""
Write-Host "SHA256 origem:"
Write-Host "  $SourceHash"


# ============================================================
# PREPARA DLL EM SYSTEM32
# ============================================================

if (Test-Path -LiteralPath $DestinationDll -PathType Leaf)
{
    $ExistingHash = (Get-FileHash -LiteralPath $DestinationDll -Algorithm SHA256).Hash

    if ($ExistingHash -ne $SourceHash)
    {
        $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $BackupDll = "$DestinationDll.bak-$Timestamp"

        Write-Host ""
        Write-Host "[INFO] Já existe uma DLL DUET diferente em System32."
        Write-Host "[INFO] Criando backup:"
        Write-Host "       $BackupDll"

        Copy-Item -LiteralPath $DestinationDll -Destination $BackupDll -Force
    }
    else
    {
        Write-Host ""
        Write-Host "[OK] A DLL existente em System32 já possui o mesmo SHA256."
    }
}


Write-Host ""
Write-Host "[COPIANDO] Credential Provider para System32..."

Copy-Item -LiteralPath $SourceDll -Destination $DestinationDll -Force


if (-not (Test-Path -LiteralPath $DestinationDll -PathType Leaf))
{
    Write-Host ""
    Write-Host "[ERRO] A DLL não apareceu em System32 após a cópia."
    exit 8
}


$DestinationHash = (Get-FileHash -LiteralPath $DestinationDll -Algorithm SHA256).Hash

if ($DestinationHash -ne $SourceHash)
{
    Write-Host ""
    Write-Host "[ERRO] SHA256 da DLL copiada é diferente da origem."
    Write-Host "Origem : $SourceHash"
    Write-Host "Destino: $DestinationHash"
    exit 9
}

Write-Host "[OK] DLL copiada e SHA256 confirmado."


# ============================================================
# REGISTRO
# ============================================================

try
{
    Write-Host ""
    Write-Host "============================================================"
    Write-Host " REGISTRANDO COM"
    Write-Host "============================================================"

    New-Item -Path $ComClassKey -Force | Out-Null
    Set-Item -LiteralPath $ComClassKey -Value $FriendlyName

    New-Item -Path $InprocServerKey -Force | Out-Null
    Set-Item -LiteralPath $InprocServerKey -Value $DestinationDll

    New-ItemProperty `
        -LiteralPath $InprocServerKey `
        -Name "ThreadingModel" `
        -Value "Apartment" `
        -PropertyType String `
        -Force `
        | Out-Null

    Write-Host "[OK] COM registrado."
    Write-Host "     ThreadingModel = Apartment"


    Write-Host ""
    Write-Host "============================================================"
    Write-Host " REGISTRANDO CREDENTIAL PROVIDER"
    Write-Host "============================================================"

    New-Item -Path $CredentialProviderKey -Force | Out-Null
    Set-Item -LiteralPath $CredentialProviderKey -Value $FriendlyName

    Write-Host "[OK] DUET registrado em Credential Providers."
    Write-Host "[OK] Nenhum Credential Provider Filter foi criado."
    Write-Host "[OK] Nenhum provider nativo foi alterado."
}
catch
{
    Write-Host ""
    Write-Host "[ERRO] Falha durante o registro:"
    Write-Host "       $($_.Exception.Message)"

    try
    {
        Remove-PartialDuetRegistration
    }
    catch
    {
        Write-Host ""
        Write-Host "[ATENÇÃO] O rollback interno também falhou:"
        Write-Host "          $($_.Exception.Message)"
        Write-Host ""
        Write-Host "Execute manualmente:"
        Write-Host "  $RollbackScript"
    }

    exit 10
}


# ============================================================
# VERIFICAÇÃO PÓS-REGISTRO
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " VERIFICAÇÃO PÓS-REGISTRO"
Write-Host "============================================================"

$VerificationErrors = @()


# Credential Provider
if (-not (Test-Path -LiteralPath $CredentialProviderKey))
{
    $VerificationErrors += "Chave Credential Providers do DUET não existe."
}
else
{
    $ProviderName = Get-RegistryDefaultValue -Path $CredentialProviderKey

    if ($ProviderName -ne $FriendlyName)
    {
        $VerificationErrors += "Nome do Credential Provider não confere."
    }
}


# COM CLSID
if (-not (Test-Path -LiteralPath $ComClassKey))
{
    $VerificationErrors += "CLSID COM do DUET não existe."
}


# InprocServer32
if (-not (Test-Path -LiteralPath $InprocServerKey))
{
    $VerificationErrors += "InprocServer32 do DUET não existe."
}
else
{
    $RegisteredDll = Get-RegistryDefaultValue -Path $InprocServerKey

    if ($RegisteredDll -ne $DestinationDll)
    {
        $VerificationErrors += "Caminho registrado da DLL não confere."
    }


    $ThreadingModel = (
        Get-ItemProperty `
            -LiteralPath $InprocServerKey `
            -Name "ThreadingModel"
    ).ThreadingModel

    if ($ThreadingModel -ne "Apartment")
    {
        $VerificationErrors += "ThreadingModel não é Apartment."
    }
}


# DLL
if (-not (Test-Path -LiteralPath $DestinationDll -PathType Leaf))
{
    $VerificationErrors += "DLL não existe em System32."
}
else
{
    $FinalHash = (Get-FileHash -LiteralPath $DestinationDll -Algorithm SHA256).Hash

    if ($FinalHash -ne $SourceHash)
    {
        $VerificationErrors += "SHA256 da DLL registrada não confere com a origem."
    }
}


# ============================================================
# RESULTADO
# ============================================================

if ($VerificationErrors.Count -gt 0)
{
    Write-Host ""
    Write-Host "[ERRO] O registro não passou na verificação final:"

    foreach ($VerificationError in $VerificationErrors)
    {
        Write-Host "       - $VerificationError"
    }

    Write-Host ""
    Write-Host "Executando rollback interno..."

    try
    {
        Remove-PartialDuetRegistration
    }
    catch
    {
        Write-Host ""
        Write-Host "[ATENÇÃO] Execute manualmente:"
        Write-Host "  $RollbackScript"
    }

    exit 11
}


Write-Host ""
Write-Host "[OK] Credential Provider registrado e validado."
Write-Host ""
Write-Host "Credential Provider:"
Write-Host "  $CredentialProviderKey"
Write-Host ""
Write-Host "COM:"
Write-Host "  $InprocServerKey"
Write-Host ""
Write-Host "DLL:"
Write-Host "  $DestinationDll"
Write-Host ""
Write-Host "ThreadingModel:"
Write-Host "  Apartment"
Write-Host ""
Write-Host "SHA256:"
Write-Host "  $SourceHash"
Write-Host ""
Write-Host "IMPORTANTE:"
Write-Host "  - O Windows NÃO foi reiniciado."
Write-Host "  - A estação NÃO foi bloqueada."
Write-Host "  - Nenhum provider nativo foi desabilitado."
Write-Host "  - Não teste a tela de logon ainda sem o próximo passo."
Write-Host "  - Mantenha o rollback disponível."
Write-Host ""
Write-Host "REGISTRO DUET FINALIZADO COM SUCESSO"
Write-Host ""

exit 0
