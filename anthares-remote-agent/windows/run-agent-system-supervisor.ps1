$ErrorActionPreference = 'Continue'
$root = 'C:\ProgramData\AntharesRemoteAgent'
$envFile = Join-Path $root 'agent-env.ps1'
if (Test-Path $envFile) { . $envFile }
$queueAuthLoader = Join-Path $root 'load-issue-queue-auth.ps1'
if (Test-Path $queueAuthLoader) {
    try { . $queueAuthLoader } catch { Write-Error -Message ('issue queue auth load deferred: ' + $_.Exception.Message) -ErrorAction Continue }
}

# Keep mutable Anthares runtime data off the nearly-full system drive. The
# executable and protected credentials stay under ProgramData, while temporary
# files, browser profiles, downloads, installers and other work products live on D:.
$workRoot = ([string]$env:ANTHARES_WORK_ROOT).Trim()
if ([string]::IsNullOrWhiteSpace($workRoot)) { $workRoot = 'D:\AntharsWork' }
try {
    @($workRoot, (Join-Path $workRoot 'temp'), (Join-Path $workRoot 'logs'), (Join-Path $workRoot 'downloads'), (Join-Path $workRoot 'installers'), (Join-Path $workRoot 'ara-jobs'), (Join-Path $workRoot 'browser-profiles')) |
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

# Canonical runtime: one SYSTEM agent, one device identity, no interactive desktop.
# Cloudflare provides the normal zero-cost HTTP controls. GitHub/GitLab private
# issue queues are independent transports when encrypted credentials are present.
# Render is intentionally absent from all defaults and normal operation.
$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP'
$v4Exe = Join-Path $root 'anthares-remote-agent-v4.exe'
$legacyExe = Join-Path $root 'anthares-remote-agent.exe'
$exe = if (Test-Path $v4Exe) { $v4Exe } else { $legacyExe }
$stdout = Join-Path $root 'agent-system.stdout.log'
$stderr = Join-Path $root 'agent-system.stderr.log'
$stateFile = Join-Path $root 'system-supervisor-state.json'

function Control-OrDefault([string]$value, [string]$fallback) {
    $candidate = ([string]$value).Trim().TrimEnd('/')
    if ([string]::IsNullOrWhiteSpace($candidate)) { return $fallback }
    if ($candidate -match 'onrender\.com') { return $fallback }
    return $candidate
}
$primaryControl = Control-OrDefault $env:ANTHARES_CONTROL_PRIMARY_URL 'https://anthares-ara-backup.anthares1.workers.dev'
$secondaryControl = Control-OrDefault $env:ANTHARES_CONTROL_SECONDARY_URL 'https://anthares-control.anthares1.workers.dev'
$tertiaryControl = ([string]$env:ANTHARES_CONTROL_TERTIARY_URL).Trim().TrimEnd('/')
if ($tertiaryControl -match 'onrender\.com') { $tertiaryControl = '' }
$httpCandidates = @($primaryControl, $secondaryControl, $tertiaryControl) |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    Select-Object -Unique

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\AntharesRemoteSystemSupervisorV6', [ref]$created)
if (-not $created) { exit 0 }

function Test-Control([string]$origin) {
    if ([string]::IsNullOrWhiteSpace($origin) -or $origin -notmatch '^https://') { return $false }
    foreach ($healthPath in @('/healthz', '/health')) {
        try {
            $r = Invoke-WebRequest -UseBasicParsing -Uri ($origin + $healthPath) -TimeoutSec 10
            if ([int]$r.StatusCode -ge 200 -and [int]$r.StatusCode -lt 300) { return $true }
        } catch {}
    }
    return $false
}
function Github-QueueConfigured { return (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY)) -and (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN)) }
function Gitlab-QueueConfigured { return (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT)) -and (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN)) }
function Queue-TransportConfigured { return (Github-QueueConfigured) -or (Gitlab-QueueConfigured) }
function Choose-Control { foreach ($candidate in $httpCandidates) { if (Test-Control $candidate) { return $candidate } }; return $null }

