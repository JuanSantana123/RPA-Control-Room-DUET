<#
.SYNOPSIS
    DUET RPA - Rollback do Credential Provider.

.DESCRIPTION
    Remove SOMENTE o Credential Provider do DUET do Registro do Windows.

    Este script existe para ser preparado e testado ANTES do primeiro
    registro real da DLL.

    CLSID DUET:
        {5CA94EF5-C6CE-4F61-8CF2-201B142EB819}

    Chaves tratadas:
        HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Providers\{CLSID}
        HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Provider Filters\{CLSID}
        HKLM\SOFTWARE\Classes\CLSID\{CLSID}

    IMPORTANTE:
        - NÃO remove Credential Providers nativos do Windows.
        - NÃO altera políticas de logon.
        - NÃO exclui a DLL do disco.
        - NÃO executa reboot automaticamente.
        - Pode ser executado várias vezes com segurança.

    Execute em PowerShell "Como Administrador".
#>

# ============================================================
# CONFIGURAÇÃO FIXA DO DUET
# ============================================================

$ErrorActionPreference = "Stop"

$DuetClsid = "{5CA94EF5-C6CE-4F61-8CF2-201B142EB819}"

$CredentialProviderKey =
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Providers\$DuetClsid"

$CredentialProviderFilterKey =
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Provider Filters\$DuetClsid"

$ComClassKey =
    "HKLM:\SOFTWARE\Classes\CLSID\$DuetClsid"


# ============================================================
# FUNÇÃO - VERIFICA ADMINISTRADOR
# ============================================================
#
# Alterações em HKLM exigem elevação.
# Não tentamos autoelevar o processo para evitar comportamento
# inesperado durante um procedimento de recuperação.
# ============================================================

function Test-IsAdministrator
{
    $CurrentIdentity =
        [Security.Principal.WindowsIdentity]::GetCurrent()

    $Principal =
        New-Object Security.Principal.WindowsPrincipal(
            $CurrentIdentity
        )

    return $Principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}


# ============================================================
# FUNÇÃO - REMOVE UMA CHAVE, SE EXISTIR
# ============================================================

function Remove-DuetRegistryKey
{
    param
    (
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if (Test-Path -LiteralPath $Path)
    {
        Write-Host ""
        Write-Host "[REMOVENDO] $Description"
        Write-Host "           $Path"

        Remove-Item `
            -LiteralPath $Path `
            -Recurse `
            -Force

        Write-Host "[OK]       Removido."
    }
    else
    {
        Write-Host ""
        Write-Host "[OK]       $Description já não existe."
        Write-Host "           $Path"
    }
}


# ============================================================
# INÍCIO
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " DUET RPA - CREDENTIAL PROVIDER ROLLBACK"
Write-Host "============================================================"
Write-Host ""
Write-Host "CLSID: $DuetClsid"


# ============================================================
# VALIDA PRIVILÉGIO
# ============================================================

if (-not (Test-IsAdministrator))
{
    Write-Host ""
    Write-Host "[ERRO] Este script precisa ser executado como Administrador."
    Write-Host ""
    Write-Host "Abra o PowerShell como Administrador e execute novamente."
    Write-Host ""

    exit 1
}


Write-Host ""
Write-Host "[OK] Processo executando com privilégios de Administrador."


# ============================================================
# REMOVE REGISTRO DO CREDENTIAL PROVIDER
# ============================================================

Remove-DuetRegistryKey `
    -Path $CredentialProviderKey `
    -Description "Registro do DUET em Credential Providers"


# ============================================================
# REMOVE FILTER DO DUET, CASO EXISTA
# ============================================================
#
# A arquitetura atual NÃO precisa registrar Credential Provider
# Filter.
#
# Ainda assim removemos defensivamente somente um eventual filtro
# que use exatamente o CLSID do DUET.
# ============================================================

Remove-DuetRegistryKey `
    -Path $CredentialProviderFilterKey `
    -Description "Eventual Credential Provider Filter do DUET"


# ============================================================
# REMOVE REGISTRO COM
# ============================================================

Remove-DuetRegistryKey `
    -Path $ComClassKey `
    -Description "Registro COM do DuetCredentialProvider"


# ============================================================
# VERIFICAÇÃO FINAL
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " VERIFICAÇÃO FINAL"
Write-Host "============================================================"

# ------------------------------------------------------------
# Monta explicitamente a lista de chaves que ainda existem.
#
# Evitamos pipeline com Where-Object aqui para manter o script
# compatível e previsível em diferentes versões do PowerShell.
# ------------------------------------------------------------

$RemainingKeys =
    @(
        foreach (
            $RegistryKey in @(
                $CredentialProviderKey,
                $CredentialProviderFilterKey,
                $ComClassKey
            )
        )
        {
            if (
                Test-Path `
                    -LiteralPath $RegistryKey
            )
            {
                $RegistryKey
            }
        }
    )


if ($RemainingKeys.Count -gt 0)
{
    Write-Host ""
    Write-Host "[ERRO] Uma ou mais chaves do DUET ainda existem:"

    foreach ($Key in $RemainingKeys)
    {
        Write-Host "       $Key"
    }

    Write-Host ""

    exit 2
}


Write-Host ""
Write-Host "[OK] Nenhuma chave de registro do DUET permanece."
Write-Host ""
Write-Host "A DLL NÃO foi apagada do disco."
Write-Host "Nenhum Credential Provider nativo foi alterado."
Write-Host ""
Write-Host "Se este rollback tiver sido usado após um registro real,"
Write-Host "reinicie o Windows antes de validar novamente a tela de logon."
Write-Host ""
Write-Host "ROLLBACK DUET FINALIZADO COM SUCESSO"
Write-Host ""

exit 0
