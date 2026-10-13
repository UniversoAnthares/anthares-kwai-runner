$ErrorActionPreference='Continue'
$root='D:\AntharsWork\AntharesRemoteAgent'
$canonicalTask='Anthares Remote Agent SYSTEM'
$watchdogTask='Anthares Remote Recovery Watchdog'
$userTask='Anthares Remote Agent User'
$canonicalScript=Join-Path $root 'run-agent-system-supervisor.ps1'
$watchdogLoop=Join-Path $root 'recovery-watchdog-loop.ps1'
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
New-Item -ItemType Directory -Force -Path $root|Out-Null
Retire-InteractiveAgents
$task=Ensure-Task $canonicalTask $canonicalScript
$wd=Ensure-Task $watchdogTask $watchdogLoop
$agents=@(Get-SystemAgents)
if($agents.Count -eq 0 -or -not $task -or [string]$task.State -ne 'Running'){
  try{Start-ScheduledTask -TaskName $canonicalTask -ErrorAction Stop;Start-Sleep 3;Log('started canonical SYSTEM task')}catch{Log("canonical task start failed: $($_.Exception.GetType().Name)")}
  $agents=@(Get-SystemAgents)
}
try{[pscustomobject]@{
  updated_at=(Get-Date).ToUniversalTime().ToString('o');install_root=$root
  canonical_task_present=[bool](Get-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue)
  watchdog_task_present=[bool](Get-ScheduledTask -TaskName $watchdogTask -ErrorAction SilentlyContinue)
  system_agent_count=$agents.Count;system_agent_pids=@($agents|ForEach-Object{$_.ProcessId})
  interactive_agent_count=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -ne 0 -and $_.Name -like 'anthares-remote-agent*'}).Count
  role='canonical-root-recovery'
}|ConvertTo-Json -Depth 4|Set-Content $state -Encoding UTF8}catch{}
