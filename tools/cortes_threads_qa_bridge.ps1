param([switch]$DryRun)
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\cortes-social-browser-20261020'
$stateFile=Join-Path $root 'threads-continuity-state.json'
$notified=Join-Path $root 'threads-qa-notification-state.json'
$audit=Join-Path $root 'threads-qa-notification.log'
$gateway='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/?action=gate'
$issues=@()
$now=[DateTime]::UtcNow
$queued=0
try {
 if(Test-Path $stateFile){
  $state=Get-Content $stateFile -Raw -Encoding UTF8|ConvertFrom-Json
  $issues+=@($state.problems|Where-Object{$_}|ForEach-Object{[string]$_})
 }
}catch{$issues+='LOCAL_CONTINUITY_STATE_UNREADABLE'}
try {
 $gate=Invoke-RestMethod -Uri $gateway -TimeoutSec 14
 if($gate.ok -ne $true -or $null -eq $gate.cloud_primary_enabled){throw 'NEON_GATE_UNVERIFIED'}
 $queued=@($gate.queued_ids).Count
 if($queued -gt 0 -and $gate.cloud_primary_enabled -eq $false){$issues+='CLOUD_PRIMARY_DISABLED_WITH_QUEUE'}
 if($queued -gt 0 -and $gate.cloud_primary_enabled -eq $true){
  $stamp=if($gate.cloud_heartbeat_at){[DateTime]::Parse($gate.cloud_heartbeat_at).ToUniversalTime()}else{[DateTime]'2000-01-01T00:00:00Z'}
  if(($now-$stamp).TotalMinutes -gt 16){$issues+='CLOUD_PRIMARY_HEARTBEAT_STALE'}
 }
}catch{$issues+='NEON_GATE_UNAVAILABLE'}
# GitHub Actions itself may stay pending without a formal "failure" conclusion.
try {
 $u='https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/actions/runs?per_page=100'
 $runs=Invoke-RestMethod -Uri $u -Headers @{'User-Agent'='Anthares-CORTES-Threads-P0'} -TimeoutSec 16
 $stalled=@($runs.workflow_runs|Where-Object{
  $_.name -eq 'CORTES Threads Cloud Handoff (fenced)' -and
  $_.status -in @('queued','pending','waiting') -and
  ($now-[DateTime]::Parse($_.created_at).ToUniversalTime()).TotalMinutes -gt 12
 })
 if($stalled.Count -gt 0){$issues+='CLOUD_GITHUB_RUNNER_QUEUED_OVER_12MIN'}
}catch{
 if($queued -gt 0){$issues+='GITHUB_CLOUD_RUNNER_STATUS_UNAVAILABLE'}
}
$issues=@($issues|Where-Object{$_}|Sort-Object -Unique)
if($issues.Count -eq 0){exit 0}
$joined=$issues -join '|'
# Transient primary/standby heartbeat changes are one publisher-continuity incident.
# Keep original details in the comment; hash the stable operational family.
$families=@($issues|ForEach-Object{
 if($_ -match '^(CLOUD_PRIMARY_DISABLED_WITH_QUEUE|CLOUD_PRIMARY_HEARTBEAT_STALE|PUBLICATION_PROGRESS_STALLED|RECURRENT_PUBLICATION_ERRORS|SCHEDULER_NO_HEARTBEAT|CLOUD_GITHUB_RUNNER_QUEUED_OVER_12MIN)
$fingerprint=([BitConverter]::ToString($sha) -replace '-','').ToLowerInvariant().Substring(0,24)
$last=if(Test-Path $notified){try{Get-Content $notified -Raw -Encoding UTF8|ConvertFrom-Json}catch{$null}}else{$null}
if($last -and $last.fingerprint -eq $fingerprint -and
    ($now-[DateTime]::Parse($last.sent_at).ToUniversalTime()).TotalMinutes -lt 45){exit 0}
$body='[QA P0][Threads][CORTES] DIAGNOSTICO IMEDIATO. Falhas='+($issues -join ', ')+
 '. Fila pendente Neon='+$queued+'. Data UTC='+$now.ToString('o')+
 '. CONTINUIDADE: acionar/validar redundancia Windows pelo Neon; sem reenvio de cortes incertos.'+
 ' Investigar raiz, corrigir codigo e teste regressivo, reconfirmar publicacao cloud.'+
 ' Automacao de QA independendente do publicador; nao expor cookies ou tokens.'
if($DryRun){
 Write-Output ('THREADS_QA_P0_DRY_RUN problems='+$joined+' queued='+$queued)
 exit 0
}
try {
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if(!$token){throw 'QA_ISSUE_AUTH_UNAVAILABLE'}
 $headers=@{Authorization='Bearer '+$token;Accept='application/vnd.github+json';
  'X-GitHub-Api-Version'='2022-11-28';'User-Agent'='Anthares-Threads-QA-Watchdog'}
 $payload=@{body=$body}|ConvertTo-Json -Compress
 $result=Invoke-RestMethod -Uri 'https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments' -Headers $headers -Method POST -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 25
 if(!$result.id){throw 'QA_COMMENT_NOT_CONFIRMED'}
 $new=@{sent_at=$now.ToString('o');fingerprint=$fingerprint;severity='P0'}
 [IO.File]::WriteAllText($notified,($new|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
 [IO.File]::AppendAllText($audit,($now.ToString('o')+' NOTIFIED P0 '+$joined+[Environment]::NewLine))
}catch{
 [IO.File]::AppendAllText($audit,($now.ToString('o')+' ERROR '+$_.Exception.GetType().Name+[Environment]::NewLine))
 # Keep the incident durable when GitHub is down: independent P0 Incident Delivery
 # can retry later, and this task will keep retrying until the comment is acknowledged.
 $dir=Join-Path $root 'qa-incidents';New-Item -ItemType Directory -Path $dir -Force|Out-Null
 $file=Join-Path $dir ('threads-cloud-p0-'+$fingerprint+'.json')
 $case=@{priority='P0';project='CORTES';network='threads';fingerprint=$fingerprint;
  kind='CLOUD_CONTROLLER_OR_PUBLISHER_FAILURE';created_at=$now.ToString('o');
  problems=$issues;queued_count=$queued;requires_reconciliation=$true;automatic_republish_of_uncertain=$false}
 [IO.File]::WriteAllText($file,($case|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 exit 2
}
){
  'PUBLISHER_PROGRESS_IMPAIRED'
 }elseif($_ -match '^(GITHUB_CLOUD_RUNNER_STATUS_UNAVAILABLE|NEON_GATE_UNAVAILABLE|LOCAL_CONTINUITY_STATE_UNREADABLE)
$fingerprint=([BitConverter]::ToString($sha) -replace '-','').ToLowerInvariant().Substring(0,24)
$last=if(Test-Path $notified){try{Get-Content $notified -Raw -Encoding UTF8|ConvertFrom-Json}catch{$null}}else{$null}
if($last -and $last.fingerprint -eq $fingerprint -and
    ($now-[DateTime]::Parse($last.sent_at).ToUniversalTime()).TotalMinutes -lt 45){exit 0}
$body='[QA P0][Threads][CORTES] DIAGNOSTICO IMEDIATO. Falhas='+($issues -join ', ')+
 '. Fila pendente Neon='+$queued+'. Data UTC='+$now.ToString('o')+
 '. CONTINUIDADE: acionar/validar redundancia Windows pelo Neon; sem reenvio de cortes incertos.'+
 ' Investigar raiz, corrigir codigo e teste regressivo, reconfirmar publicacao cloud.'+
 ' Automacao de QA independendente do publicador; nao expor cookies ou tokens.'
if($DryRun){
 Write-Output ('THREADS_QA_P0_DRY_RUN problems='+$joined+' queued='+$queued)
 exit 0
}
try {
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if(!$token){throw 'QA_ISSUE_AUTH_UNAVAILABLE'}
 $headers=@{Authorization='Bearer '+$token;Accept='application/vnd.github+json';
  'X-GitHub-Api-Version'='2022-11-28';'User-Agent'='Anthares-Threads-QA-Watchdog'}
 $payload=@{body=$body}|ConvertTo-Json -Compress
 $result=Invoke-RestMethod -Uri 'https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments' -Headers $headers -Method POST -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 25
 if(!$result.id){throw 'QA_COMMENT_NOT_CONFIRMED'}
 $new=@{sent_at=$now.ToString('o');fingerprint=$fingerprint;severity='P0'}
 [IO.File]::WriteAllText($notified,($new|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
 [IO.File]::AppendAllText($audit,($now.ToString('o')+' NOTIFIED P0 '+$joined+[Environment]::NewLine))
}catch{
 [IO.File]::AppendAllText($audit,($now.ToString('o')+' ERROR '+$_.Exception.GetType().Name+[Environment]::NewLine))
 # Keep the incident durable when GitHub is down: independent P0 Incident Delivery
 # can retry later, and this task will keep retrying until the comment is acknowledged.
 $dir=Join-Path $root 'qa-incidents';New-Item -ItemType Directory -Path $dir -Force|Out-Null
 $file=Join-Path $dir ('threads-cloud-p0-'+$fingerprint+'.json')
 $case=@{priority='P0';project='CORTES';network='threads';fingerprint=$fingerprint;
  kind='CLOUD_CONTROLLER_OR_PUBLISHER_FAILURE';created_at=$now.ToString('o');
  problems=$issues;queued_count=$queued;requires_reconciliation=$true;automatic_republish_of_uncertain=$false}
 [IO.File]::WriteAllText($file,($case|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 exit 2
}
){
  'CONTROL_PLANE_VISIBILITY_LOST'
 }else{$_}
}|Sort-Object -Unique)
$familyKey=$families -join '|'
$sha=[Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($familyKey))
$fingerprint=([BitConverter]::ToString($sha) -replace '-','').ToLowerInvariant().Substring(0,24)
$last=if(Test-Path $notified){try{Get-Content $notified -Raw -Encoding UTF8|ConvertFrom-Json}catch{$null}}else{$null}
if($last -and $last.fingerprint -eq $fingerprint -and
    ($now-[DateTime]::Parse($last.sent_at).ToUniversalTime()).TotalMinutes -lt 45){exit 0}
$body='[QA P0][Threads][CORTES] DIAGNOSTICO IMEDIATO. Falhas='+($issues -join ', ')+
 '. Fila pendente Neon='+$queued+'. Data UTC='+$now.ToString('o')+
 '. CONTINUIDADE: acionar/validar redundancia Windows pelo Neon; sem reenvio de cortes incertos.'+
 ' Investigar raiz, corrigir codigo e teste regressivo, reconfirmar publicacao cloud.'+
 ' Automacao de QA independendente do publicador; nao expor cookies ou tokens.'
if($DryRun){
 Write-Output ('THREADS_QA_P0_DRY_RUN problems='+$joined+' queued='+$queued)
 exit 0
}
try {
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if(!$token){throw 'QA_ISSUE_AUTH_UNAVAILABLE'}
 $headers=@{Authorization='Bearer '+$token;Accept='application/vnd.github+json';
  'X-GitHub-Api-Version'='2022-11-28';'User-Agent'='Anthares-Threads-QA-Watchdog'}
 $payload=@{body=$body}|ConvertTo-Json -Compress
 $result=Invoke-RestMethod -Uri 'https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments' -Headers $headers -Method POST -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 25
 if(!$result.id){throw 'QA_COMMENT_NOT_CONFIRMED'}
 $new=@{sent_at=$now.ToString('o');fingerprint=$fingerprint;severity='P0'}
 [IO.File]::WriteAllText($notified,($new|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
 [IO.File]::AppendAllText($audit,($now.ToString('o')+' NOTIFIED P0 '+$joined+[Environment]::NewLine))
}catch{
 [IO.File]::AppendAllText($audit,($now.ToString('o')+' ERROR '+$_.Exception.GetType().Name+[Environment]::NewLine))
 # Keep the incident durable when GitHub is down: independent P0 Incident Delivery
 # can retry later, and this task will keep retrying until the comment is acknowledged.
 $dir=Join-Path $root 'qa-incidents';New-Item -ItemType Directory -Path $dir -Force|Out-Null
 $file=Join-Path $dir ('threads-cloud-p0-'+$fingerprint+'.json')
 $case=@{priority='P0';project='CORTES';network='threads';fingerprint=$fingerprint;
  kind='CLOUD_CONTROLLER_OR_PUBLISHER_FAILURE';created_at=$now.ToString('o');
  problems=$issues;queued_count=$queued;requires_reconciliation=$true;automatic_republish_of_uncertain=$false}
 [IO.File]::WriteAllText($file,($case|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 exit 2
}
