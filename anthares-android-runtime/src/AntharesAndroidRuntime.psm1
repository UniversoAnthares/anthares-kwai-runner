Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:RuntimeRoot = if ($env:ANTHARES_ANDROID_HOME) { $env:ANTHARES_ANDROID_HOME } else { 'C:\ProgramData\AntharesAndroidRuntime' }
$script:MEmuName = if ($env:ANTHARES_MEMU_VM) { $env:ANTHARES_MEMU_VM } else { 'MEmu_4' }
$script:MEmuRoot = if ($env:MEMU_HOME) { $env:MEMU_HOME } else { 'D:\Program Files\Microvirt\MEmu' }
$script:MEmuHyperv = if ($env:MEMU_HYPERV_HOME) { $env:MEMU_HYPERV_HOME } else { 'D:\Program Files\Microvirt\MEmuHyperv' }
$script:Adb = Join-Path $script:MEmuRoot 'adb.exe'
$script:Manager = Join-Path $script:MEmuHyperv 'MEmuManage.exe'
$script:Memuc = Join-Path $script:MEmuRoot 'memuc.exe'
$script:MEmuIndex = '4'

function Initialize-AntharesRuntime {
    foreach ($p in @($script:RuntimeRoot,(Join-Path $script:RuntimeRoot 'locks'),(Join-Path $script:RuntimeRoot 'evidence'))) {
        if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
    }
}

function Write-AntharesEvent {
    param([string]$Operation,[hashtable]$Data)
    Initialize-AntharesRuntime
    $event = [ordered]@{ timestamp=(Get-Date).ToUniversalTime().ToString('o'); operation=$Operation; backend='memu4'; data=$Data }
    $json = $event | ConvertTo-Json -Depth 8 -Compress
    Add-Content -Path (Join-Path $script:RuntimeRoot 'events.jsonl') -Value $json -Encoding UTF8
    $event | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $script:RuntimeRoot 'state.json') -Encoding UTF8
    return $event
}

