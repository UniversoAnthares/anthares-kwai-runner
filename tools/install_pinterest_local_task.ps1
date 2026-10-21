param([string]$RepoPath = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$runner = Join-Path $RepoPath 'tools\cortes_pinterest_local_runner.py'
if (-not (Test-Path $runner)) { throw 'Pinterest local runner missing' }
$python = (Get-Command py -ErrorAction Stop).Source
$action = New-ScheduledTaskAction -Execute $python -Argument ('-3 "' + $runner + '"') -WorkingDirectory $RepoPath
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -MultipleInstances IgnoreNew -Hidden -StartWhenAvailable
Register-ScheduledTask -TaskName 'CORTES-Pinterest-Local' -Action $action -Trigger $trigger -Settings $settings -Description 'Fenced Pinterest local publisher; requires explicit environment arming and OAuth token' -Force | Out-Null
Write-Output 'CORTES-Pinterest-Local installed; publishing remains gated until credentials and arming are present'
