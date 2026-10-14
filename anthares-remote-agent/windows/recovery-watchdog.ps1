$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$canonicalTask='Anthares Remote Agent SYSTEM'
$watchdogTask='Anthares Remote Recovery Watchdog'
$canonicalScript=Join-Path $root 'run-agent-system-supervisor.ps1'
$watchdogLoop=Join-Path $root 'recovery-watchdog-loop.ps1'
$exe=Join-Path $root 'anthares-remote-agent-v4.exe'
$lastGood=Join-Path $root 'anthares-remote-agent-v4.lastgood.exe'
$baseline=Join-Path $root 'integrity-baseline.json'
$log=Join-Path $root 'recovery-watchdog.log'
$state=Join-Path $root 'recovery-watchdog-state.json'
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Add-Content -Path $log -Encoding UTF8}catch{}}
function Get-SystemV4{@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq 0 -and $_.Name -eq 'anthares-remote-agent-v4.exe'})}
function Ensure-Task([string]$name,[string]$script){
  $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  $actionText=if($task){(($task.Actions|ForEach-Object{$_.Execute+' '+$_.Arguments}) -join ';')}else{''}
  $needs=(-not $task)-or([string]$task.Principal.UserId -notmatch '^(SYSTEM|SISTEMA|S-1-5-18)$')-or([string]$task.Principal.RunLevel -ne 'Highest')-or($actionText -notmatch [regex]::Escape($script))
  if($needs){
    $a=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$script+'"') -WorkingDirectory $root
    $tr=New-ScheduledTaskTrigger -AtStartup
    $pr=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $st=New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
    Register-ScheduledTask -TaskName $name -Action $a -Trigger $tr -Principal $pr -Settings $st -Force|Out-Null
    Log("repaired task $name")
  }
  Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
}
function Ensure-BinaryIntegrity{
  if(-not(Test-Path $exe)){throw 'v4 binary missing'}
  if(-not(Test-Path $baseline)){return}
  $expected=[string]((Get-Content $baseline -Raw|ConvertFrom-Json).v4_sha256)
  if([string]::IsNullOrWhiteSpace($expected)){return}
  $actual=(Get-FileHash $exe -Algorithm SHA256).Hash
  if($actual -eq $expected){return}
  if(-not(Test-Path $lastGood)){throw 'v4 hash mismatch and lastgood missing'}
  $backup=(Get-FileHash $lastGood -Algorithm SHA256).Hash
  if($backup -ne $expected){throw 'v4 hash mismatch and lastgood rejected'}
  Stop-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue
  Get-SystemV4|ForEach-Object{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}
  Copy-Item $lastGood $exe -Force
  if((Get-FileHash $exe -Algorithm SHA256).Hash -ne $expected){throw 'restored v4 hash mismatch'}
  Log('restored validated V4 binary')
}
try{
  Ensure-BinaryIntegrity
  $task=Ensure-Task $canonicalTask $canonicalScript
  $wd=Ensure-Task $watchdogTask $watchdogLoop
  $agents=@(Get-SystemV4)
  if($agents.Count -eq 0){
    Stop-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    Start-ScheduledTask -TaskName $canonicalTask -ErrorAction Stop
    Start-Sleep -Seconds 3
    $agents=@(Get-SystemV4)
  }
  [pscustomobject]@{
    updated_at=(Get-Date).ToUniversalTime().ToString('o');ok=$true;install_root=$root
    canonical_task_present=[bool]$task;watchdog_task_present=[bool]$wd
    canonical_task_state=[string]$task.State;watchdog_task_state=[string]$wd.State
    system_v4_count=$agents.Count;system_v4_pids=@($agents|ForEach-Object{$_.ProcessId})
    legacy_preserved_until_queue_proof=$true;role='canonical-root-recovery'
  }|ConvertTo-Json -Depth 4|Set-Content $state -Encoding UTF8
}catch{
  Log("recovery failed: $($_.Exception.Message)")
  try{[pscustomobject]@{updated_at=(Get-Date).ToUniversalTime().ToString('o');ok=$false;error=$_.Exception.Message}|ConvertTo-Json|Set-Content $state -Encoding UTF8}catch{}
}
