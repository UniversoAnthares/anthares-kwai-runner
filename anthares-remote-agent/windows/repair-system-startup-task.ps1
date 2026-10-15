$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$script=Join-Path $root 'run-agent-system-supervisor.ps1'
if(-not (Test-Path $script)){throw 'supervisor script missing'}
$action=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$script+'"') -WorkingDirectory $root
$trigger=New-ScheduledTaskTrigger -AtStartup
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$principal=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
$wd=Get-ScheduledTask -TaskName 'Anthares Remote Recovery Watchdog' -ErrorAction SilentlyContinue
if($null -ne $wd){Stop-ScheduledTask -TaskName 'Anthares Remote Recovery Watchdog' -ErrorAction SilentlyContinue; Disable-ScheduledTask -TaskName 'Anthares Remote Recovery Watchdog' -ErrorAction SilentlyContinue | Out-Null}
$t=Get-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -ErrorAction Stop
$w=Get-ScheduledTask -TaskName 'Anthares Remote Recovery Watchdog' -ErrorAction SilentlyContinue
[pscustomobject]@{identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;task=$t.TaskName;state=[string]$t.State;enabled=[bool]$t.Settings.Enabled;user=$t.Principal.UserId;restart_count=$t.Settings.RestartCount;restart_interval=[string]$t.Settings.RestartInterval;trigger=(($t.Triggers|ForEach-Object{$_.CimClass.CimClassName})-join ',');watchdog_enabled=if($w){[bool]$w.Settings.Enabled}else{$false};watchdog_state=if($w){[string]$w.State}else{'absent'}}|ConvertTo-Json -Compress
