$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$supervisor=Join-Path $root 'run-agent-system-supervisor.ps1'
$backup=Join-Path $root ('run-agent-system-supervisor.ps1.pre-vercel-'+(Get-Date -Format 'yyyyMMddHHmmss')+'.bak')
$url='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/windows/run-agent-system-supervisor.ps1'
if(Test-Path $supervisor){Copy-Item $supervisor $backup -Force}
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile ($supervisor+'.new')
$txt=Get-Content ($supervisor+'.new') -Raw
if($txt -notmatch [regex]::Escape("https://anthares-remote-primary.vercel.app")){throw 'new supervisor does not contain Vercel primary'}
Move-Item ($supervisor+'.new') $supervisor -Force

$restart=Join-Path $root 'cutover-vercel-primary-once.ps1'
@'
$ErrorActionPreference='Continue'
Start-Sleep -Seconds 12
Stop-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -ErrorAction Stop
Start-Sleep -Seconds 8
$t=Get-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -ErrorAction SilentlyContinue
@{restarted=$true;task_state=if($t){[string]$t.State}else{'missing'};at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json -Compress|Set-Content 'C:\ProgramData\AntharesRemoteAgent\vercel-primary-cutover-result.json' -Encoding UTF8
Unregister-ScheduledTask -TaskName 'Anthares Remote Agent Vercel Cutover' -Confirm:$false -ErrorAction SilentlyContinue
'@ | Set-Content $restart -Encoding UTF8

$action=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$restart+'"') -WorkingDirectory $root
$trigger=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddSeconds(20))
$principal=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 3)
Register-ScheduledTask -TaskName 'Anthares Remote Agent Vercel Cutover' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
[pscustomobject]@{ok=$true;supervisor=$supervisor;backup=$backup;vercel_primary=$true;control='https://anthares-remote-primary.vercel.app';cutover_scheduled=$true;cutover_at=$trigger.StartBoundary}|ConvertTo-Json -Compress
