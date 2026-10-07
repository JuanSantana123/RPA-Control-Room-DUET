$ErrorActionPreference = "Stop"
$ProtocolKey = "HKCU:\Software\Classes\duet"

if (Test-Path $ProtocolKey) {
    Remove-Item -Path $ProtocolKey -Recurse -Force
}

Write-Host "Protocolo duet:// removido."
