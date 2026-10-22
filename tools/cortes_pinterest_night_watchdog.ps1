# Silent CORTES Pinterest watchdog. Never touches personal Chrome tabs.
# Keeps the existing Neon-fenced publisher scheduled through overnight hours.
$ErrorActionPreference='Stop'
$taskName='CORTES-Pinterest-Local'
$browserTask='Anthares CORTES Pinterest Headless Browser Silent'
$log='D:\AntharsWork\cortes-pinterest-local\pinterest-watchdog-health.json'
$status=[ordered]@{at=(Get-Date).ToUniversalTime().ToString('o');publisher='UNKNOWN';
    chrome='UNKNOWN';action='NONE';qa='NONE'}
try{
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    if(-not $task.Settings.Enabled){
        Enable-ScheduledTask -TaskName $taskName -ErrorAction Stop|Out-Null
        $status.action='REENABLED_PUBLISHER'
    }
    $info=Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction Stop
    $lag=((Get-Date)-$info.LastRunTime).TotalMinutes
    # Recover missed scheduled invocations only; never launch parallel instances
    # in reaction to platform-side Publish button rejection.
    if($lag -gt 22 -and [string]$task.State -ne 'Running'){
        Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
        $status.action='RECOVERED_STALE_SCHEDULE'
    }
    $status.publisher='SCHEDULED'
    $status.lastRun=$info.LastRunTime.ToString('o')
    $status.lastResult=$info.LastTaskResult
    $status.nextRun=$info.NextRunTime.ToString('o')
    # A healthy scheduler is NOT evidence of a published Pin. Record separate
    # indicators from the publisher's own sanitized events and Neon ledger.
    $eventsPath='D:\AntharsWork\cortes-pinterest-local\pinterest-browser-events.log'
    if(Test-Path $eventsPath){
        $events=@(Get-Content $eventsPath -Tail 250 -ErrorAction SilentlyContinue|
            ForEach-Object {try{$_|ConvertFrom-Json}catch{}})
        $lastEvent=$events|Select-Object -Last 1
        if($lastEvent){
            $status.lastEvent=[string]$lastEvent.action
            $status.lastEventTime=[string]$lastEvent.when
            if($lastEvent.action -eq 'PINTEREST_DRAFT_CAPACITY_PAUSED'){
                $status.publisher='BLOCKED_DRAFT_CAPACITY'
                $status.qa='PINTEREST_DRAFT_CAPACITY_EXHAUSTED'
            }elseif($lastEvent.action -eq 'PINTEREST_UI_BLOCKED'){
                $status.publisher='DEGRADED_UI'
                $status.qa='PINTEREST_UI_PUBLICATION_BLOCKED'
            }
        }
        $latestPin=@($events|Where-Object {$_.action -eq 'PIN_CONFIRMED'}|
            Select-Object -Last 1)
        if($latestPin.Count -gt 0){$status.lastConfirmedAt=[string]$latestPin[0].when}
    }
    try{
        $health=Invoke-RestMethod 'https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/?action=health' -TimeoutSec 7
        $rows=@($health.counts|Where-Object {$_.target_key -eq 'pinterest:lucasyahn'})
        $queued=@($rows|Where-Object {$_.status -eq 'queued'})
        $confirmed=@($rows|Where-Object {$_.status -eq 'confirmed'})
        $status.queued=if($queued.Count){[int]$queued[0].n}else{0}
        $status.confirmed=if($confirmed.Count){[int]$confirmed[0].n}else{0}
        if($status.publisher -eq 'SCHEDULED' -and $status.queued -gt 0 -and
            $info.LastTaskResult -ne 0){
            $status.publisher='DEGRADED_SCHEDULED_NOT_PUBLISHING'
            $status.qa='PINTEREST_QUEUE_STALLED'
        }
    }catch{$status.queueStatus='LEDGER_HEALTH_UNAVAILABLE'}
    try{
        $version=Invoke-RestMethod 'http://127.0.0.1:9226/json/version' -TimeoutSec 4
        if($version.Browser -match '^Chrome/'){$status.chrome='HEADLESS_PROFILE_UP'}
        else{throw 'UNEXPECTED_BROWSER'}
    }catch{
        # This task only restarts the existing *isolated* headless launcher.
        $br=Get-ScheduledTask -TaskName $browserTask -ErrorAction SilentlyContinue
        if($br -and $br.Settings.Enabled -and [string]$br.State -ne 'Running'){
            Start-ScheduledTask -TaskName $browserTask -ErrorAction Stop
            $status.chrome='HEADLESS_RESTART_REQUESTED'
            $status.action='RECOVERED_HEADLESS_BROWSER'
        }else{$status.chrome='HEADLESS_OFFLINE_OR_STARTING'}
    }
}catch{
    $status.publisher='NEEDS_ATTENTION'
    $status.qa='PINTEREST_WATCHDOG_SCHEDULE_UNAVAILABLE'
}
try{
    $folder=Split-Path -Parent $log
    if(-not(Test-Path $folder)){New-Item -Force -ItemType Directory -Path $folder|Out-Null}
    ($status|ConvertTo-Json -Compress)|Set-Content -Path $log -Encoding UTF8
}catch{}
Write-Output ($status|ConvertTo-Json -Compress)
