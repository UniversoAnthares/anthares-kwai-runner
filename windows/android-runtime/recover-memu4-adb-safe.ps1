# Anthares MEmu4 ADB recovery; safe for existing Kwai app data.
# Execute on the Windows host, not on GitHub-hosted runners.
$ErrorActionPreference = 'Stop'
$base = 'D:\Program Files\Microvirt\MEmu'
$adb = Join-Path $base 'adb.exe'
$memuc = Join-Path $base 'memuc.exe'
$mgr = 'D:\Program Files\Microvirt\MEmuHyperv\MEmuManage.exe'
$vm = 'MEmu_4'
if (!(Test-Path $adb) -or !(Test-Path $mgr) -or !(Test-Path $memuc)) { throw 'MEmu binaries missing' }

# MEmuHyperv stores its canonical registry under the interactive Lucas profile.
# The Anthares Remote Agent runs as SYSTEM, so every MEmu control call must inherit
# the canonical profile instead of creating/reading a SYSTEM-local hypervisor context.
$env:USERPROFILE = 'C:\Users\Lucas'
$env:HOMEDRIVE = 'C:'
$env:HOMEPATH = '\Users\Lucas'

$info = (& $mgr showvminfo $vm --machinereadable 2>&1 | Out-String)
if ($info -notmatch '(?m)^VMState="running"') { throw 'VM is not running; do not reset automatically' }
if ($info -notmatch 'Forwarding\(\d+\)="ADB,tcp,127\.0\.0\.1,(\d+),') { throw 'ADB forwarding port unavailable' }
$serial = '127.0.0.1:' + $Matches[1]
$logDir = 'C:\ProgramData\AntharesRemoteAgent\android-runtime'
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir 'memu4-adb-recovery.json'

function Probe {
  $devices = (& $adb devices -l 2>&1 | Out-String)
  $transport = if ($devices -match [regex]::Escape($serial) + '\s+device\b') {'device'} elseif ($devices -match [regex]::Escape($serial) + '\s+offline\b') {'offline'} else {'missing'}
  $boot = if ($transport -eq 'device') { (& $adb -s $serial shell getprop sys.boot_completed 2>&1 | Out-String).Trim() } else { '' }
  [ordered]@{serial=$serial;transport=$transport;boot=$boot;healthy=($transport -eq 'device' -and $boot -eq '1')}
}

function Invoke-MEmuGuest([string]$Command) {
  (& $memuc -n $vm execcmd $Command 2>&1 | Out-String).Trim()
}

function Repair-GuestAdbTcp {
  # This path is independent of the host ADB server. It is deliberately attempted
  # before any VM reset because MEmu can expose a fully booted Android whose adbd
  # is running but has service.adb.tcp.port unset.
  $boot = Invoke-MEmuGuest '/system/bin/getprop sys.boot_completed'
  $adbd = Invoke-MEmuGuest '/system/bin/getprop init.svc.adbd'
  $port = Invoke-MEmuGuest '/system/bin/getprop service.adb.tcp.port'
  if ($boot -ne '1' -or $adbd -ne 'running') {
    return [ordered]@{attempted=$true;ok=$false;boot=$boot;adbd=$adbd;port=$port;reason='guest_not_ready'}
  }
  if ($port -ne '5555') {
    [void](Invoke-MEmuGuest '/system/bin/setprop service.adb.tcp.port 5555')
    [void](Invoke-MEmuGuest '/system/bin/setprop persist.adb.tcp.port 5555')
    [void](Invoke-MEmuGuest '/system/bin/setprop ctl.restart adbd')
    Start-Sleep -Seconds 4
  }
  $verifiedPort = Invoke-MEmuGuest '/system/bin/getprop service.adb.tcp.port'
  $verifiedAdbd = Invoke-MEmuGuest '/system/bin/getprop init.svc.adbd'
  & $adb disconnect $serial 2>&1 | Out-Null
  & $adb connect $serial 2>&1 | Out-Null
  Start-Sleep -Seconds 3
  $after = Probe
  [ordered]@{attempted=$true;ok=[bool]$after.healthy;boot=$boot;adbd=$verifiedAdbd;port=$verifiedPort;after=$after}
}

$before=Probe
$steps=New-Object System.Collections.Generic.List[string]
$guestRepair=$null
if (-not $before.healthy) {
  & $adb start-server | Out-Null; $steps.Add('start-server')
  & $adb disconnect $serial | Out-Null; $steps.Add('disconnect')
  & $adb connect $serial | Out-Null; $steps.Add('connect')
  for ($i=0;$i -lt 15;$i++){Start-Sleep -Seconds 2;$after=Probe;if($after.healthy){break}}
  if (-not $after.healthy) {
    # Recycle host ADB server only; VM, virtual disks and Kwai app data remain untouched.
    & $adb kill-server | Out-Null; $steps.Add('kill-server')
    Start-Sleep -Seconds 2
    & $adb start-server | Out-Null; $steps.Add('restart-server')
    & $adb connect $serial | Out-Null; $steps.Add('reconnect')
    for ($i=0;$i -lt 15;$i++){Start-Sleep -Seconds 2;$after=Probe;if($after.healthy){break}}
  }
  if (-not $after.healthy) {
    $guestRepair=Repair-GuestAdbTcp
    $steps.Add('guest-adbd-tcp-repair')
    $after=Probe
  }
} else {$after=$before}
$result=[ordered]@{timestamp=(Get-Date).ToUniversalTime().ToString('o');before=$before;after=$after;steps=@($steps);guest_repair=$guestRepair;ok=[bool]$after.healthy;data_preserved=$true;backend_reset_used=$false}
$result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $log
$result|ConvertTo-Json -Depth 8
if(-not $after.healthy){exit 2}
