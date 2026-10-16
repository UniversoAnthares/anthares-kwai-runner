$ErrorActionPreference='Continue'
$runtime='C:\ProgramData\AntharesRemoteAgent\android-runtime\anthares-android-runtime-v2.ps1'
$log='D:\AntharsWork\logs\anthares-android-boot.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
function Log([string]$m){try{Add-Content -LiteralPath $log -Encoding UTF8 -Value ((Get-Date).ToUniversalTime().ToString('o')+' '+$m)}catch{}}
Log 'boot-runtime begin'
Start-Sleep -Seconds 20
for($i=1;$i -le 8;$i++){
  try{
    $raw=(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $runtime -Command health | Out-String).Trim()
    $h=$raw|ConvertFrom-Json
    if($h.memu.healthy){Log ('healthy attempt='+$i+' transport='+$h.memu.transport);exit 0}
  }catch{Log ('health-error attempt='+$i+' '+$_.Exception.Message)}
  try{& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $runtime -Command recover -Target memu -AllowBackendStart -AllowBackendReset | Out-Null}catch{Log ('recover-error attempt='+$i+' '+$_.Exception.Message)}
  Start-Sleep -Seconds 20
}
Log 'ERROR boot-runtime recovery exhausted'
exit 4
