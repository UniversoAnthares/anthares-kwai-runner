# Offline-safe bootstrap for CORTES X. Designed for the authorized Anthares SYSTEM
# remote agent; creates a hidden interactive task that installs the Lucas-owned
# scheduled publisher once the Windows machine reconnects.
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-reliability-qa-20261021'
$token=$env:NORTHFLANK_API_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
  throw 'X_BOOTSTRAP_REMOTE_NORTHFLANK_TOKEN_MISSING'
}
New-Item -ItemType Directory -Path $root -Force | Out-Null
Add-Type -AssemblyName System.Security
$clear=[Text.Encoding]::UTF8.GetBytes($token)
$encrypted=[Security.Cryptography.ProtectedData]::Protect(
  $clear,$null,[Security.Cryptography.DataProtectionScope]::LocalMachine
)
[Array]::Clear($clear,0,$clear.Length)
$recovery=Join-Path $root 'x_northflank_recovery.machine.dpapi'
[IO.File]::WriteAllBytes($recovery,$encrypted)
& icacls $recovery /inheritance:r /grant:r 'SYSTEM:(F)' 'Lucas:(R)' | Out-Null
$installer=Join-Path $root 'x_install_windows_fallback.ps1'
$script=Join-Path $root 'x_bootstrap_windows_standby_runner.ps1'
$vb=Join-Path $root 'x_bootstrap_windows_standby_invisible.vbs'
@'
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-reliability-qa-20261021'
$installer=Join-Path $root 'x_install_windows_fallback.ps1'
$log=Join-Path $root 'x_bootstrap_windows_standby.log'
try {
  $encoded = & gh api 'repos/UniversoAnthares/anthares-kwai-runner/contents/tools/x_install_windows_fallback.ps1?ref=main' --jq '.content'
  if ($LASTEXITCODE -ne 0) { throw 'X_INSTALLER_GITHUB_SYNC_FAILED' }
  [IO.File]::WriteAllBytes($installer,[Convert]::FromBase64String(($encoded -join '' -replace '\s','')))
  & $installer *>> $log
  if (!(Get-ScheduledTask -TaskName 'Anthares X Durable Local Standby' -ErrorAction SilentlyContinue)) {
    throw 'X_STANDBY_TASK_NOT_REGISTERED'
  }
  Disable-ScheduledTask -TaskName 'Anthares X Standby Bootstrap' | Out-Null
} catch {
  Add-Content -Path $log -Value ('['+(Get-Date -Format o)+'] X_BOOTSTRAP_RETRY '+$_.Exception.GetType().Name)
}
'@ | Set-Content -Path $script -Encoding UTF8
@'
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""D:\AntharsWork\x-reliability-qa-20261021\x_bootstrap_windows_standby_runner.ps1""", 0, True
'@ | Set-Content -Path $vb -Encoding Ascii
$action=New-ScheduledTaskAction -Execute (Join-Path $env:WINDIR 'System32\wscript.exe') -Argument ('/B "'+$vb+'"')
$login=New-ScheduledTaskTrigger -AtLogOn -User 'Lucas'
$repeat=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)
$principal=New-ScheduledTaskPrincipal -UserId 'Lucas' -LogonType Interactive -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 12)
Register-ScheduledTask -TaskName 'Anthares X Standby Bootstrap' -Action $action -Trigger @($login,$repeat) -Principal $principal -Settings $settings -Force | Out-Null
try { Start-ScheduledTask -TaskName 'Anthares X Standby Bootstrap' } catch {}
Write-Output 'X_OFFLINE_BOOTSTRAP_TASK_REGISTERED'
