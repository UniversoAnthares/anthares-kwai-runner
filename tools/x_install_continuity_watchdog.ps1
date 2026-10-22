# Elevated one-time install of a hidden, independent X watchdog task.
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-watchdog'
New-Item -ItemType Directory -Force $root|Out-Null
$runner=Join-Path $root 'x-watchdog-runner.ps1'
$vb=Join-Path $root 'x-watchdog-invisible.vbs'
@'
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-watchdog'
$target=Join-Path $root 'x_windows_publication_watchdog.ps1'
try {
 $raw=& gh api 'repos/UniversoAnthares/anthares-kwai-runner/contents/tools/x_windows_publication_watchdog.ps1?ref=main' --jq '.content'
 if($LASTEXITCODE){throw 'WATCHDOG_GH_DOWNLOAD_FAILED'}
 [IO.File]::WriteAllBytes(($target+'.next'),[Convert]::FromBase64String(($raw -join '' -replace '\s','')))
 $parsed=$null;$errors=$null
 [void][System.Management.Automation.Language.Parser]::ParseFile(($target+'.next'),[ref]$parsed,[ref]$errors)
 if(@($errors).Count -gt 0){throw 'WATCHDOG_SCRIPT_PARSE_FAILED'}
 Move-Item -Force ($target+'.next') $target
} catch {
 if(!(Test-Path $target)){throw 'WATCHDOG_CODE_NOT_AVAILABLE'}
}
& $target
'@ | Set-Content -LiteralPath $runner -Encoding UTF8
@'
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""D:\AntharsWork\x-watchdog\x-watchdog-runner.ps1""", 0, True
'@|Set-Content -LiteralPath $vb -Encoding Ascii
$action=New-ScheduledTaskAction -Execute (Join-Path $env:WINDIR 'System32\wscript.exe') -Argument ('/B "'+$vb+'"')
$repeat=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
$startup=New-ScheduledTaskTrigger -AtLogOn -User 'Lucas'
$principal=New-ScheduledTaskPrincipal -UserId 'Lucas' -LogonType Interactive -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 4) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'Anthares X Continuity Watchdog' -Trigger @($repeat,$startup) -Action $action -Principal $principal -Settings $settings -Force|Out-Null
Start-ScheduledTask -TaskName 'Anthares X Continuity Watchdog'
Write-Output 'X_WATCHDOG_REGISTERED'
