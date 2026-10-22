param([switch]$CheckOnly)
$ErrorActionPreference='Stop'
$repo='UniversoAnthares/anthares-clipper'
$workflow='cortes-daily.yml'
$log='D:\AntharsWork\AntharesRemote\cortes-0600-local-safety.log'
$markerRoot='D:\AntharsWork\AntharesRemote\cortes-daily-dispatch-state'
$now=[DateTimeOffset]::Now
$start=[DateTimeOffset]::new($now.Year,$now.Month,$now.Day,6,0,0,$now.Offset)
if(-not $CheckOnly -and ($now -lt $start -or $now -ge $start.AddHours(16))){exit 0}
function Status([string]$msg){
 $line=([DateTimeOffset]::Now.ToString('o')+' '+$msg)
 Add-Content -LiteralPath $log -Value $line -Encoding UTF8
 Write-Output $line
}
$dispatchLock=[System.Threading.Mutex]::new($false,'Local\AntharesCortesSharedOrchestratorDispatch20261022')
$hasDispatchLock=$false
try{
 $hasDispatchLock=$dispatchLock.WaitOne(0)
 if(-not $hasDispatchLock){Status 'SKIP second_local_controller_instance';exit 0}
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if([string]::IsNullOrWhiteSpace($token)){throw 'NO_PROTECTED_GITHUB_TOKEN'}
 $headers=@{
  'Authorization'='Bearer '+$token
  'Accept'='application/vnd.github+json'
  'User-Agent'='Anthares-Cortes-0600-LocalSafety'
  'X-GitHub-Api-Version'='2022-11-28'
 }
 $url="https://api.github.com/repos/$repo/actions/workflows/$workflow/runs?per_page=75"
 $data=Invoke-RestMethod -Uri $url -Headers $headers -TimeoutSec 28
 $resumeUrl="https://api.github.com/repos/$repo/actions/workflows/cortes-short-resume.yml/runs?per_page=75"
 $resumeData=Invoke-RestMethod -Uri $resumeUrl -Headers $headers -TimeoutSec 28
 $sharedActive=@($data.workflow_runs | Where-Object {$_.status -in @('queued','in_progress','waiting','pending','requested')})
 $sharedActive+=@($resumeData.workflow_runs | Where-Object {$_.status -in @('queued','in_progress','waiting','pending','requested')})
 if($sharedActive.Count -gt 0){
  Status ("SKIP shared_orchestrator_busy active="+$sharedActive.Count)
  exit 0
 }
 $today=@($data.workflow_runs | Where-Object {
   $_.name -eq 'CORTES diario' -and $_.created_at -and
   ([DateTimeOffset]::Parse([string]$_.created_at).ToUniversalTime() -ge $start.ToUniversalTime())
 })
 $active=@($today | Where-Object {$_.status -in @('queued','in_progress','waiting','pending','requested')})
 $success=@($today | Where-Object {$_.conclusion -eq 'success'})
 $failed=@($today | Where-Object {$_.conclusion -in @('failure','cancelled','timed_out')})
 if($CheckOnly){Status "CHECK_ONLY access=OK runs_today=$($today.Count) active=$($active.Count) success=$($success.Count) failed=$($failed.Count)";exit 0}
 if($active.Count -gt 0){Status "SKIP active_daily_run count=$($active.Count)";exit 0}
 if($success.Count -gt 0){
 $ledger='D:\AntharsWork\anthares-clipper\runner-media\state\cortes-short-ledger.json'
 $day=$now.ToString('yyyy-MM-dd')
 $currentDayGenerated=$false
 if(Test-Path $ledger){
  try{
   $state=Get-Content -Raw -LiteralPath $ledger -Encoding UTF8|ConvertFrom-Json
   foreach($source in $state.sources.PSObject.Properties){
    if([string]$source.Value.schedule_date -eq $day -and $source.Value.analysis_completed_at){$currentDayGenerated=$true;break}
   }
  }catch{Status 'ALERT daily_ledger_unreadable'}
 }
 if($currentDayGenerated){Status "SKIP current_day_source_completed success=$($success.Count)";exit 0}
 if($success.Count -ge 6){Status 'ALERT repeated_success_without_today_source QA_required';exit 1}
 Status "RESUME next_chronological_source_previous_legacy_completed successes=$($success.Count)"
}
 if($failed.Count -ge 2){Status "ALERT daily_failed_twice count=$($failed.Count) recovery_still_enabled"}
 New-Item -ItemType Directory -Path $markerRoot -Force | Out-Null
 $marker=Join-Path $markerRoot ($now.ToString('yyyyMMdd')+'.ack')
 if(Test-Path $marker){
 $previous=[DateTimeOffset]::MinValue
 [DateTimeOffset]::TryParse([string](Get-Content -LiteralPath $marker -Raw),[ref]$previous)|Out-Null
 if($previous -gt $now.AddMinutes(-25)){Status 'SKIP dispatched_recently_cooldown_25min';exit 0}
 Status "RETRY after_previous_dispatch_not_confirmed marker_age_min=$([math]::Round(($now-$previous).TotalMinutes))"
}
 $body='{"ref":"main"}'
 $response=Invoke-WebRequest -Uri "https://api.github.com/repos/$repo/actions/workflows/$workflow/dispatches" -Method POST -Headers $headers -ContentType 'application/json' -Body $body -UseBasicParsing -TimeoutSec 35
 if([int]$response.StatusCode -ne 204){throw ('DISPATCH_UNEXPECTED_HTTP_'+[int]$response.StatusCode)}
 [IO.File]::WriteAllText($marker,$now.ToString('o'),[Text.UTF8Encoding]::new($false))
 Status 'DISPATCH_ACCEPTED_NOT_CONFIRMED workflow=cortes-daily.yml ref=main'
 exit 0
}catch{
 $code=0
 if($_.Exception.Response){$code=[int]$_.Exception.Response.StatusCode}
 Status ('ERROR type='+$_.Exception.GetType().Name+' http='+$code)
 exit 2
}finally{
 if($hasDispatchLock){[void]$dispatchLock.ReleaseMutex()}
 $dispatchLock.Dispose()
 Remove-Item Env:\ANTHARES_GITHUB_QUEUE_TOKEN -ErrorAction SilentlyContinue
}
