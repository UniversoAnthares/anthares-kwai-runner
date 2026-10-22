# Codeberg TikTok primary: resilient Windows fallback with Neon identity fencing.
# Runs as a hidden scheduled task every five minutes. No TikTok browser is
# started here; only the approved self-hosted GitHub OIDC workflow can publish.
$ErrorActionPreference='Stop'
$repo='UniversoAnthares/anthares-kwai-runner'
$root=Join-Path $env:LOCALAPPDATA 'Anthares\TikTok'
New-Item -Path $root -ItemType Directory -Force|Out-Null
$stateFile=Join-Path $root 'codeberg-failover-state.json'
$logFile=Join-Path $root 'codeberg-failover.log'
$mutex=New-Object System.Threading.Mutex($false,'Local\AntharesTikTokCodebergFallback')
$held=$false
function Log([string]$message) {
 Add-Content -Path $logFile -Encoding UTF8 -Value ((Get-Date).ToUniversalTime().ToString('o')+' '+$message)
}
try {
 try {$held=$mutex.WaitOne(0)}catch [System.Threading.AbandonedMutexException] {$held=$true}
 if(-not $held){exit 0}
 $arm=(& gh variable get TIKTOK_CODEBERG_PRIMARY -R $repo 2>$null|Out-String).Trim()
 if($LASTEXITCODE -ne 0){Log 'QA_P0_GH_ARM_STATE_UNAVAILABLE';exit 2}
 if($arm -ne 'true'){Log 'STANDBY_CODEBERG_NOT_PRIMARY';exit 0}
 $now=[DateTimeOffset]::UtcNow
 $state=@{}
 if(Test-Path $stateFile) {
  try{$old=Get-Content $stateFile -Raw|ConvertFrom-Json;foreach($p in $old.PSObject.Properties){$state[$p.Name]=$p.Value}}
  catch{Log 'STATE_INVALID_RECOVERING'}
 }
 $data=$null
 try {
  $data=Invoke-RestMethod 'https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner/actions/runs?limit=80' -TimeoutSec 16
 } catch {Log ('QA_P0_CODEBERG_HEALTH_UNAVAILABLE='+$_.Exception.GetType().Name)}
 $targets=@(
  @{account='universo';workflow='cortes-tiktok-universo-codeberg.yml';backup='cortes-tiktok-primary-windows-fallback.yml'},
  @{account='lucas4';workflow='cortes-tiktok-lucas4-codeberg.yml';backup='cortes-tiktok-lucasrosalem4-windows-fallback.yml'}
 )
 foreach($target in $targets) {
  $key=$target.account
  $newest=$null
  if($data -and $data.workflow_runs) {
   $matches=@($data.workflow_runs|Where-Object {$_.workflow_id -eq $target.workflow -and $_.status -eq 'success'})
   foreach($item in $matches) {
    try {
     $stamp=[DateTimeOffset]::Parse([string]$item.updated,[Globalization.CultureInfo]::InvariantCulture)
     if(-not $newest -or $stamp -gt $newest){$newest=$stamp}
    } catch {continue}
   }
  }
  if($newest){$state[$key+'LastSuccess']=$newest.ToString('o')}
  $last=$null
  if($state.ContainsKey($key+'LastSuccess')) {
   try{$last=[DateTimeOffset]::Parse([string]$state[$key+'LastSuccess'])}catch{}
  }
  if(-not $last) {$state[$key+'LastSuccess']=$now.ToString('o');Log ('GRACE_FIRST_OBSERVATION='+$key);continue}
  $age=($now-$last).TotalMinutes
  if($age -lt 20){Log ($key+'_CODEBERG_HEALTHY age_minutes='+[int]$age);continue}
  $recentDispatch=$null
  if($state.ContainsKey($key+'LastDispatch')) {
   try{$recentDispatch=[DateTimeOffset]::Parse([string]$state[$key+'LastDispatch'])}catch{}
  }
  if($recentDispatch -and ($now-$recentDispatch).TotalMinutes -lt 6){Log ($key+'_FAILOVER_COOLDOWN');continue}
  $runsJson=& gh run list -R $repo --workflow $target.backup --limit 8 --json databaseId,status,createdAt 2>$null
  if($LASTEXITCODE -ne 0){Log ($key+'_FAILOVER_RUN_STATUS_UNAVAILABLE');continue}
  $runs=@($runsJson|ConvertFrom-Json)
  $active=@($runs|Where-Object {$_.status -in @('queued','pending','in_progress','waiting')})
  if($active.Count -gt 0){Log ($key+'_FAILOVER_ALREADY_ACTIVE');continue}
  & gh workflow run $target.backup -R $repo --ref main -f proof_publish_one=true 2>$null|Out-Null
  if($LASTEXITCODE -eq 0) {
   $state[$key+'LastDispatch']=$now.ToString('o')
   Log ('QA_P0_CODEBERG_PRIMARY_DOWN_WINDOWS_DISPATCHED='+$key)
  } else {Log ('QA_P0_CODEBERG_PRIMARY_DOWN_WINDOWS_DISPATCH_FAILED='+$key)}
 }
 $json=$state|ConvertTo-Json -Compress
 $temp=$stateFile+'.tmp'
 Set-Content -Path $temp -Value $json -Encoding UTF8
 Move-Item $temp $stateFile -Force
 exit 0
} catch {
 Log ('QA_P0_CODEBERG_WATCHDOG_EXCEPTION='+$_.Exception.GetType().Name)
 exit 3
} finally {
 if($held){$mutex.ReleaseMutex()}
 $mutex.Dispose()
}
