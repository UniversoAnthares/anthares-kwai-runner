$ErrorActionPreference='Stop'
$root='D:\AntharsWork\AntharesRemoteAgent'
$result=Join-Path $root 'phase4-migration-result.json'
$task='Anthares Remote Agent SYSTEM'
$watchdog='Anthares Remote Recovery Watchdog'
$userTask='Anthares Remote Agent User'
$oldRecovery='Anthares Remote Recovery'
$oldBridge='Anthares-GitHub-Queue-Bridge'
$newExe=Join-Path $root 'anthares-remote-agent-v4.phase4.new.exe'
$exe=Join-Path $root 'anthares-remote-agent-v4.exe'
$lastGood=Join-Path $root 'anthares-remote-agent-v4.lastgood.exe'
try{
  if(-not(Test-Path $newExe)){throw 'staged V4 missing'}
  $oldHash=if(Test-Path $exe){(Get-FileHash $exe -Algorithm SHA256).Hash}else{''}
  $newHash=(Get-FileHash $newExe -Algorithm SHA256).Hash
  if(Test-Path $exe){Copy-Item $exe (Join-Path $root 'anthares-remote-agent-v4.pre-phase4.exe') -Force}
  foreach($n in @($userTask,$oldRecovery,$oldBridge)){try{Disable-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue|Out-Null}catch{}}
  try{Stop-ScheduledTask -TaskName $watchdog -ErrorAction SilentlyContinue}catch{}
  try{Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue}catch{}
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'}|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}catch{}}
  Start-Sleep -Seconds 1
  Copy-Item $newExe $exe -Force
  Copy-Item $exe $lastGood -Force
  [pscustomobject]@{v4_sha256=$newHash;promoted_at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content (Join-Path $root 'integrity-baseline.json') -Encoding UTF8
  $tr=New-ScheduledTaskTrigger -AtStartup
  $pr=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
  $st=New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
  $a=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "D:\AntharsWork\AntharesRemoteAgent\run-agent-system-supervisor.ps1"' -WorkingDirectory $root
  Register-ScheduledTask -TaskName $task -Action $a -Trigger $tr -Principal $pr -Settings $st -Force|Out-Null
  $wa=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "D:\AntharsWork\AntharesRemoteAgent\recovery-watchdog-loop.ps1"' -WorkingDirectory $root
  Register-ScheduledTask -TaskName $watchdog -Action $wa -Trigger $tr -Principal $pr -Settings $st -Force|Out-Null
  Start-ScheduledTask -TaskName $task
  Start-Sleep -Seconds 3
  Start-ScheduledTask -TaskName $watchdog
  [pscustomobject]@{ok=$true;old_hash=$oldHash;new_hash=$newHash;installed_hash=(Get-FileHash $exe -Algorithm SHA256).Hash;root=$root;at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content $result -Encoding UTF8
}catch{
  [pscustomobject]@{ok=$false;error=$_.Exception.Message;at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content $result -Encoding UTF8
  throw
}
