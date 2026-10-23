$ErrorActionPreference='Stop'
$log='D:\AntharsWork\AntharesRemote\cortes-kwai-refill-fallback.log'
try {
  # Guard: no queue-refill while physical Kwai publisher is paused for reconciliation.
  $pause='D:\AntharsWork\quota-write-20261017\.state\cortes-publisher-maintenance.pause'
  if(Test-Path -LiteralPath $pause){
    Add-Content -Path $log -Value ((Get-Date -Format o)+' REFILL_SKIP_PUBLISHER_MAINTENANCE')
    exit 0
  }
  # A dated owner-attested Kwai total is authoritative when CORTES stats lag.
  $floorPath='D:\AntharsWork\quota-write-20261017\.state\kwai-daily-cap-owner-confirmed.json'
  if(Test-Path $floorPath){
    try {
      $doc=Get-Content $floorPath -Raw -Encoding UTF8|ConvertFrom-Json
      if($doc.schema -ne 'cortes.daily-owner-floor.v1'){throw 'INVALID_OWNER_CAP_SCHEMA'}
      $item=$doc.per_target_per_day.PSObject.Properties['kwai:lucasrosalem']
      $day=(Get-Date).ToString('yyyy-MM-dd')
      $count=0
      if($null -ne $item) {
        $d=$item.Value.PSObject.Properties[$day]
        if($null -ne $d){$count=[int]$d.Value}
      }
      if($count -ge 100) {
        Add-Content $log ((Get-Date -Format o)+' REFILL_SKIP_DAILY_CAP day='+$day+' floor='+$count)
        exit 0
      }
    } catch {
      Add-Content $log ((Get-Date -Format o)+' REFILL_SKIP_CAP_UNREADABLE')
      exit 0
    }
  }
  $now=Get-Date
  if($now.Hour -lt 6 -or $now.Hour -ge 23){exit 0}
  . 'C:\ProgramData\AntharesRemoteAgent\agent-env.ps1'
  $h=@{Authorization='Bearer '+$env:ANTHARES_DEVICE_TOKEN;'X-Anthares-Device'='DESKTOP-FTDK0HP';'Content-Type'='application/json'}
  $stats=Invoke-RestMethod 'https://anthares-remote-primary.vercel.app/api/cortes-queue?action=stats' -Method POST -Headers $h -Body '{"target_key":"kwai:lucasrosalem"}' -TimeoutSec 16
  if(!$stats.ok){throw 'NEON_STATS_INVALID'}
  if([int]$stats.confirmed_today -ge 100 -or [int]$stats.pending -ge 4){exit 0}
  . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
  $gh=@{Authorization='Bearer '+$env:ANTHARES_GITHUB_QUEUE_TOKEN;Accept='application/vnd.github+json';'User-Agent'='Anthares-Kwai-Queue-Fallback'}
  $url='https://api.github.com/repos/UniversoAnthares/anthares-clipper/actions/workflows/cortes-kwai-dispatch-refill.yml'
  $runs=Invoke-RestMethod ($url+'/runs?per_page=6') -Headers $gh -TimeoutSec 18
  if(@($runs.workflow_runs|Where-Object status -in 'queued','in_progress','waiting','pending').Count -gt 0){exit 0}
  $response=Invoke-WebRequest ($url+'/dispatches') -Headers $gh -Method POST -ContentType 'application/json' -Body '{"ref":"main"}' -UseBasicParsing -TimeoutSec 19
  if([int]$response.StatusCode -ne 204){throw 'DISPATCH_UNACKNOWLEDGED'}
  Add-Content $log ((Get-Date -Format o)+' REFILL_ACK pending='+$stats.pending+' posted='+$stats.confirmed_today)
}catch {
  Add-Content $log ((Get-Date -Format o)+' REFILL_ERROR type='+$_.Exception.GetType().Name)
  exit 1
}