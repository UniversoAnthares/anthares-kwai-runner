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
  if($age -ge 20 -and @($gate.queued_ids).Count -gt 0 -and $gate.owner -eq 'local' -and [int]$gate.cloud_inflight -eq 0){
   $off=DevicePost 'deactivate-primary'
   if($off.ok){Log 'CLOUD_STALE_20MIN_SAFE_LOCAL_TAKEOVER'; & $node (Join-Path $root 'threads_cloud_local_gate.mjs')|Out-Null}
   else{Log 'TAKEOVER_DENIED_CLOUD_ACTIVE'}
  }else{
   & $node (Join-Path $root 'threads_cloud_local_gate.mjs')|Out-Null
   if($LASTEXITCODE -ne 20){throw 'CLOUD_PRIMARY_GATE_NOT_BLOCKING'}
   Log ('CLOUD_PRIMARY_HEALTHY age_minutes='+[math]::Round($age,1))
  }
 }else{
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
