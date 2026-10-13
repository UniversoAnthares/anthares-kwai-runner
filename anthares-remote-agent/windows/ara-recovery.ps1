$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\ProgramData\AntharesRemoteAgent'
$taskName = 'Anthares Remote Agent SYSTEM'
$log = Join-Path $root 'recovery.log'
$envFile = Join-Path $root 'agent-env.ps1'
if (Test-Path $envFile) { try { . $envFile } catch {} }

function Log([string]$m) {
    try { Add-Content -Path $log -Value ((Get-Date).ToUniversalTime().ToString('o') + ' ' + $m) -Encoding UTF8 } catch {}
}

function Test-AgentHeartbeat {
    $device = ([string]$env:ANTHARES_DEVICE_ID).Trim()
    if ([string]::IsNullOrWhiteSpace($device)) { $device = 'DESKTOP-FTDK0HP' }
    $token = ([string]$env:ANTHARES_DEVICE_TOKEN).Trim()
    if ([string]::IsNullOrWhiteSpace($token)) { return $null }
    $origin = ([string]$env:ANTHARES_CONTROL_URL).Trim().TrimEnd('/')
    if ([string]::IsNullOrWhiteSpace($origin) -or $origin -match 'onrender\.com') {
        $origin = 'https://anthares-ara-backup.anthares1.workers.dev'
    }
    try {
        $headers = @{ Authorization = ('Bearer ' + $token); 'X-Anthares-Device' = $device }
        $s = Invoke-RestMethod -Headers $headers -Uri ($origin + '/v1/device/status') -TimeoutSec 8
        if ($null -eq $s) { return $false }
        if (-not [bool]$s.connected) { return $false }
        $seen = [DateTimeOffset]::Parse([string]$s.seen_at).ToUniversalTime()
        return ((([DateTimeOffset]::UtcNow - $seen).TotalSeconds) -lt 50)
    } catch {
        # Control-path failure alone is not proof that the local agent is bad.
        return $null
    }
}

$supervisor = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'powershell.exe' -and $_.CommandLine -match 'run-agent-system-supervisor\.ps1'
})
$agents = @(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard','anthares-remote-agent-v4' -ErrorAction SilentlyContinue)
$heartbeat = Test-AgentHeartbeat

if ($supervisor.Count -gt 0 -and $agents.Count -gt 0 -and $heartbeat -eq $true) {
    Log ('healthy supervisor=' + (($supervisor.ProcessId -join ',')) + ' agent=' + (($agents.Id -join ',')))
    exit 0
}
if ($supervisor.Count -gt 0 -and $agents.Count -gt 0 -and $null -eq $heartbeat) {
    Log 'control-status-unavailable; preserving live supervisor/agent'
    exit 0
}

$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $task) {
    Log 'ERROR task-missing'
    exit 2
}

try {
    if ($heartbeat -eq $false) {
        foreach ($agent in $agents) {
            try { Stop-Process -Id $agent.Id -Force -ErrorAction SilentlyContinue } catch {}
        }
        Log 'RECOVERY stale-device-heartbeat; terminated exact Anthares agent processes'
        Start-Sleep -Milliseconds 750
    }
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 750
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    Log 'RECOVERY restarted-system-supervisor'
    exit 0
} catch {
    Log ('ERROR restart-failed ' + $_.Exception.GetType().Name)
    exit 3
}
