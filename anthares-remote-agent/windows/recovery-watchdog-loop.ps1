$ErrorActionPreference='Continue'
$watchdog='C:\ProgramData\AntharesRemoteAgent\recovery-watchdog.ps1'
$log='C:\ProgramData\AntharesRemoteAgent\recovery-watchdog-loop.log'
while($true){
  try{& $watchdog}catch{try{"$(Get-Date -Format o) loop failed: $($_.Exception.Message)"|Add-Content -Path $log -Encoding UTF8}catch{}}
  Start-Sleep -Seconds 30
}
