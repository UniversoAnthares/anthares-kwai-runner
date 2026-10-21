param([string]$RepoPath = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$runner = Join-Path $RepoPath 'tools\run_pinterest_browser_local.ps1'
if (-not (Test-Path $runner)) { throw 'Pinterest local browser runner missing' }
$ps = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action = New-ScheduledTaskAction -Execute $ps -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $runner + '"') -WorkingDirectory $RepoPath
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew -Hidden -StartWhenAvailable
Register-ScheduledTask -TaskName 'CORTES-Pinterest-Local' -Action $action -Trigger $trigger -Settings $settings -Description 'Neon-fenced local web UI surplus publisher (Pinterest); browser session required, no API token' -Force | Out-Null
Write-Output 'CORTES-Pinterest-Local: browser publisher installed. Requires authenticated Pinterest Chrome session.'
