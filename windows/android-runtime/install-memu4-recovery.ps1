param(
  [string]$InstallRoot='C:\ProgramData\AntharesRemoteAgent',
  [string]$UserId='DESKTOP-FTDK0HP\Lucas'
)
$ErrorActionPreference='Stop'
$sourceRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherSource=Join-Path $sourceRoot 'memu4-recovery-launcher.ps1'
$launcherTarget=Join-Path $InstallRoot 'memu4-recovery-launcher.ps1'
$adb='D:\Program Files\Microvirt\MEmu\adb.exe'
if(-not (Test-Path $launcherSource)){throw "missing launcher source: $launcherSource"}
if(-not (Test-Path $adb)){throw "missing MEmu adb: $adb"}
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
Copy-Item $launcherSource $launcherTarget -Force
$principal=New-ScheduledTaskPrincipal -UserId $UserId -LogonType Interactive -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
$adbAction=New-ScheduledTaskAction -Execute $adb -Argument '-P 5038 start-server' -WorkingDirectory (Split-Path $adb -Parent)
Register-ScheduledTask -TaskName 'Anthares-MEmu4-ADB5038-Interactive' -Action $adbAction -Principal $principal -Settings $settings -Force | Out-Null
$ps='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$launcherArgs='-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$launcherTarget+'"'
$launcherAction=New-ScheduledTaskAction -Execute $ps -Argument $launcherArgs -WorkingDirectory $InstallRoot
Register-ScheduledTask -TaskName 'Anthares-MEmu4-Recovery-Launcher' -Action $launcherAction -Principal $principal -Settings $settings -Force | Out-Null
foreach($old in @('Anthares MEmu4 Headless Boot','Anthares-MEmu4-Boot','Anthares-MEmu4-Recover')){Disable-ScheduledTask -TaskName $old -ErrorAction SilentlyContinue | Out-Null}
Enable-ScheduledTask -TaskName 'Anthares-MEmu4-ADB5038-Interactive' | Out-Null
Enable-ScheduledTask -TaskName 'Anthares-MEmu4-Recovery-Launcher' | Out-Null
[ordered]@{ok=$true;launcher_task='Anthares-MEmu4-Recovery-Launcher';adb_task='Anthares-MEmu4-ADB5038-Interactive';adb_server_port=5038;legacy_headless_tasks_disabled=$true}|ConvertTo-Json -Compress