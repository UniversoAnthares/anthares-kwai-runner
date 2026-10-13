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
    # A crashed long-running task can remain logically "Running" after its
    # supervisor process disappeared. Clear that stale state first so the
    # subsequent start is guaranteed to create a fresh supervisor process.
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 750
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    Log 'RECOVERY restarted-system-supervisor'
    exit 0
} catch {
    Log ('ERROR restart-failed ' + $_.Exception.GetType().Name)
    exit 3
}
