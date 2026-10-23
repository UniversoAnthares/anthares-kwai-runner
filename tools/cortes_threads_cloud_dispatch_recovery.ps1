param([switch]$SelfTest,[switch]$DryRun)
# Existing Windows steward invokes this helper; no new scheduler is created.
# GitHub action schedules can be delayed. A single safe dispatch restores cloud
# progress without using logged-out browser sessions or reproducing submissions.
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\cortes-social-browser-20261020'
$gateUrl='https://br-crimson-unit-b89nau08-cortesthreadspub.compute.c-14.us-east-1.aws.neon.tech/?action=gate'
$workflow='https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/actions/workflows/cortes-threads-cloud-handoff.yml'
$mark=Join-Path $root 'threads-cloud-dispatch-recovery.json'
function MinutesOld($when,$now) {
 if([string]::IsNullOrWhiteSpace([string]$when)){return 999999}
 try{return [math]::Max(0,($now-[DateTime]::Parse([string]$when).ToUniversalTime()).TotalMinutes)}
 catch{return 999999}
}
function NeedsCloudRecovery($gate,$now) {
 if(!$gate -or $gate.ok -ne $true -or $gate.cloud_primary_enabled -ne $true){return $false}
 if(@($gate.queued_ids).Count -eq 0 -or [int]$gate.cloud_inflight -ne 0){return $false}
 return ((MinutesOld $gate.cloud_last_success_at $now) -ge 14 -and
         (MinutesOld $gate.cloud_heartbeat_at $now) -ge 8)
}
if($SelfTest){
 $now=[DateTime]::UtcNow
 $old=$now.AddMinutes(-35).ToString('o')
 $recent=$now.AddMinutes(-2).ToString('o')
 $base=[pscustomobject]@{ok=$true;cloud_primary_enabled=$true;cloud_inflight=0;queued_ids=@('test');cloud_last_success_at=$old;cloud_heartbeat_at=$old}
 if(!(NeedsCloudRecovery $base $now)){throw 'QA_RECOVERY_SHOULD_DISPATCH'}
 $base.cloud_heartbeat_at=$recent
 if(NeedsCloudRecovery $base $now){throw 'QA_RECOVERY_HEARTBEAT_FALSE_POSITIVE'}
 $base.cloud_heartbeat_at=$old
 $base.cloud_inflight=1
 if(NeedsCloudRecovery $base $now){throw 'QA_RECOVERY_INFLIGHT_FALSE_POSITIVE'}
 $base.cloud_inflight=0
 $base.queued_ids=@()
 if(NeedsCloudRecovery $base $now){throw 'QA_RECOVERY_EMPTY_FALSE_POSITIVE'}
 Write-Output 'THREADS_RECOVERY_SELFTEST_PASS=4'
 return
}
try{
 $now=[DateTime]::UtcNow
 $gate=Invoke-RestMethod -Uri $gateUrl -TimeoutSec 16
 if(!(NeedsCloudRecovery $gate $now)){Write-Output 'CLOUD_RECOVERY_UNNECESSARY';return}
 if(Test-Path $mark){
  try{
   $previous=Get-Content $mark -Raw -Encoding UTF8|ConvertFrom-Json
   if((MinutesOld $previous.accepted_at $now) -lt 19){Write-Output 'CLOUD_RECOVERY_RECENT_ACK';return}
  }catch{}
 }
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if([string]::IsNullOrWhiteSpace($token)){throw 'RECOVERY_AUTH_NOT_CONFIGURED'}
 $headers=@{Authorization='Bearer '+$token;Accept='application/vnd.github+json';
    'X-GitHub-Api-Version'='2022-11-28';'User-Agent'='Anthares-Threads-Recovery'}
 $runs=Invoke-RestMethod -Uri ($workflow+'/runs?per_page=15') -Headers $headers -TimeoutSec 15
 $active=@($runs.workflow_runs|Where-Object{$_.status -in @('queued','pending','waiting','in_progress','requested')})
 if($active.Count -gt 0){Write-Output 'CLOUD_RECOVERY_ACTIVE_RUN';return}
 if($DryRun){Write-Output 'CLOUD_RECOVERY_DRYRUN_ELIGIBLE';return}
 $data=@{ref='main';inputs=@{publish='true';batch='false'}}|ConvertTo-Json -Compress -Depth 4
 $request=Invoke-WebRequest -Uri ($workflow+'/dispatches') -Method Post -Headers $headers -ContentType 'application/json' -Body $data -TimeoutSec 20
 if([int]$request.StatusCode -ne 204){throw 'RECOVERY_DISPATCH_NOT_ACCEPTED'}
 $snapshot=@{schema='anthares.threads.dispatch-recovery.v1';accepted_at=$now.ToString('o');queue_count=@($gate.queued_ids).Count;result='DISPATCH_ACK_ONLY'}
 $tmp=$mark+'.tmp'
 [IO.File]::WriteAllText($tmp,($snapshot|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
 Move-Item -LiteralPath $tmp -Destination $mark -Force
 Write-Output 'CLOUD_RECOVERY_DISPATCH_ACCEPTED'
}catch{
 # The steward keeps independent Neon failover. No secrets or response bodies in logs.
 Write-Output ('CLOUD_RECOVERY_FAILED_'+$_.Exception.GetType().Name)
}
