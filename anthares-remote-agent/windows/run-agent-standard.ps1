$ErrorActionPreference = 'Continue'
$root = 'C:\ProgramData\AntharesRemoteAgent'
. (Join-Path $root 'agent-env.ps1')

$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP'
$primary = 'https://anthares-ara-control.onrender.com'
$secondary = 'https://anthares-ara-infra-canary-v2.onrender.com'
$exe = Join-Path $root 'anthares-remote-agent-standard.exe'
$stdout = Join-Path $root 'agent-standard.stdout.log'
$stderr = Join-Path $root 'agent-standard.stderr.log'
$stateFile = Join-Path $root 'standard-supervisor-state.json'

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\AntharesRemoteAgentStandardSupervisor', [ref]$created)
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

try {
    while ($true) {
        $existing = @(Get-Process -Name 'anthares-remote-agent-standard' -ErrorAction SilentlyContinue)
        if ($existing.Count -gt 0) {
            foreach ($p in $existing) {
                try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}
            }
            Start-Sleep -Seconds 2
        }

        if (Test-Control $primary) {
            $active = $primary
        } elseif (Test-Control $secondary) {
            $active = $secondary
        } else {
            Save-State '' 'both-controls-unavailable'
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

            if ($active -eq $secondary) {
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
            $alternate = if ($active -eq $primary) { $secondary } else { $primary }
            if (Test-Control $alternate) {
                Save-State $active ('switching-to:' + $alternate) $proc.Id
                try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
                try { $proc.WaitForExit(5000) | Out-Null } catch {}
                break
            }
            Save-State $active 'active-unhealthy-alternate-unavailable' $proc.Id
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
