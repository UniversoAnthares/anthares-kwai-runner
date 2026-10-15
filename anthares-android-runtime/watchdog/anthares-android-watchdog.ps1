param([int]$IntervalSeconds=30,[int]$BackoffMaxSeconds=300)
$ErrorActionPreference='Continue'
$env:USERPROFILE='C:\Users\Lucas'
$env:HOMEDRIVE='C:'
$env:HOMEPATH='\Users\Lucas'
$base=Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $base 'src\AntharesAndroidRuntime.psm1') -Force
$backoff=$IntervalSeconds
while ($true) {
    try {
        $leasePath='C:\ProgramData\AntharesAndroidRuntime\locks\memu4.json'
        $activeLease=$false
        if (Test-Path $leasePath) {
            try {
                $l=Get-Content $leasePath -Raw | ConvertFrom-Json
                $activeLease=([datetime]$l.expires_at -gt (Get-Date).ToUniversalTime())
            } catch {}
        }
        $h=Get-AntharesAndroidHealth
        if ($h.ok) { $backoff=$IntervalSeconds }
        elseif (-not $activeLease) {
            $r=Repair-AdbTransport -AllowBackendReset
            if ($r.ok) { $backoff=$IntervalSeconds } else { $backoff=[Math]::Min($backoff*2,$BackoffMaxSeconds) }
        }
    } catch { $backoff=[Math]::Min($backoff*2,$BackoffMaxSeconds) }
    Start-Sleep -Seconds $backoff
}
