$ErrorActionPreference='SilentlyContinue'
$root='C:\ProgramData\AntharesRemoteAgent'
$standby='https://anthares-ara-infra-canary-v2.onrender.com'

function Warm-Standby {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri ($standby + '/healthz') -TimeoutSec 20 | Out-Null
    } catch {}
}

function Ensure-Supervisor([string]$scriptName) {
    $launcher=Join-Path $root $scriptName
    if(-not (Test-Path $launcher)){ return }
    $escaped=[regex]::Escape($scriptName)
    $running=Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object {
        $_.CommandLine -match $escaped
    }
    if(-not $running){
        $cmd="powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcher`""
        ([wmiclass]'Win32_Process').Create($cmd) | Out-Null
    }
}

Warm-Standby
Ensure-Supervisor 'run-agent.ps1'
Ensure-Supervisor 'run-agent-standard.ps1'
