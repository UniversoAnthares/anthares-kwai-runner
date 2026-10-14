$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$canonicalTask='Anthares Remote Agent SYSTEM'
$watchdogTask='Anthares Remote Recovery Watchdog'
$canonicalScript=Join-Path $root 'run-agent-system-supervisor.ps1'
$queueLoader=Join-Path $root 'load-issue-queue-auth.ps1'
$watchdogLoop=Join-Path $root 'recovery-watchdog-loop.ps1'
$exe=Join-Path $root 'anthares-remote-agent-v4.exe'
$lastGood=Join-Path $root 'anthares-remote-agent-v4.lastgood.exe'
$baseline=Join-Path $root 'integrity-baseline.json'
$credential=Join-Path $root 'secrets\issue-queue.json'
$log=Join-Path $root 'recovery-watchdog.log'
$state=Join-Path $root 'recovery-watchdog-state.json'
$restartStamp=Join-Path $root 'recovery-last-restart.txt'
$restartCooldownSeconds=120
$critical=@('run-agent-system-supervisor.ps1','load-issue-queue-auth.ps1','recovery-watchdog-loop.ps1')
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Add-Content -Path $log -Encoding UTF8}catch{}}
function Get-SystemV4{@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq 0 -and $_.Name -eq 'anthares-remote-agent-v4.exe'})}
function Get-InteractiveAgents{@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -ne 0 -and $_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'})}
function Restore-CriticalScripts{
  foreach($name in $critical){
    $live=Join-Path $root $name;$good=$live+'.lastgood'
    if(-not(Test-Path $good)){continue}
    $restore=$false
    if(-not(Test-Path $live)){$restore=$true}else{try{$restore=((Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $good -Algorithm SHA256).Hash)}catch{$restore=$true}}
    if($restore){try{Copy-Item -LiteralPath $good -Destination $live -Force;Log("restored critical script $name")}catch{Log("failed restoring critical script $name: $($_.Exception.Message)")}}
  }
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
    $task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  }
  return $task
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
function Test-QueueCredential{
  if(-not(Test-Path $credential)){return $false}
  try{
    Remove-Item Env:ANTHARES_GITHUB_QUEUE_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:ANTHARES_GITHUB_QUEUE_REPOSITORY -ErrorAction SilentlyContinue
    Remove-Item Env:ANTHARES_GITLAB_QUEUE_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:ANTHARES_GITLAB_QUEUE_PROJECT -ErrorAction SilentlyContinue
    . $queueLoader
    return (((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY))) -or ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT))))
  }catch{Log("queue credential load failed: $($_.Exception.GetType().Name)");return $false}
}
function Can-Restart{
  try{
    if(-not(Test-Path $restartStamp)){return $true}
    $raw=(Get-Content -LiteralPath $restartStamp -Raw -ErrorAction Stop).Trim()
    $last=[DateTimeOffset]::Parse($raw)
    return ((([DateTimeOffset]::UtcNow-$last).TotalSeconds) -ge $restartCooldownSeconds)
  }catch{return $true}
}
function Mark-Restart{try{[DateTimeOffset]::UtcNow.ToString('o')|Set-Content -LiteralPath $restartStamp -Encoding ASCII}catch{}}
try{
  Restore-CriticalScripts
  Ensure-BinaryIntegrity
  $task=Ensure-Task $canonicalTask $canonicalScript
  $wd=Ensure-Task $watchdogTask $watchdogLoop
  $queueCredentialPresent=Test-Path $credential
  $queueCredentialLoaded=Test-QueueCredential
  $githubQueue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))
  $gitlabQueue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))
  Get-InteractiveAgents|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue;Log("stopped interactive agent pid=$($_.ProcessId)")}catch{}}
  $agents=@(Get-SystemV4)
  $restartAttempted=$false
  if($agents.Count -eq 0){
    if($queueCredentialLoaded -and (Can-Restart)){
      $restartAttempted=$true;Mark-Restart
      Stop-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue
      Start-Sleep -Seconds 1
      Start-ScheduledTask -TaskName $canonicalTask -ErrorAction Stop
      Start-Sleep -Seconds 3
      $agents=@(Get-SystemV4)
    }elseif(-not $queueCredentialLoaded -and [string]$task.State -ne 'Running'){
      Start-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue
    }
  }
  $interactive=@(Get-InteractiveAgents)
  $reason=if($agents.Count -gt 0){'system-agent-running'}elseif(-not $queueCredentialLoaded){'waiting-for-private-queue-credential'}elseif(-not (Can-Restart)){'restart-cooldown'}else{'system-agent-missing'}
  [pscustomobject]@{
    updated_at=(Get-Date).ToUniversalTime().ToString('o');ok=$true;install_root=$root;role='canonical-root-recovery';reason=$reason
    canonical_task_present=[bool]$task;watchdog_task_present=[bool]$wd
    canonical_task_state=[string](Get-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue).State
    watchdog_task_state=[string](Get-ScheduledTask -TaskName $watchdogTask -ErrorAction SilentlyContinue).State
    queue_credential_present=[bool]$queueCredentialPresent;queue_credential_loaded=[bool]$queueCredentialLoaded
    github_queue=$githubQueue;gitlab_queue=$gitlabQueue;dual_queue_redundancy=($githubQueue -and $gitlabQueue)
    system_v4_count=$agents.Count;system_v4_pids=@($agents|ForEach-Object{$_.ProcessId})
    restart_cooldown_seconds=$restartCooldownSeconds;restart_attempted=$restartAttempted
    interactive_agent_count=$interactive.Count;interactive_agent_pids=@($interactive|ForEach-Object{$_.ProcessId})
    legacy_preserved_until_queue_proof=$true
  }|ConvertTo-Json -Depth 4|Set-Content $state -Encoding UTF8
}catch{
  Log("recovery failed: $($_.Exception.Message)")
  try{[pscustomobject]@{updated_at=(Get-Date).ToUniversalTime().ToString('o');ok=$false;error=$_.Exception.Message}|ConvertTo-Json|Set-Content $state -Encoding UTF8}catch{}
}
