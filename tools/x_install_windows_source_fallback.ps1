# Install the authenticated, invisible Windows origin fallback for long X videos.
# Executed by the elevated Anthares Remote controller. Does not open a browser.
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-longform-source'
$runner=Join-Path $root 'x-source-runner.ps1'
$vb=Join-Path $root 'x-source-invisible.vbs'
$script=Join-Path $root 'x_local_longform_producer.py'
$task='Anthares X Longform Source Fallback'
$python='C:\Users\Lucas\AppData\Local\Programs\Python\Python311\pythonw.exe'
$cookie='D:\AntharsWork\anthares-clipper\runner-media\work\youtube-cookies.txt'
if(!(Test-Path $python)){throw 'X_SOURCE_PYTHONW_MISSING'}
if(!(Test-Path $cookie)){throw 'X_SOURCE_AUTHENTICATED_YOUTUBE_SESSION_MISSING'}
New-Item -ItemType Directory -Path $root -Force|Out-Null
@'
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-longform-source'
$target=Join-Path $root 'x_local_longform_producer.py'
$log=Join-Path $root 'x-source-runner.log'
try {
  $b64 = & gh api 'repos/UniversoAnthares/anthares-kwai-runner/contents/tools/x_local_longform_producer.py?ref=main' --jq '.content'
  if($LASTEXITCODE){throw 'GITHUB_SOURCE_SYNC_FAILED'}
  $new=[Convert]::FromBase64String(($b64 -join '' -replace '\s',''))
  $tmp=$target+'.new'
  [IO.File]::WriteAllBytes($tmp,$new)
  $cmd='C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe'
  & $cmd -m py_compile $tmp |Out-Null
  if($LASTEXITCODE){throw 'PRODUCER_COMPILE_FAILED'}
  Move-Item -LiteralPath $tmp -Destination $target -Force
  $env:PYTHONUTF8='1'
  $env:PYTHONDONTWRITEBYTECODE='1'
  $exe='C:\Users\Lucas\AppData\Local\Programs\Python\Python311\pythonw.exe'
  & $exe $target
  Add-Content -Path $log -Value ('['+(Get-Date -Format o)+'] X_ORIGIN_RUN_COMPLETED')
} catch {
  Add-Content -Path $log -Value ('['+(Get-Date -Format o)+'] X_ORIGIN_RUN_FAILED '+$_.Exception.GetType().Name)
}
'@ | Set-Content -Path $runner -Encoding UTF8
@'
Set sh=CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""D:\AntharsWork\x-longform-source\x-source-runner.ps1""", 0, True
'@ |Set-Content -Path $vb -Encoding Ascii
$action=New-ScheduledTaskAction -Execute (Join-Path $env:WINDIR 'System32\wscript.exe') -Argument ('/B "'+$vb+'"')
$periodic=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(4)) -RepetitionInterval (New-TimeSpan -Hours 2) -RepetitionDuration (New-TimeSpan -Days 3650)
$onlogon=New-ScheduledTaskTrigger -AtLogOn -User 'Lucas'
$principal=New-ScheduledTaskPrincipal -UserId 'Lucas' -LogonType Interactive -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2) -RestartCount 1 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $task -Action $action -Trigger @($periodic,$onlogon) -Principal $principal -Settings $settings -Force|Out-Null
Write-Output 'X_LONGFORM_SOURCE_FALLBACK_INSTALLED'
Write-Output ('X_SOURCE_TASK_STATE='+(Get-ScheduledTask -TaskName $task).State)
