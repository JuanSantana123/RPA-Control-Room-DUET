param(
    [Parameter(Mandatory = $true)]
    [string]$PythonExe
)

$ErrorActionPreference = "Stop"

$BridgeRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainPy = Join-Path $BridgeRoot "main.py"

$ResolvedPython = (Resolve-Path $PythonExe).Path
$ResolvedMain = (Resolve-Path $MainPy).Path

$ProtocolKey = "HKCU:\Software\Classes\duet"
$CommandKey = Join-Path $ProtocolKey "shell\open\command"

New-Item -Path $ProtocolKey -Force | Out-Null
Set-Item -Path $ProtocolKey -Value "URL:DUET Developer Protocol"

New-ItemProperty `
    -Path $ProtocolKey `
    -Name "URL Protocol" `
    -Value "" `
    -PropertyType String `
    -Force | Out-Null

New-Item -Path $CommandKey -Force | Out-Null

$Command = "`"$ResolvedPython`" `"$ResolvedMain`" `"%1`""
Set-Item -Path $CommandKey -Value $Command

Write-Host ""
Write-Host "DUET Developer Protocol registrado com sucesso."
Write-Host "Python: $ResolvedPython"
Write-Host "Bridge: $ResolvedMain"
Write-Host ""
