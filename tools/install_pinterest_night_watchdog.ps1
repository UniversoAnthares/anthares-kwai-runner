param([string]$RepoPath=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
$name='CORTES-Pinterest-Local-Watchdog'
$file=Join-Path $RepoPath 'tools\cortes_pinterest_night_watchdog.ps1'
if(-not(Test-Path $file)){throw 'PINTEREST_WATCHDOG_SCRIPT_NOT_FOUND'}
$ps=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action=New-ScheduledTaskAction -Execute $ps -WorkingDirectory $RepoPath -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$file+'"')
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 365)
$settings=New-ScheduledTaskSettingsSet -Hidden -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 2) -MultipleInstances IgnoreNew
$principal=New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Silent Pinterest Neon-fenced publisher and headless browser continuity watchdog' -Force|Out-Null
Write-Output 'CORTES_PINTEREST_WATCHDOG_INSTALLED'
