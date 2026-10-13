$ErrorActionPreference='Continue'
$watchdog='D:\AntharsWork\AntharesRemoteAgent\recovery-watchdog.ps1'
$log='D:\AntharsWork\AntharesRemoteAgent\recovery-watchdog-loop.log'
while($true){
  try{& $watchdog}catch{try{"$(Get-Date -Format o) loop failed: $($_.Exception.Message)"|Add-Content -Path $log -Encoding UTF8}catch{}}
  Start-Sleep -Seconds 30
}
