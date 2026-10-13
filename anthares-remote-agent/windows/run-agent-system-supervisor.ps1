$ErrorActionPreference = 'Continue'
$root = 'C:\ProgramData\AntharesRemoteAgent'
. (Join-Path $root 'agent-env.ps1')

# Canonical Anthares Remote runtime: one SYSTEM agent, one device identity,
# independent zero-cost control-plane candidates, no interactive desktop.
$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP'

# Render is intentionally absent from the canonical path. Cloudflare Workers are
# persistent controls; GitHub Actions is the finite-job watchdog/emergency executor.
$primary = 'https://anthares-ara-backup.anthares1.workers.dev'
$secondary = 'https://anthares-control.anthares1.workers.dev'
$tertiary = ($env:ANTHARES_CONTROL_TERTIARY_URL | ForEach-Object { [string]$_ }).TrimEnd('/')
$exe = Join-Path $root 'anthares-remote-agent.exe'
$stdout = Join-Path $root 'agent-system.stdout.log'
$stderr = Join-Path $root 'agent-system.stderr.log'
$stateFile = Join-Path $root 'system-supervisor-state.json'
$forceSecondary = Join-Path $root 'force-secondary.flag'
$forceTertiary = Join-Path $root 'force-tertiary.flag'

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\AntharesRemoteSystemSupervisorV3', [ref]$created)
if (-not $created) { exit 0 }

function Test-Control([string]$origin) {
    if ([string]::IsNullOrWhiteSpace($origin)) { return $false }
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri ($origin + '/healthz') -TimeoutSec 12
        return ([int]$r.StatusCode -ge 200 -and [int]$r.StatusCode -lt 300)
    } catch {
        return $false
    }
}

function Save-State([string]$active, [string]$reason, [int]$agentPid = 0) {
    try {
        [pscustomobject]@{
            active_control = $active
            reason = $reason
            updated_at = (Get-Date).ToUniversalTime().ToString('o')
            supervisor_pid = $PID
            agent_pid = $agentPid
            device_id = $env:ANTHARES_DEVICE_ID
            identity = 'SYSTEM'
            session = 0
            render_required = $false
        } | ConvertTo-Json | Set-Content -Path $stateFile -Encoding UTF8
    } catch {}
}

function Candidate-Controls {
    @($primary, $secondary, $tertiary) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique
}

function Choose-Control {
    if ((Test-Path $forceTertiary) -and (Test-Control $tertiary)) { return $tertiary }
    if ((Test-Path $forceSecondary) -and (Test-Control $secondary)) { return $secondary }
    foreach ($candidate in (Candidate-Controls)) {
        if (Test-Control $candidate) { return $candidate }
    }
    return $null
}

function Preferred-Alternate([string]$active) {
    foreach ($candidate in (Candidate-Controls)) {
        if ($candidate -eq $active) { continue }
        if (Test-Control $candidate) { return $candidate }
    }
    return $null
}

try {
    while ($true) {
        # Never terminate agents that this supervisor did not start.
        # An existing agent may belong to a healthy recovery or admin channel.
        # Wait for it to exit rather than stealing its identity or leases.
        $existing = @(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard' -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) {
            Save-State '' 'waiting-for-existing-agent'
            Start-Sleep -Seconds 5
            continue
        }

        $active = Choose-Control
        if (-not $active) {
            Save-State '' 'all-controls-unavailable'
            Start-Sleep -Seconds 5
            continue
        }

        $env:ANTHARES_CONTROL_URL = $active
        Save-State $active 'agent-start'
        try {
            $proc = Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        } catch {
            Save-State $active ('start-failed:' + $_.Exception.GetType().Name)
            Start-Sleep -Seconds 5
            continue
        }

        Save-State $active 'running' $proc.Id
        $activeFailures = 0
        $primaryHealthyStreak = 0

        while (-not $proc.HasExited) {
            Start-Sleep -Seconds 10

            if ((Test-Path $forceTertiary) -and (Test-Control $tertiary)) {
                if ($active -ne $tertiary) {
                    Save-State $active 'forced-switch-to-tertiary' $proc.Id
                    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                    try { $proc.WaitForExit(5000) | Out-Null } catch {}
                    break
                }
            } elseif ((Test-Path $forceSecondary) -and (Test-Control $secondary)) {
                if ($active -ne $secondary) {
                    Save-State $active 'forced-switch-to-secondary' $proc.Id
                    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                    try { $proc.WaitForExit(5000) | Out-Null } catch {}
                    break
                }
            } elseif ($active -ne $primary) {
                if (Test-Control $primary) { $primaryHealthyStreak++ } else { $primaryHealthyStreak = 0 }
                if ($primaryHealthyStreak -ge 6) {
                    Save-State $active 'primary-stable-failback' $proc.Id
                    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                    try { $proc.WaitForExit(5000) | Out-Null } catch {}
                    break
                }
            }

            if (Test-Control $active) {
                $activeFailures = 0
                continue
            }

            $activeFailures++
            if ($activeFailures -lt 2) { continue }
            $alternate = Preferred-Alternate $active
            if ($alternate) {
                Save-State $active ('switching-to:' + $alternate) $proc.Id
                try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                try { $proc.WaitForExit(5000) | Out-Null } catch {}
                break
            }
            Save-State $active 'active-unhealthy-no-alternate' $proc.Id
            $activeFailures = 0
        }

        if ($proc.HasExited) {
            Save-State $active ('agent-exited:' + $proc.ExitCode)
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    try { $mutex.ReleaseMutex() } catch {}
    $mutex.Dispose()
}
