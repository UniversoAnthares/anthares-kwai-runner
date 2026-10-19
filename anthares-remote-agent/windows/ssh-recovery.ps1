# Invoked only by a forced-command SSH key. No arbitrary remote commands.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$request=[string]$env:SSH_ORIGINAL_COMMAND
if($request -notmatch '^(probe|observe|recover) ([A-Za-z0-9_-]{1,80})$'){throw 'unsupported SSH recovery request'}
$mode=$Matches[1];$requestId=$Matches[2]
$root='C:\ProgramData\AntharesRemoteSSHRecovery'
$agentRoot='C:\ProgramData\AntharesRemoteAgent'
Import-Module (Join-Path $root 'ssh-recovery-policy.psm1') -Force
$lock=New-Object Threading.Mutex($false,'Global\AntharesRemoteSSHRecoveryV1')
$held=$false;$transition=$null;$transitionHeld=$false
try{
  try{$held=$lock.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
  if(-not $held){throw 'recovery lock busy'}
  $processes=@(Get-CimInstance Win32_Process -Filter "Name='anthares-remote-agent-v4-c8.exe' OR Name='anthares-remote-agent-v4.exe'")
  $primary=@($processes|Where-Object {$_.Name -eq 'anthares-remote-agent-v4-c8.exe' -and $_.SessionId -eq 0})
  $reserve=@($processes|Where-Object {$_.Name -eq 'anthares-remote-agent-v4.exe'})
  # Preserve the disabled legacy watchdog. Wake only the enabled canonical
  # one-shot recovery task, whose IgnoreNew setting serializes all its callers.
  $task=Get-ScheduledTask -TaskName 'Anthares Remote Recovery'
  $principal=[string]$task.Principal.UserId
  $actions=@($task.Actions)
  $expected=Join-Path $agentRoot 'ara-recovery.ps1'
  $valid=($principal -match '^(SYSTEM|SISTEMA|S-1-5-18)$') -and ([string]$task.Principal.RunLevel -eq 'Highest') -and $task.Settings.Enabled -and ([string]$task.Settings.MultipleInstances -eq 'IgnoreNew') -and ($actions.Count -eq 1)
  $expectedArgs='-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File '+$expected
  if($valid){$valid=([string]$actions[0].Execute -ieq 'powershell.exe') -and ([string]$actions[0].Arguments -ceq $expectedArgs)}
  $pins=@{'ara-recovery.ps1'='7E7A4AF38DE022A31D1D3CD125A5428B5193FDB58059FFB5420AF418BDFCBD1B';'run-agent-system-supervisor.ps1'='84DCFBE8273C444D6531320D5975B3E6747A86DE719499A8A0D9E2BDA211B264'}
  foreach($name in $pins.Keys){
    if((Get-FileHash (Join-Path $agentRoot $name)).Hash -ne $pins[$name]){$valid=$false}
  }
  $supervisors=@(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'"|Where-Object {$_.CommandLine -match 'run-agent-system-supervisor\.ps1'})
  $statePath=Join-Path $root 'state.json';$state=$null
  if(Test-Path $statePath){$state=Get-Content $statePath -Raw|ConvertFrom-Json}
  $decision=Get-SSHRecoveryDecision -PrimaryCount $primary.Count -ReserveCount $reserve.Count -RecoveryOwnerActive (([string]$task.State -eq 'Running') -or $supervisors.Count -gt 0) -TasksValid $valid -Now ([datetimeoffset]::UtcNow) -State $state
  $performed=$false
  if($mode -eq 'recover' -and $decision.action -eq 'StartCanonicalRecovery'){
    $transition=New-Object Threading.Mutex($false,'Global\AntharesRemoteExecutionTransitionV1')
    try{$transitionHeld=$transition.WaitOne(0)}catch [Threading.AbandonedMutexException]{$transitionHeld=$true}
    if(-not $transitionHeld){throw 'canonical transition busy'}
    # Re-check immediately under the transition lock; never compete with an agent.
    $alive=@(Get-CimInstance Win32_Process -Filter "Name='anthares-remote-agent-v4-c8.exe' OR Name='anthares-remote-agent-v4.exe'")
    $freshTask=Get-ScheduledTask -TaskName $task.TaskName
    $freshSupervisors=@(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'"|Where-Object {$_.CommandLine -match 'run-agent-system-supervisor\.ps1'})
    if($alive.Count -eq 0 -and $freshSupervisors.Count -eq 0 -and [string]$freshTask.State -ne 'Running' -and $freshTask.Settings.Enabled){
      # Persist the cooldown before the side effect; crash/retry cannot duplicate it.
      $decision.last_action_utc=[datetimeoffset]::UtcNow.ToString('o')
      $decision|ConvertTo-Json|Set-Content ($statePath+'.tmp') -Encoding UTF8
      Move-Item -LiteralPath ($statePath+'.tmp') -Destination $statePath -Force
      Start-ScheduledTask -TaskName $task.TaskName
      $performed=$true
    }
  }
  if($mode -ne 'probe'){
    $decision|ConvertTo-Json|Set-Content ($statePath+'.tmp') -Encoding UTF8
    Move-Item -LiteralPath ($statePath+'.tmp') -Destination $statePath -Force
  }
  $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
  $admin=(New-Object Security.Principal.WindowsPrincipal($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  [pscustomobject]@{schema='anthares.ssh-recovery.v1';hostname=$env:COMPUTERNAME;identity=$identity.Name;administrator=$admin;request_id=$requestId;primary_count=$primary.Count;reserve_count=$reserve.Count;canonical_tasks_valid=$valid;decision=$decision.reason;action_performed=$performed;authority='canonical-local-recovery-task';mode=$mode}|ConvertTo-Json -Compress
}finally{
  if($transitionHeld){$transition.ReleaseMutex()};if($transition){$transition.Dispose()}
  if($held){$lock.ReleaseMutex()};$lock.Dispose()
}
