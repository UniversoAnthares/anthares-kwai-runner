# Install/update cloud-first X standby as an invisible Windows scheduled task.
# Run under the authorized interactive account (Lucas), not SYSTEM.
$ErrorActionPreference = 'Stop'
if ($env:USERNAME -ine 'Lucas') { throw 'X_INSTALL_REQUIRES_LUCAS_INTERACTIVE_USER' }
$root = 'D:\AntharsWork\x-reliability-qa-20261021'
$python = 'C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe'
$script = Join-Path $root 'x_local_browser_consumer.py'
$secret = Join-Path $root 'x_cloud_bridge_token.dpapi'
$runner = Join-Path $root 'x_local_consumer_runner.ps1'
$vbscript = Join-Path $root 'x_local_consumer_invisible.vbs'
$task = 'Anthares X Durable Local Standby'
New-Item -ItemType Directory -Path $root -Force | Out-Null
if (!(Test-Path $python)) { throw 'X_PYTHON_MISSING' }
if (!(Get-ScheduledTask -TaskName 'Anthares X Browser Persistent' -ErrorAction SilentlyContinue)) {
  throw 'X_PERSISTENT_CHROME_TASK_MISSING'
}
if (!(Get-ScheduledTask -TaskName 'Anthares X Window Invisible Guard' -ErrorAction SilentlyContinue)) {
  throw 'X_INVISIBLE_WINDOW_GUARD_MISSING'
}
if (!(Get-Command gh -ErrorAction SilentlyContinue)) { throw 'X_GITHUB_CLI_MISSING' }
# Recovery agent may register the task while the interactive user's process
# environment is unavailable. It can pass the token in a machine-scoped DPAPI
# ciphertext file ACL-restricted to SYSTEM and Lucas. Immediately rewrap it
# under Lucas' user-scoped DPAPI identity and discard the recovery ciphertext.
$machineRecovery = Join-Path $root 'x_northflank_recovery.machine.dpapi'
if ([string]::IsNullOrWhiteSpace($env:NORTHFLANK_API_TOKEN) -and (Test-Path $machineRecovery)) {
  Add-Type -AssemblyName System.Security
  [byte[]]$blob = [IO.File]::ReadAllBytes($machineRecovery)
  [byte[]]$plain = [Security.Cryptography.ProtectedData]::Unprotect(
    $blob, $null, [Security.Cryptography.DataProtectionScope]::LocalMachine
  )
  $env:NORTHFLANK_API_TOKEN = [Text.Encoding]::UTF8.GetString($plain)
  [Array]::Clear($plain, 0, $plain.Length)
}
if (-not [string]::IsNullOrWhiteSpace($env:NORTHFLANK_API_TOKEN)) {
  $secure = ConvertTo-SecureString $env:NORTHFLANK_API_TOKEN -AsPlainText -Force
  $secure | ConvertFrom-SecureString | Set-Content -Path $secret -Encoding Ascii
  & icacls $secret /inheritance:r /grant:r ("{0}:(R)" -f $env:USERNAME) 'SYSTEM:(R)' | Out-Null
}
if (!(Test-Path $secret)) { throw 'X_ENCRYPTED_NORTHFLANK_TOKEN_MISSING' }
if ((Test-Path $machineRecovery) -and (Test-Path $secret)) {
  Remove-Item -LiteralPath $machineRecovery -Force
}
@'
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-reliability-qa-20261021'
$source=Join-Path $root 'x_local_browser_consumer.py'
$stage=Join-Path $root 'x_local_browser_consumer.download'
$log=Join-Path $root 'x_local_consumer.log'
$python='C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe'
$encrypted=Get-Content -Path (Join-Path $root 'x_cloud_bridge_token.dpapi') -Raw
$secure=ConvertTo-SecureString $encrypted.Trim()
$env:NORTHFLANK_API_TOKEN=([System.Net.NetworkCredential]::new('', $secure)).Password
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
try {
  $encoded = & gh api 'repos/UniversoAnthares/anthares-kwai-runner/contents/tools/x_local_browser_consumer.py?ref=main' --jq '.content'
  if ($LASTEXITCODE -ne 0) { throw 'X_GITHUB_SYNC_FAILED' }
  [IO.File]::WriteAllBytes($stage,[Convert]::FromBase64String(($encoded -join '' -replace '\s','')))
  & $python -m py_compile $stage 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'X_NEW_CONSUMER_COMPILE_FAILED' }
  Move-Item -LiteralPath $stage -Destination $source -Force
  & $python -u $source *>> $log
} catch {
  $message='['+(Get-Date -Format o)+'] X_LOCAL_RUNNER_ERROR '+$_.Exception.GetType().Name
  Add-Content -Path $log -Value $message
}
'@ | Set-Content -Path $runner -Encoding UTF8
# wscript invokes Powershell with SW_HIDE; the scheduler itself opens no window.
@'
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""D:\AntharsWork\x-reliability-qa-20261021\x_local_consumer_runner.ps1""", 0, True
'@ | Set-Content -Path $vbscript -Encoding Ascii
$action = New-ScheduledTaskAction -Execute (Join-Path $env:WINDIR 'System32\wscript.exe') -Argument ('/B "'+$vbscript+'"')
$repeat = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
$logon = New-ScheduledTaskTrigger -AtLogOn -User 'Lucas'
$principal = New-ScheduledTaskPrincipal -UserId 'Lucas' -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $task -Action $action -Trigger @($repeat,$logon) -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $task
Write-Output 'X_HIDDEN_LOCAL_STANDBY_INSTALLED'
Write-Output ('X_SCHEDULE_STATE='+(Get-ScheduledTask -TaskName $task).State)
