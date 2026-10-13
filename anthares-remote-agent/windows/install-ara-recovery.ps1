$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\AntharesRemoteAgent'
$recovery = Join-Path $root 'ara-recovery.ps1'

if (-not (Test-Path $recovery)) {
    throw "Missing recovery script: $recovery"
}

$action = 'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $recovery + '"'

# Independent recovery path. It runs as SYSTEM in session 0, so it cannot steal
# focus or surface a console window on the interactive desktop.
schtasks.exe /Create /TN "Anthares Remote Recovery" /TR $action /SC MINUTE /MO 1 /RU SYSTEM /RL HIGHEST /F | Out-Null

# Validate that the task is registered and can execute immediately.
schtasks.exe /Run /TN "Anthares Remote Recovery" | Out-Null
Start-Sleep -Seconds 2

$task = Get-ScheduledTask -TaskName 'Anthares Remote Recovery' -ErrorAction Stop
[pscustomobject]@{
    task_name = $task.TaskName
    state = [string]$task.State
    user = $task.Principal.UserId
    logon_type = [string]$task.Principal.LogonType
    run_level = [string]$task.Principal.RunLevel
    recovery_script = $recovery
} | ConvertTo-Json -Compress
