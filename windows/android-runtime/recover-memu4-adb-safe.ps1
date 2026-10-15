# Anthares MEmu4 ADB recovery; safe for existing Kwai app data.
# Execute on the Windows host, not on GitHub-hosted runners.
$ErrorActionPreference = 'Stop'
$base = 'D:\Program Files\Microvirt\MEmu'
$adb = Join-Path $base 'adb.exe'
$mgr = 'D:\Program Files\Microvirt\MEmuHyperv\MEmuManage.exe'
$vm = 'MEmu_4'
if (!(Test-Path $adb) -or !(Test-Path $mgr)) { throw 'MEmu binaries missing' }
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
$before=Probe
$steps=New-Object System.Collections.Generic.List[string]
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
} else {$after=$before}
$result=[ordered]@{timestamp=(Get-Date).ToUniversalTime().ToString('o');before=$before;after=$after;steps=@($steps);ok=[bool]$after.healthy;data_preserved=$true}
$result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $log
$result|ConvertTo-Json -Depth 8
if(-not $after.healthy){exit 2}
