$ErrorActionPreference='Stop'
$root='D:\AntharsWork\cortes-social-browser-20261020'
$task='Anthares CORTES Threads Browser Publisher'
$marker=Join-Path $root 'threads-cloud-handoff-armed.json'
$log=Join-Path $root 'threads-cloud-primary-steward.log'
$node='C:\Program Files\nodejs\node.exe'
$api='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/'
function Log([string]$s){[IO.File]::AppendAllText($log,((Get-Date).ToUniversalTime().ToString('o')+' '+$s+[Environment]::NewLine),(New-Object Text.UTF8Encoding($false)))}
function ReadGate(){return Invoke-RestMethod -Uri ($api+'?action=gate') -TimeoutSec 16}
function DevicePost([string]$action){
 . 'D:\AntharsWork\AntharesRemoteAgent\agent-env.ps1'
 if([string]::IsNullOrEmpty($env:ANTHARES_DEVICE_TOKEN)){throw 'DEVICE_TOKEN_NOT_AVAILABLE'}
 return Invoke-RestMethod -Uri ($api+'?action=control') -Method POST -Headers @{
 'Authorization'='Bearer '+$env:ANTHARES_DEVICE_TOKEN;
 'X-Anthares-Device'='DESKTOP-FTDK0HP'
 } -ContentType 'application/json' -Body ('{"action":"'+$action+'"}') -TimeoutSec 18
}
try{
 $gate=ReadGate
 if($gate.ok -ne $true){throw 'NEON_GATE_BAD'}
 if($gate.cloud_primary_enabled -eq $true){
  # The local publisher is HOT STANDBY, but the node gate always blocks it.
  if(!(Test-Path $marker)){
   $content=@{enabled=$true;epoch_at_arm=[long]$gate.epoch;expires_at=[DateTime]::UtcNow.AddDays(2).ToString('o');reason='cloud-primary-steward'}|ConvertTo-Json -Compress
   [IO.File]::WriteAllText($marker,$content,(New-Object Text.UTF8Encoding($false)))
  }
  if((Get-ScheduledTask -TaskName $task).State -eq 'Disabled'){Enable-ScheduledTask -TaskName $task|Out-Null}
  $heartbeat=if($gate.cloud_heartbeat_at){[DateTime]::Parse($gate.cloud_heartbeat_at).ToUniversalTime()}else{[DateTime]::MinValue}
  $age=([DateTime]::UtcNow-$heartbeat).TotalMinutes
   # Restore cloud dispatch when scheduled GitHub runs are delayed.
   $dispatchResult=@(& (Join-Path $root 'threads-cloud-dispatch-recovery.ps1'))
   if($dispatchResult -contains 'CLOUD_RECOVERY_DISPATCH_ACCEPTED' -or
      $dispatchResult -contains 'CLOUD_RECOVERY_ACTIVE_RUN' -or
      $dispatchResult -contains 'CLOUD_RECOVERY_RECENT_ACK'){
    Log ('CLOUD_RECOVERY_BACKSTOP '+($dispatchResult -join ','))
    exit 0
   }
  if($age -ge 20 -and $gate.owner -eq 'local' -and [int]$gate.cloud_inflight -eq 0){
   $off=DevicePost 'deactivate-primary'
   if($off.ok){Log 'CLOUD_STALE_20MIN_SAFE_LOCAL_TAKEOVER'; & $node (Join-Path $root 'threads_cloud_local_gate.mjs')|Out-Null}
   else{Log 'TAKEOVER_DENIED_CLOUD_ACTIVE'}
  }else{
   & $node (Join-Path $root 'threads_cloud_local_gate.mjs')|Out-Null
   if($LASTEXITCODE -ne 20){throw 'CLOUD_PRIMARY_GATE_NOT_BLOCKING'}
   Log ('CLOUD_PRIMARY_HEALTHY age_minutes='+[math]::Round($age,1))
  }
 }else{
  # Live auth gate for the original owned AntharesMeta profile.
  # The probe is read-only; no login, cookies or personal interaction.
  $authProbe=Join-Path $root 'threads-auth-circuit.mjs'
  if(!(Test-Path -LiteralPath $authProbe)){throw 'THREADS_AUTH_CIRCUIT_MISSING'}
  $authLines=@(& $node $authProbe 2>&1)
  $authExit=$LASTEXITCODE
  if($authExit -eq 20){
   $pubTask=Get-ScheduledTask -TaskName $task -ErrorAction Stop
   if($pubTask.State -ne 'Disabled'){Disable-ScheduledTask -TaskName $task -ErrorAction Stop|Out-Null}
   Log 'LOCAL_BROWSER_DISABLED_NO_AUTHENTICATED_OWNER_SESSION'
   exit 0
  }
  if($authExit -ne 0){throw ('THREADS_AUTH_CIRCUIT_ERROR_'+$authExit)}

  # Pause the local publisher when interactive authentication is blocked.
  # Keep cloud activation under its independent gate and preserve the queue.
  $continuity=Join-Path $root 'threads-continuity-state.json'
  if(Test-Path -LiteralPath $continuity){
   $currentState=Get-Content -LiteralPath $continuity -Raw|ConvertFrom-Json
   if($currentState.auth_backoff -and $currentState.auth_backoff.blocked -eq $true){
    $pubTask=Get-ScheduledTask -TaskName $task -ErrorAction Stop
    if($pubTask.State -ne 'Disabled'){
     Disable-ScheduledTask -TaskName $task -ErrorAction Stop|Out-Null
    }
    Log ('LOCAL_PUBLISHER_PAUSED_AUTH_BACKOFF pending='+[int]$currentState.pending_count)
    exit 0
   }
  }
  # If the automation-only local profile has lost Threads authentication,
  # safely pause it and restore the last working cloud primary instead of
  # repeatedly attempting a logged-out browser session.
  $authFailed=$false
  try {
   $cutoff=[DateTime]::UtcNow.AddHours(-8)
   foreach($line in @(Get-Content (Join-Path $root 'threads-scheduler.log') -Tail 160 -ErrorAction Stop)) {
    if($line -match 'THREADS_NOT_AUTHENTICATED_OR_WRONG_PROFILE' -and $line -match '^(\d{4}-\d{2}-\d{2}T[0-9:.]+Z)') {
     $seen=[DateTime]::Parse($matches[1]).ToUniversalTime()
     if($seen -ge $cutoff){$authFailed=$true;break}
    }
   }
  }catch{}
  if($authFailed) {
   $lastCloud=if($gate.cloud_last_success_at){[DateTime]::Parse($gate.cloud_last_success_at).ToUniversalTime()}else{[DateTime]::MinValue}
   if(([DateTime]::UtcNow-$lastCloud).TotalHours -lt 48) {
     Disable-ScheduledTask -TaskName $task|Out-Null
     try {
      # Drain the active local worker after disabling new acquisitions.
      $idle=$false
      for($attempt=0;$attempt -lt 24;$attempt++){
       $running=(Get-ScheduledTask -TaskName $task).State -eq 'Running'
       $workerLock=Test-Path (Join-Path $root 'threads-worker.lock')
       $liveNode=@(Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'publish-threads-once'})
       if(-not $running -and -not $workerLock -and $liveNode.Count -eq 0){$idle=$true;break}
       Start-Sleep -Seconds 2
      }
      if(-not $idle){Log 'LOCAL_AUTH_INVALID_WAIT_FOR_IDLE';exit 0}
     $ack=DevicePost 'ack-pause'
     if($ack.ok -ne $true){throw 'LOCAL_PAUSE_ACK_DENIED'}
     $on=DevicePost 'activate-primary'
     if($on.ok -ne $true){throw 'CLOUD_REACTIVATION_DENIED'}
     Log 'LOCAL_AUTH_INVALID_SAFE_CLOUD_REACTIVATION'
     exit 0
    }finally {
     Enable-ScheduledTask -TaskName $task|Out-Null
    }
   }
  }
  & $node (Join-Path $root 'threads_cloud_local_gate.mjs')|Out-Null
  if($LASTEXITCODE -eq 0){
   if((Get-ScheduledTask -TaskName $task).State -eq 'Disabled'){Enable-ScheduledTask -TaskName $task|Out-Null}
   Log 'LOCAL_FALLBACK_ACTIVE'
  }else{Log 'LOCAL_WAITING_FOR_CLOUD_OR_RECONCILIATION'}
 }
}catch{
 Log ('STEWARD_ERROR '+$_.Exception.GetType().Name+' '+[string]$_.Exception.Message.Substring(0,[Math]::Min($_.Exception.Message.Length,95)))
 exit 2
}

