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

# Redundancy-only helpers: no trigger and disabled outside an explicit fallback.
$principal=New-ScheduledTaskPrincipal -UserId $UserId -LogonType Interactive -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::FromMinutes(5))
$adbAction=New-ScheduledTaskAction -Execute $adb -Argument '-P 5038 start-server' -WorkingDirectory (Split-Path $adb -Parent)
Register-ScheduledTask -TaskName 'Anthares-MEmu4-ADB5038-Interactive' -Action $adbAction -Principal $principal -Settings $settings -Force | Out-Null
$ps='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$launcherArgs='-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$launcherTarget+'"'
$launcherAction=New-ScheduledTaskAction -Execute $ps -Argument $launcherArgs -WorkingDirectory $InstallRoot
Register-ScheduledTask -TaskName 'Anthares-MEmu4-Recovery-Launcher' -Action $launcherAction -Principal $principal -Settings $settings -Force | Out-Null
foreach($old in @('Anthares MEmu4 Headless Boot','Anthares-MEmu4-Boot','Anthares-MEmu4-Recover','Anthares-MEmu4-Runtime-Recovery','Anthares-MEmu4-Interactive-Launcher')){
  Stop-ScheduledTask -TaskName $old -ErrorAction SilentlyContinue
  Disable-ScheduledTask -TaskName $old -ErrorAction SilentlyContinue | Out-Null
}
foreach($fallback in @('Anthares-MEmu4-ADB5038-Interactive','Anthares-MEmu4-Recovery-Launcher')){
  Stop-ScheduledTask -TaskName $fallback -ErrorAction SilentlyContinue
  Disable-ScheduledTask -TaskName $fallback -ErrorAction SilentlyContinue | Out-Null
}
[ordered]@{ok=$true;primary_authority='Anthares Android Runtime SYSTEM direct headless';fallback_launcher_task='Anthares-MEmu4-Recovery-Launcher';fallback_adb_task='Anthares-MEmu4-ADB5038-Interactive';fallback_default='disabled';adb_server_port=5038;simultaneous_authorities=$false}|ConvertTo-Json -Compress