function Save-State([string]$active, [string]$mode, [string]$reason, [int]$agentPid = 0) {
    try {
        [pscustomobject]@{
            active_control=$active; mode=$mode; reason=$reason; updated_at=(Get-Date).ToUniversalTime().ToString('o')
            supervisor_pid=$PID; agent_pid=$agentPid; device_id=$env:ANTHARES_DEVICE_ID; identity='SYSTEM'; session=0
            binary=(Split-Path $exe -Leaf); github_queue=[bool](Github-QueueConfigured); gitlab_queue=[bool](Gitlab-QueueConfigured)
            queue_failover=[bool](Queue-TransportConfigured); cloudflare_controls=$true; render_required=$false
            work_root=$env:ANTHARES_WORK_ROOT; http_candidates=@($httpCandidates)
        } | ConvertTo-Json -Depth 4 | Set-Content -Path $stateFile -Encoding UTF8
    } catch {}
}
function Start-Agent([string]$control, [string]$mode) {
    if (-not (Test-Path $exe)) { throw "agent executable not found: $exe" }
    if ([string]::IsNullOrWhiteSpace($control)) { Remove-Item Env:ANTHARES_CONTROL_URL -ErrorAction SilentlyContinue } else { $env:ANTHARES_CONTROL_URL = $control }
    Save-State $control $mode 'agent-start'
    return Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
}

try {
    while ($true) {
        # Never kill another agent instance merely because this supervisor was
        # restarted. Preserve the live control path and wait for a clean handoff.
        $existing = @(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard','anthares-remote-agent-v4' -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) { Save-State '' 'preserve-existing' 'waiting-for-existing-agent'; Start-Sleep -Seconds 5; continue }
        if (Test-Path $queueAuthLoader) { try { . $queueAuthLoader } catch { Write-Error -Message ('issue queue auth reload deferred: ' + $_.Exception.Message) -ErrorAction Continue } }
        $queueReady = Queue-TransportConfigured
        $active = Choose-Control
        if ($queueReady) { $mode = if ($active) { 'issue-queues+cloudflare-http' } else { 'issue-queues-only' } }
        elseif ($active) { $mode = 'cloudflare-http-only' }
        else { Save-State '' 'waiting' 'all-control-transports-unavailable'; Start-Sleep -Seconds 10; continue }
        try { $proc = Start-Agent $active $mode } catch { Save-State $active $mode ('start-failed:' + $_.Exception.GetType().Name); Start-Sleep -Seconds 5; continue }
        Save-State $active $mode 'running' $proc.Id
        $activeFailures = 0
        while (-not $proc.HasExited) {
            Start-Sleep -Seconds 10
            if (Queue-TransportConfigured) {
                $currentControlHealthy = $false; if ($active) { $currentControlHealthy = Test-Control $active }
                $reason = if ($currentControlHealthy) { 'running-queue-with-cloudflare-http' } else { 'running-queue-failover' }
                Save-State $active $mode $reason $proc.Id
                if (-not $currentControlHealthy) { $active = Choose-Control }
                continue
            }
            if ($active -and (Test-Control $active)) { $activeFailures = 0; continue }
            $activeFailures++
            if ($activeFailures -lt 2) { continue }
            $alternate = Choose-Control
            if ($alternate -and $alternate -ne $active) {
                Save-State $active $mode ('switching-to:' + $alternate) $proc.Id
                try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                try { $proc.WaitForExit(5000) | Out-Null } catch {}
                break
            }
            Save-State $active $mode 'http-unhealthy-no-alternate' $proc.Id; $activeFailures = 0
        }
        if ($proc.HasExited) { Save-State $active $mode ('agent-exited:' + $proc.ExitCode) }
        Start-Sleep -Seconds 2
    }
} finally { try { $mutex.ReleaseMutex() } catch {}; $mutex.Dispose() }
