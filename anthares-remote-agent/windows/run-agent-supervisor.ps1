$ErrorActionPreference = 'Continue'
$root = 'C:\ProgramData\AntharesRemoteAgent'
. (Join-Path $root 'agent-env.ps1')

# The fallback supervisor must never share the standard agent's queue or result
# spool. A distinct device identity prevents duplicate leases and conflicting
# result replays while preserving the same device credential and capabilities.
$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP-SYSTEM'

$primary = 'https://anthares-ara-control.onrender.com'
$secondary = 'https://anthares-ara-infra-canary-v2.onrender.com'
$tertiary = 'https://anthares-ara-backup.anthares1.workers.dev'
$exe = Join-Path $root 'anthares-remote-agent.exe'
$stdout = Join-Path $root 'agent.stdout.log'
$stderr = Join-Path $root 'agent.stderr.log'
$stateFile = Join-Path $root 'supervisor-state.json'
$forceSecondary = Join-Path $root 'force-secondary.flag'
$forceTertiary = Join-Path $root 'force-tertiary.flag'

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\AntharesRemoteAgentSupervisor', [ref]$created)
if (-not $created) { exit 0 }

function Test-Control([string]$origin) {
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
        } | ConvertTo-Json | Set-Content -Path $stateFile -Encoding UTF8
    } catch {}
}

function Choose-Control {
    if (Test-Path $forceTertiary) {
        if (Test-Control $tertiary) { return $tertiary }
        if (Test-Control $primary) { return $primary }
        if (Test-Control $secondary) { return $secondary }
        return $null
    }
    if (Test-Path $forceSecondary) {
        if (Test-Control $secondary) { return $secondary }
        if (Test-Control $primary) { return $primary }
        if (Test-Control $tertiary) { return $tertiary }
        return $null
    }
    if (Test-Control $primary) { return $primary }
    if (Test-Control $secondary) { return $secondary }
    if (Test-Control $tertiary) { return $tertiary }
    return $null
}

function Preferred-Alternate([string]$active) {
    foreach ($candidate in @($primary, $secondary, $tertiary)) {
        if ($candidate -eq $active) { continue }
        if (Test-Control $candidate) { return $candidate }
    }
    return $null
}

try {
    while ($true) {
        $existing = @(Get-Process -Name 'anthares-remote-agent' -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) {
            foreach ($p in $existing) {
                try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}
            }
            Start-Sleep -Seconds 2
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

            if (Test-Path $forceTertiary) {
                if ($active -ne $tertiary -and (Test-Control $tertiary)) {
                    Save-State $active 'forced-switch-to-tertiary' $proc.Id
                    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                    try { $proc.WaitForExit(5000) | Out-Null } catch {}
                    break
                }
            } elseif (Test-Path $forceSecondary) {
                if ($active -ne $secondary -and (Test-Control $secondary)) {
                    Save-State $active 'forced-switch-to-secondary' $proc.Id
                    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                    try { $proc.WaitForExit(5000) | Out-Null } catch {}
                    break
                }
            } elseif ($active -ne $primary) {
                if (Test-Control $primary) {
                    $primaryHealthyStreak++
                } else {
                    $primaryHealthyStreak = 0
                }
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
