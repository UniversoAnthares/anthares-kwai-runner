$ErrorActionPreference='Stop'
# Run elevated once on the dedicated Windows publisher. Installed task
# runs hidden as SYSTEM, independently of GitHub/GitLab and Anthares Remote.
$root='D:\AntharsWork\quota-write-20261017'
$script=Join-Path $root 'ops\windows\cortes-kwai-continuity-watchdog.ps1'
$taskName='Anthares CORTES Kwai Continuity Watchdog'
if(!(Test-Path -LiteralPath $script)){throw 'KWAI_WATCHDOG_SCRIPT_NOT_DEPLOYED'}
$taskCmd='powershell.exe -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$script+'"'
& schtasks.exe /Create /F /SC MINUTE /MO 2 /RU SYSTEM /RL HIGHEST /TN $taskName /TR $taskCmd | Out-Null
if($LASTEXITCODE -ne 0){throw 'KWAI_WATCHDOG_TASK_REGISTRATION_FAILED'}
$registered=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
if($registered.State -eq 'Disabled'){throw 'KWAI_WATCHDOG_TASK_DISABLED'}
# First run checks/restarts the canonical daemon without submitting a post.
Start-ScheduledTask -TaskName $taskName
Write-Output 'KWAI_CONTINUITY_WATCHDOG_REGISTERED=1 INTERVAL_MINUTES=2 HIDDEN=1'
