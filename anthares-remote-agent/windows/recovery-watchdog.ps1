$ErrorActionPreference='Continue'
$root='D:\AntharsWork\AntharesRemoteAgent'
$canonicalTask='Anthares Remote Agent SYSTEM'
$watchdogTask='Anthares Remote Recovery Watchdog'
$userTask='Anthares Remote Agent User'
$canonicalScript=Join-Path $root 'run-agent-system-supervisor.ps1'
$watchdogLoop=Join-Path $root 'recovery-watchdog-loop.ps1'
$exe=Join-Path $root 'anthares-remote-agent-v4.exe'
$lastGood=Join-Path $root 'anthares-remote-agent-v4.lastgood.exe'
$baseline=Join-Path $root 'integrity-baseline.json'
$log=Join-Path $root 'recovery-watchdog.log'
$state=Join-Path $root 'recovery-watchdog-state.json'
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Add-Content -Path $log -Encoding UTF8}catch{}}
function Get-SystemAgents{@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq 0 -and $_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'})}
function Retire-InteractiveAgents{
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -ne 0 -and $_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'}|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue;Log("retired interactive agent pid=$($_.ProcessId)")}catch{}}
  try{$t=Get-ScheduledTask -TaskName $userTask -ErrorAction SilentlyContinue;if($t){Disable-ScheduledTask -TaskName $userTask -ErrorAction SilentlyContinue|Out-Null}}catch{}
}
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
  if(-not (Test-Path $baseline)){return $false}
  try{$expected=[string]((Get-Content $baseline -Raw|ConvertFrom-Json).v4_sha256)}catch{return $false}
  if([string]::IsNullOrWhiteSpace($expected)){return $false}
  $current=if(Test-Path $exe){(Get-FileHash $exe -Algorithm SHA256).Hash}else{''}
  if($current -eq $expected){return $false}
  $backup=if(Test-Path $lastGood){(Get-FileHash $lastGood -Algorithm SHA256).Hash}else{''}
  if($backup -ne $expected){Log("rollback refused: lastgood hash does not match baseline");return $false}
  Log("binary mismatch detected; restoring lastgood")
  try{Stop-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue}catch{}
  Get-SystemAgents|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}catch{}}
  Start-Sleep -Milliseconds 500
  try {
    Copy-Item $lastGood $exe -Force -ErrorAction Stop
    $restored=(Get-FileHash $exe -Algorithm SHA256 -ErrorAction Stop).Hash
    if($restored -ne $expected){throw "restored binary hash mismatch"}
    Log("automatic rollback restored sha256=$expected")
    return $true
  } catch {
    Log("automatic rollback failed: $($_.Exception.Message)")
    return $false
  }
}
New-Item -ItemType Directory -Force -Path $root|Out-Null
Retire-InteractiveAgents
$rolledBack=Ensure-BinaryIntegrity
# Never start an unverified binary when a pinned integrity baseline exists.
if(Test-Path $baseline){
  try {
    $expected=[string]((Get-Content $baseline -Raw -ErrorAction Stop|ConvertFrom-Json).v4_sha256)
    $actual=if(Test-Path $exe){(Get-FileHash $exe -Algorithm SHA256 -ErrorAction Stop).Hash}else{''}
    if(-not [string]::IsNullOrWhiteSpace($expected) -and $actual -ne $expected){
      Log('recovery halted: binary integrity mismatch remains after rollback attempt')
      return
    }
  } catch {
    Log("recovery halted: unable to verify integrity baseline: $($_.Exception.Message)")
    return
  }
}
$task=Ensure-Task $canonicalTask $canonicalScript
$wd=Ensure-Task $watchdogTask $watchdogLoop
$agents=@(Get-SystemAgents)
if($rolledBack -or $agents.Count -eq 0 -or -not $task -or [string]$task.State -ne 'Running'){
  try{Start-ScheduledTask -TaskName $canonicalTask -ErrorAction Stop;Start-Sleep 3;Log('started canonical SYSTEM task')}catch{Log("canonical task start failed: $($_.Exception.GetType().Name)")}
  $agents=@(Get-SystemAgents)
}
try{[pscustomobject]@{
  updated_at=(Get-Date).ToUniversalTime().ToString('o');install_root=$root;automatic_rollback=$rolledBack
  canonical_task_present=[bool](Get-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue)
  watchdog_task_present=[bool](Get-ScheduledTask -TaskName $watchdogTask -ErrorAction SilentlyContinue)
  system_agent_count=$agents.Count;system_agent_pids=@($agents|ForEach-Object{$_.ProcessId})
  interactive_agent_count=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -ne 0 -and $_.Name -like 'anthares-remote-agent*'}).Count
  role='canonical-root-recovery'
}|ConvertTo-Json -Depth 4|Set-Content $state -Encoding UTF8}catch{}
