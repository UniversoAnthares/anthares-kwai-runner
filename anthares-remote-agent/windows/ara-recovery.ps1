$ErrorActionPreference = 'SilentlyContinue'
$taskName = 'Anthares Remote Agent SYSTEM'
$log = 'C:\ProgramData\AntharesRemoteAgent\recovery.log'

function Log([string]$m) {
    try {
        Add-Content -Path $log -Value ((Get-Date).ToUniversalTime().ToString('o') + ' ' + $m) -Encoding UTF8
    } catch {}
}

$supervisor = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'powershell.exe' -and $_.CommandLine -match 'run-agent-system-supervisor\.ps1'
})

if ($supervisor.Count -gt 0) {
    Log ('healthy supervisor=' + (($supervisor.ProcessId -join ',')))
    exit 0
}

$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $task) {
    Log 'ERROR task-missing'
    exit 2
}

try {
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    Log 'RECOVERY started-system-supervisor'
    exit 0
} catch {
    Log ('ERROR start-failed ' + $_.Exception.GetType().Name)
    exit 3
}
