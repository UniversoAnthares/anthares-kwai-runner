param([string]$RepoPath = (Split-Path -Parent $PSScriptRoot), [string]$RunAs = $env:USERNAME)
$ErrorActionPreference = 'Stop'
$runner=Join-Path $RepoPath 'tools\cortes_provider_mirrors_windows.ps1'
if(-not(Test-Path $runner)){throw 'CORTES_MIRROR_SCRIPT_MISSING'}
$ps=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arguments='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$runner+'"'
$action=New-ScheduledTaskAction -Execute $ps -Argument $arguments -WorkingDirectory $RepoPath
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 12) -MultipleInstances IgnoreNew -Hidden -StartWhenAvailable
# Reuse the same interactive Windows user; do not copy/store OS Git tokens.
$principal=New-ScheduledTaskPrincipal -UserId $RunAs -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'CORTES-Git-Provider-Mirrors' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'GitHub main to GitLab/Codeberg via independent Windows runner; SHA verification and no force push' -Force |Out-Null
Write-Output 'CORTES_GIT_PROVIDER_MIRROR_TASK_INSTALLED'
