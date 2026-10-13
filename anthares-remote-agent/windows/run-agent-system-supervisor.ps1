$ErrorActionPreference = 'Continue'
$root = 'C:\ProgramData\AntharesRemoteAgent'
$envFile = Join-Path $root 'agent-env.ps1'
if (Test-Path $envFile) { . $envFile }
$queueAuthLoader = Join-Path $root 'load-issue-queue-auth.ps1'

# Canonical Anthares Remote transport: private GitHub/GitLab issue queues.
# Render, Cloudflare and other HTTP control planes are deliberately absent.
$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP'
Remove-Item Env:ANTHARES_CONTROL_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_PRIMARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_SECONDARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_TERTIARY_URL -ErrorAction SilentlyContinue

$workRoot = ([string]$env:ANTHARES_WORK_ROOT).Trim()
if ([string]::IsNullOrWhiteSpace($workRoot)) { $workRoot = 'D:\AntharsWork' }
$logRoot = Join-Path $workRoot 'logs'
$runtimeRoot = Join-Path $workRoot 'legacy-pc-runtime\supervisor'
try {
    @($workRoot, (Join-Path $workRoot 'temp'), $logRoot, (Join-Path $workRoot 'ara-jobs'), (Join-Path $workRoot 'legacy-pc-runtime'), $runtimeRoot) |
        ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
    $env:ANTHARES_WORK_ROOT = $workRoot
    $env:TEMP = Join-Path $workRoot 'temp'
    $env:TMP = $env:TEMP
    $roots = @(([string]$env:ANTHARES_ALLOWED_ROOTS -split ';') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($roots -notcontains $workRoot) { $roots += $workRoot }
    $env:ANTHARES_ALLOWED_ROOTS = ($roots | Select-Object -Unique) -join ';'
} catch {
    Write-Error -Message ('AntharsWork initialization deferred: ' + $_.Exception.Message) -ErrorAction Continue
}

$v4Exe = Join-Path $root 'anthares-remote-agent-v4.exe'
$legacyExe = Join-Path $root 'anthares-remote-agent.exe'
$exe = if (Test-Path $v4Exe) { $v4Exe } elseif (Test-Path $legacyExe) { $legacyExe } else { $v4Exe }
$stdout = Join-Path $logRoot 'agent-system.stdout.log'
$stderr = Join-Path $logRoot 'agent-system.stderr.log'
$stateFile = Join-Path $runtimeRoot 'system-supervisor-state.json'

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\AntharesRemoteSystemSupervisorV9', [ref]$created)
if (-not $created) { exit 0 }

function Github-QueueConfigured {
    return (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY)) -and
           (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))
}
function Gitlab-QueueConfigured {
    return (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT)) -and
           (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))
}
function Queue-TransportConfigured { return (Github-QueueConfigured) -or (Gitlab-QueueConfigured) }
function Load-QueueAuth {
    if (Test-Path $queueAuthLoader) {
        try { . $queueAuthLoader }
        catch { Write-Error -Message ('issue queue auth load deferred: ' + $_.Exception.Message) -ErrorAction Continue }
    }
}
function Save-State([string]$reason, [int]$agentPid = 0) {
    try {
        [pscustomobject]@{
            active_control='private-issue-queues'
            mode='issue-queues-only'
            reason=$reason
            updated_at=(Get-Date).ToUniversalTime().ToString('o')
            supervisor_pid=$PID
            agent_pid=$agentPid
            device_id=$env:ANTHARES_DEVICE_ID
            identity='SYSTEM'
            session=0
            binary=(Split-Path $exe -Leaf)
            github_queue=[bool](Github-QueueConfigured)
            gitlab_queue=[bool](Gitlab-QueueConfigured)
            queue_failover=[bool](Queue-TransportConfigured)
            render_required=$false
            cloudflare_required=$false
            http_control_enabled=$false
            work_root=$env:ANTHARES_WORK_ROOT
            stdout_path=$stdout
            stderr_path=$stderr
            state_path=$stateFile
        } | ConvertTo-Json -Depth 4 | Set-Content -Path $stateFile -Encoding UTF8
    } catch {}
}
function Start-Agent {
    if (-not (Test-Path $exe)) { throw "agent executable not found: $exe" }
    Remove-Item Env:ANTHARES_CONTROL_URL -ErrorAction SilentlyContinue
    Save-State 'agent-start'
    return Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
}

try {
    # Session 0 only: retire stale/legacy writers without touching interactive UI.
    Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard','anthares-remote-agent-v4' -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 800

    while ($true) {
        Load-QueueAuth
        if (-not (Queue-TransportConfigured)) {
            Save-State 'waiting-for-private-queue-credential'
            Start-Sleep -Seconds 15
            continue
        }
        try { $proc = Start-Agent }
        catch {
            Save-State ('start-failed:' + $_.Exception.GetType().Name)
            Start-Sleep -Seconds 5
            continue
        }
        Save-State 'running-private-queue' $proc.Id
        while (-not $proc.HasExited) {
            Start-Sleep -Seconds 10
            Load-QueueAuth
            Save-State 'running-private-queue' $proc.Id
        }
        Save-State ('agent-exited:' + $proc.ExitCode)
        Start-Sleep -Seconds 2
    }
} finally {
    try { $mutex.ReleaseMutex() } catch {}
    $mutex.Dispose()
}
