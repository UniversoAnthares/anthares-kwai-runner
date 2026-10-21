[task:da5fb2173f2c] $ErrorActionPreference='Stop'
$root='D:\AntharsWork\AntharesRemote'
$log='D:\AntharsWork\quota-write-20261017\.state\kwai-physical-queue.log'
$ledger=Join-Path $root 'cortes-kwai-qa-alert-ledger.json'
$audit=Join-Path $root 'cortes-kwai-qa-alert-events.log'
try {
 $known=@{}
 if(Test-Path $ledger){$old=Get-Content $ledger -Raw -Encoding UTF8|ConvertFrom-Json;foreach($p in $old.PSObject.Properties){$known[$p.Name]=$true}}
 $ids=@(Get-Content $log -Tail 900 -Encoding UTF8|Where-Object {$_ -match 'JOB_FAILED\s+([^ ]+)'}|ForEach-Object {if($_ -match 'JOB_FAILED\s+([^ ]+)'){$matches[1]}}|Select-Object -Unique)
 # Independently monitor stalled publisher, intentional pauses and missing daemon.
 $extra=@()
 $kwaiRoot='D:\AntharsWork\quota-write-20261017'
 $pauseFile=Join-Path $kwaiRoot '.state\cortes-publisher-maintenance.pause'
 if((Test-Path $pauseFile) -and ((Get-Date)-(Get-Item $pauseFile).LastWriteTime).TotalMinutes -ge 15){
  $extra+=('KWAI_PAUSED_OVER_15_MIN_'+(Get-Date -Format 'yyyyMMdd'))
 }
 if((Test-Path $log) -and ((Get-Date)-(Get-Item $log).LastWriteTime).TotalMinutes -ge 6){
  $extra+=('KWAI_DAEMON_LOG_SILENT_'+(Get-Date -Format 'yyyyMMdd'))
 }
 $daemon=@(Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object {$_.CommandLine -like '*kwai_physical_queue_daemon.py daemon*'})
 if($daemon.Count -eq 0){
  $extra+=('KWAI_DAEMON_MISSING_'+(Get-Date -Format 'yyyyMMdd'))
  $task=Get-ScheduledTask -TaskName 'Anthares CORTES Kwai Physical Publisher' -ErrorAction SilentlyContinue
  if($task -and $task.State -ne 'Running'){
   try {Start-ScheduledTask -TaskName $task.TaskName; Add-Content $audit ((Get-Date -Format o)+' DAEMON_RESTART_REQUESTED')}
   catch {Add-Content $audit ((Get-Date -Format o)+' DAEMON_RESTART_FAILED')}
  }
 }
 $ids=@($ids)+@($extra)
 # Independent quota/drift QA: a real-world owner count supersedes incomplete CORTES logs.
 # Every incident is deduplicated by local day via the existing ledger.
 $today=Get-Date -Format 'yyyy-MM-dd'
 $floorPath='D:\AntharsWork\quota-write-20261017\.state\kwai-daily-cap-owner-confirmed.json'
 $floor=0
 if(Test-Path $floorPath){
  try {
   $doc=Get-Content $floorPath -Raw -Encoding UTF8|ConvertFrom-Json
   if($doc.schema -ne 'cortes.daily-owner-floor.v1'){throw 'invalid quota schema'}
   $acct=$doc.per_target_per_day.PSObject.Properties['kwai:lucasrosalem']
   if($null -ne $acct){
    $dayProperty=$acct.Value.PSObject.Properties[$today]
    if($null -ne $dayProperty){$floor=[int]$dayProperty.Value}
   }
  } catch {
   $ids+=('KWAI_QUOTA_OVERRIDE_CORRUPT_'+$today)
   Add-Content $audit ((Get-Date -Format o)+' QUOTA_OVERRIDE_CORRUPT')
  }
 }
 $pause='D:\AntharsWork\quota-write-20261017\.state\cortes-publisher-maintenance.pause'
 if((Test-Path $pause) -and (Get-Item $pause).LastWriteTime -lt (Get-Date).AddMinutes(-30)){
  $ids+=('KWAI_STALE_MAINTENANCE_PAUSE_'+$today)
  Add-Content $audit ((Get-Date -Format o)+' STALE_PAUSE_DETECTED')
 }
 if($floor -ge 100){
  try {
   . 'C:\ProgramData\AntharesRemoteAgent\agent-env.ps1'
   $env:CORTES_QUEUE_URL='https://anthares-remote-primary.vercel.app/api/cortes-queue'
   $python='C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe'
   $data=& $python -c "import sys,json;sys.path.insert(0,r'D:\AntharsWork\quota-write-20261017\tools');from cortes_neon_queue_client import call;r=call('stats',{'target_key':'kwai:lucasrosalem'});print(json.dumps({'ok':r.get('ok'),'confirmed_today':r.get('confirmed_today')}))"
   if($LASTEXITCODE -ne 0){throw 'quota stats unavailable'}
   $stats=$data|ConvertFrom-Json
   if($stats.ok -ne $true){throw 'quota stats error'}
   $confirmed=[int]$stats.confirmed_today
   if($floor -gt $confirmed){
    $ids+=('KWAI_REAL_POSTS_LEDGER_DRIFT_'+$today)
    Add-Content $audit ((Get-Date -Format o)+' QUOTA_DRIFT owner_floor='+$floor+' queue_confirmed='+$confirmed)
   }
  } catch {
   $ids+=('KWAI_QUOTA_AUDIT_UNAVAILABLE_'+$today)
   Add-Content $audit ((Get-Date -Format o)+' QUOTA_AUDIT_ERROR='+$_.Exception.GetType().Name)
  }
 }
 $new=@($ids|Where-Object {$_ -and !$known.ContainsKey($_)})
 if(!$new.Count){exit 0}
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if(!$token){throw 'QA_GITHUB_AUTH_UNAVAILABLE'}
 $headers=@{Authorization='Bearer '+$token;Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28';'User-Agent'='Anthares-Cortes-Kwai-P0-Watchdog'}
 $names=($new|Select-Object -First 20) -join ', '
 $body="**[QA P0][Kwai] Falhas de publicação detectadas pelo watchdog.** "+ "Analisar e corrigir imediatamente. O Android pode ter clicado Publicar; manter UNCERTAIN e reconciliar por evidência antes de republicar. "+ "Novos IDs: "+$names+". Horário: "+(Get-Date -Format o)+". Fonte: kwai-physical-queue.log. Teto diário 100."
 $payload=@{body=$body}|ConvertTo-Json -Compress
 Invoke-RestMethod -Uri 'https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments' -Headers $headers -Method POST -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 25|Out-Null
 foreach($id in $new){$known[$id]=$true}
 $stable=[ordered]@{}
 foreach($id in ($known.Keys|Sort-Object|Select-Object -Last 500)){$stable[$id]=$true}
 [IO.File]::WriteAllText($ledger,($stable|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
 Add-Content $audit ((Get-Date -Format o)+' P0_SENT new_ids='+$new.Count)
}catch{
 Add-Content $audit ((Get-Date -Format o)+' P0_NOTIFY_ERROR type='+$_.Exception.GetType().Name)
 exit 1
}