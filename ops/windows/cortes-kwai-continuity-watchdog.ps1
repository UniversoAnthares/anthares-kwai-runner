$ErrorActionPreference='Stop'
# Independent Scheduled Task. No publication or queue mutation occurs here.
$root='D:\AntharsWork\quota-write-20261017'
$state=Join-Path $root '.state'
$log=Join-Path $state 'kwai-continuity-watchdog.log'
$publisherTask='Anthares CORTES Kwai Physical Publisher'
$pause=Join-Path $state 'cortes-publisher-maintenance.pause'
$autoheal=Join-Path $root 'ops\windows\cortes-kwai-autoheal.py'
$python='C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe'

function Note([string]$event) {
  if(!(Test-Path -LiteralPath $state)){New-Item -ItemType Directory -Path $state -Force | Out-Null}
  Add-Content -LiteralPath $log -Value ((Get-Date -Format o)+' '+$event) -Encoding UTF8
}
try {
  # A running publisher already owns its queue lease and process lock.
  $daemon=@(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'kwai_physical_queue_daemon\.py\s+daemon(?:\s|$)' })
  if($daemon.Count -gt 0) {
    # A stalled daemon is reported separately. Never kill an in-flight publish.
    $queueLog=Join-Path $state 'kwai-physical-queue.log'
    if((Test-Path -LiteralPath $queueLog) -and
       (Get-Item -LiteralPath $queueLog).LastWriteTime -lt (Get-Date).AddMinutes(-9)){
      Note 'ALERT_DAEMON_SILENT_POSSIBLE_INFLIGHT_FENCING_PRESERVED'
    }
    exit 0
  }
  # A pause is a safety gate. Only the existing identity/cap-aware healer
  # is authorized to clear a positively tagged AUTO_RECOVERY_ALLOWED pause.
  if(Test-Path -LiteralPath $pause) {
    if(!(Test-Path -LiteralPath $autoheal) -or !(Test-Path -LiteralPath $python)){
      Note 'HOLD_PAUSE_HEALER_UNAVAILABLE'
      exit 1
    }
    & $python -u $autoheal 2>&1 | Out-Null
    if(Test-Path -LiteralPath $pause){Note 'HOLD_PAUSE_NOT_AUTHORIZED_FOR_RELEASE';exit 0}
    Note 'AUTOHEAL_RELEASED_AUTHORIZED_PAUSE'
  }
  $task=Get-ScheduledTask -TaskName $publisherTask -ErrorAction SilentlyContinue
  if(!$task){Note 'ERROR_PUBLISHER_TASK_MISSING';exit 1}
  # Start the existing authenticated task. Never run an alternative publisher
  # with different credentials, bypass the fenced lease, or alter daily quotas.
  Start-ScheduledTask -TaskName $publisherTask -ErrorAction Stop
  Note 'PUBLISHER_DAEMON_RESTART_REQUESTED'
  exit 0
} catch {
  Note ('ERROR_CONTINUITY_WATCHDOG '+$_.Exception.GetType().Name)
  exit 1
}