function Invoke-External {
    param([string]$File,[string[]]$Arguments,[int]$TimeoutSec=12)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $File
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.Arguments = (($Arguments | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"','\"') + '"' } else { $_ } }) -join ' ')
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    try {
        [void]$p.Start()
        if (-not $p.WaitForExit($TimeoutSec*1000)) {
            try { $p.Kill() } catch {}
            return [ordered]@{ ok=$false; exit_code=$null; timed_out=$true; stdout=''; stderr='timeout' }
        }
        return [ordered]@{ ok=($p.ExitCode -eq 0); exit_code=$p.ExitCode; timed_out=$false; stdout=$p.StandardOutput.ReadToEnd(); stderr=$p.StandardError.ReadToEnd() }
    } catch {
        return [ordered]@{ ok=$false; exit_code=$null; timed_out=$false; stdout=''; stderr=$_.Exception.Message }
    } finally { if ($p) { $p.Dispose() } }
}

function Get-MEmuInfo {
    $r = Invoke-External $script:Manager @('showvminfo',$script:MEmuName,'--machinereadable') 10
    $state='unknown'; $serial=$null; $audio=$null
    if ($r.ok) {
        if ($r.stdout -match '(?m)^VMState="([^"]+)"') { $state=$Matches[1] }
        if ($r.stdout -match 'Forwarding\(\d+\)="ADB,tcp,127\.0\.0\.1,(\d+),') { $serial='127.0.0.1:'+$Matches[1] }
        if ($r.stdout -match '(?m)^audio="([^"]+)"') { $audio=$Matches[1] }
    }
    [ordered]@{ name=$script:MEmuName; state=$state; serial=$serial; audio=$audio; manager_ok=$r.ok; manager_error=$r.stderr.Trim() }
}

function Get-AdbDevices {
    if (-not (Test-Path $script:Adb)) { return [ordered]@{ ok=$false; devices=@{}; error='adb_missing' } }
    $r=Invoke-External $script:Adb @('devices','-l') 8
    $devices=@{}
    foreach ($line in ($r.stdout -split "`r?`n" | Select-Object -Skip 1)) {
        $parts=$line.Trim() -split '\s+'
        if ($parts.Count -ge 2 -and $parts[0]) { $devices[$parts[0]]=$parts[1] }
    }
    [ordered]@{ ok=$r.ok; devices=$devices; error=$r.stderr.Trim() }
}

function Invoke-Adb {
    param([string[]]$Arguments,[string]$Serial,[int]$TimeoutSec=10)
    $all=@(); if ($Serial) { $all += @('-s',$Serial) }; $all += $Arguments
    Invoke-External $script:Adb $all $TimeoutSec
}

function Get-AntharesAndroidHealth {
    $vm=Get-MEmuInfo
    $ds=Get-AdbDevices
    $transport='missing'
    if ($vm.serial -and $ds.devices.ContainsKey($vm.serial)) { $transport=$ds.devices[$vm.serial] }
    $boot=$false; $latency=$null; $package=$null
    if ($transport -eq 'device') {
        $sw=[Diagnostics.Stopwatch]::StartNew(); $b=Invoke-Adb @('shell','getprop','sys.boot_completed') $vm.serial 7; $sw.Stop(); $latency=$sw.ElapsedMilliseconds
        $boot=($b.ok -and $b.stdout.Trim() -eq '1')
        if ($boot) {
            $p=Invoke-Adb @('shell','pm','list','packages') $vm.serial 10
            if ($p.ok) {
                $candidates=@('com.kwai.video','kwai.lite.video','com.smile.gifmaker')
                $package=($candidates | Where-Object { $p.stdout -match ('package:'+ [regex]::Escape($_) +'(?:\r?$)') } | Select-Object -First 1)
                if (-not $package) {
                    $m=[regex]::Matches($p.stdout,'(?im)^package:([^\r\n]*(kwai|gifmaker)[^\r\n]*)$')
                    if ($m.Count -gt 0) { $package=$m[0].Groups[1].Value.Trim() }
                }
            }
        }
    }
    $score=0
    if ($vm.state -eq 'running') { $score+=20 }
    if ($transport -eq 'device') { $score+=30 }
    if ($boot) { $score+=30 }
    if ($package) { $score+=20 }
    $state = if ($vm.state -in @('poweroff','aborted','saved')) { 'STOPPED' } elseif ($vm.state -ne 'running') { 'DEGRADED' } elseif ($transport -eq 'offline') { 'RUNNING_TRANSPORT_OFFLINE' } elseif ($transport -eq 'unauthorized') { 'TRANSPORT_UNAUTHORIZED' } elseif ($transport -ne 'device') { 'TRANSPORT_MISSING' } elseif (-not $boot) { 'ANDROID_BOOTING' } elseif (-not $package) { 'APP_MISSING' } else { 'ANDROID_READY' }
    [ordered]@{ ok=($state -eq 'ANDROID_READY'); backend='memu4'; backend_state=$vm.state; state=$state; serial=$vm.serial; transport='adb'; transport_state=$transport; android_ready=$boot; adb_latency_ms=$latency; kwai_package=$package; audio=$vm.audio; health_score=$score }
}

function Start-MEmuBackend {
    $vm=Get-MEmuInfo
    if ($vm.state -eq 'running') { return [ordered]@{ ok=$true; action='already_running' } }
    $oldCompat=$env:__COMPAT_LAYER
    try {
        $env:__COMPAT_LAYER='RunAsInvoker'
        $r=Invoke-External $script:Memuc @('start','-i',$script:MEmuIndex) 35
    } finally {
        $env:__COMPAT_LAYER=$oldCompat
    }
    [ordered]@{ ok=$r.ok; action='start_official_launcher'; stderr=$r.stderr.Trim(); stdout=$r.stdout.Trim() }
}

function Stop-MEmuBackend {
    $r=Invoke-External $script:Manager @('controlvm',$script:MEmuName,'acpipowerbutton') 12
    [ordered]@{ ok=$r.ok; action='acpi_powerbutton'; stderr=$r.stderr.Trim() }
}

function Reset-MEmuBackend {
    $r=Invoke-External $script:Manager @('controlvm',$script:MEmuName,'reset') 15
    [ordered]@{ ok=$r.ok; action='vm_reset'; stderr=$r.stderr.Trim() }
}

function Repair-AdbTransport {
    param([switch]$AllowBackendReset)
    $before=Get-AntharesAndroidHealth
    if ($before.ok) { return [ordered]@{ ok=$true; action='already_healthy'; before=$before; after=$before } }
    if ($before.backend_state -ne 'running') { [void](Start-MEmuBackend) }
    $vm=Get-MEmuInfo
    if (-not $vm.serial) { return [ordered]@{ ok=$false; failure_class='TRANSPORT_MISSING'; before=$before; after=(Get-AntharesAndroidHealth) } }
    $steps=@(
        @('disconnect',$vm.serial),
        @('connect',$vm.serial),
        @('kill-server'),
        @('start-server'),
        @('connect',$vm.serial)
    )
    foreach ($step in $steps) {
        [void](Invoke-Adb $step $null 7)
        $deadline=(Get-Date).AddSeconds(6)
        do {
            $h=Get-AntharesAndroidHealth
            if ($h.ok) {
                $result=[ordered]@{ ok=$true; action='adb_recovered'; before=$before; after=$h }
                [void](Write-AntharesEvent 'recover_transport' $result)
                return $result
            }
            Start-Sleep -Milliseconds 750
        } while ((Get-Date) -lt $deadline)
    }
    if ($AllowBackendReset) {
        [void](Reset-MEmuBackend)
        $deadline=(Get-Date).AddSeconds(45)
        do {
            $h=Get-AntharesAndroidHealth
            if ($h.ok) {
                $result=[ordered]@{ ok=$true; action='backend_reset_recovered'; before=$before; after=$h }
                [void](Write-AntharesEvent 'recover_transport' $result)
                return $result
            }
            Start-Sleep -Seconds 2
        } while ((Get-Date) -lt $deadline)
    }
    $result=[ordered]@{ ok=$false; failure_class='RECOVERY_EXHAUSTED'; before=$before; after=(Get-AntharesAndroidHealth) }
    [void](Write-AntharesEvent 'recover_transport' $result)
    return $result
}

function Get-ForegroundApp {
    $h=Get-AntharesAndroidHealth
    if ($h.transport_state -ne 'device') { return [ordered]@{ ok=$false; failure_class='TRANSPORT_OFFLINE'; health=$h } }
    $r=Invoke-Adb @('shell','dumpsys','window','windows') $h.serial 8
    $line=($r.stdout -split "`r?`n" | Where-Object { $_ -match 'mCurrentFocus|mFocusedApp' } | Select-Object -First 1)
    [ordered]@{ ok=$r.ok; foreground=$line.Trim(); serial=$h.serial }
}

function Start-Kwai {
    $h=Get-AntharesAndroidHealth
    if (-not $h.kwai_package) { return [ordered]@{ ok=$false; failure_class='APP_MISSING'; health=$h } }
    $r=Invoke-Adb @('shell','monkey','-p',$h.kwai_package,'-c','android.intent.category.LAUNCHER','1') $h.serial 12
    [ordered]@{ ok=$r.ok; package=$h.kwai_package; stderr=$r.stderr.Trim() }
}

function Get-UiDump {
    $h=Get-AntharesAndroidHealth
    if ($h.transport_state -ne 'device') { return [ordered]@{ ok=$false; failure_class='TRANSPORT_OFFLINE' } }
    [void](Invoke-Adb @('shell','uiautomator','dump','/sdcard/window.xml') $h.serial 12)
    $r=Invoke-Adb @('shell','cat','/sdcard/window.xml') $h.serial 10
    [ordered]@{ ok=$r.ok; xml=$r.stdout }
}

function Get-KwaiIdentitySignal {
    $h=Get-AntharesAndroidHealth
    if (-not $h.ok) { return [ordered]@{ ok=$false; identity=$null; failure_class=$h.state; health=$h } }
    $fg=Get-ForegroundApp
    $ui=Get-UiDump
    $expected='@lucasrosalem'
    $hits=@()
    if ($ui.ok -and $ui.xml -match [regex]::Escape($expected)) { $hits += 'ui_exact_username' }
    if ($fg.ok -and $fg.foreground -match [regex]::Escape($h.kwai_package)) { $hits += 'foreground_kwai_package' }
    $identity=if ($hits -contains 'ui_exact_username') { $expected } else { $null }
    [ordered]@{ ok=($identity -eq $expected -and $hits.Count -ge 2); identity=$identity; expected=$expected; signals=$hits; package=$h.kwai_package; foreground=$fg.foreground }
}

function Acquire-DeviceLease {
    param([string]$Owner,[int]$TtlSeconds=120)
    Initialize-AntharesRuntime
    $path=Join-Path $script:RuntimeRoot 'locks\memu4.json'
    $now=(Get-Date).ToUniversalTime()
    if (Test-Path $path) {
        try { $old=Get-Content $path -Raw | ConvertFrom-Json; if ([datetime]$old.expires_at -gt $now -and $old.owner -ne $Owner) { return [ordered]@{ ok=$false; failure_class='LOCK_TIMEOUT'; owner=$old.owner; expires_at=$old.expires_at } } } catch {}
    }
    $lease=[ordered]@{ owner=$Owner; acquired_at=$now.ToString('o'); expires_at=$now.AddSeconds($TtlSeconds).ToString('o') }
    $lease | ConvertTo-Json | Set-Content $path -Encoding UTF8
    [ordered]@{ ok=$true; lease=$lease }
}

function Release-DeviceLease {
    param([string]$Owner)
    $path=Join-Path $script:RuntimeRoot 'locks\memu4.json'
    if (-not (Test-Path $path)) { return [ordered]@{ ok=$true; action='already_free' } }
    try { $old=Get-Content $path -Raw | ConvertFrom-Json; if ($old.owner -ne $Owner) { return [ordered]@{ ok=$false; failure_class='LOCK_TIMEOUT'; owner=$old.owner } } catch {}
    Remove-Item $path -Force
    [ordered]@{ ok=$true; action='released' }
}

Export-ModuleMember -Function Initialize-AntharesRuntime,Get-MEmuInfo,Get-AdbDevices,Get-AntharesAndroidHealth,Repair-AdbTransport,Start-MEmuBackend,Stop-MEmuBackend,Reset-MEmuBackend,Get-ForegroundApp,Start-Kwai,Get-UiDump,Get-KwaiIdentitySignal,Acquire-DeviceLease,Release-DeviceLease,Write-AntharesEvent
