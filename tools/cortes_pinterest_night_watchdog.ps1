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
