$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$envFile=Join-Path $root 'agent-env.ps1'
if(Test-Path $envFile){. $envFile}
$device='DESKTOP-FTDK0HP'
if([string]::IsNullOrWhiteSpace($env:ANTHARES_DEVICE_TOKEN)){
  [pscustomobject]@{ok=$false;stage='credential';reason='device_token_missing'}|ConvertTo-Json -Compress
  exit 8
}
$headers=@{Authorization=('Bearer '+$env:ANTHARES_DEVICE_TOKEN);'X-Anthares-Device'=$device}
$body=@{device_id=$device;probe=$true}|ConvertTo-Json -Compress
try{
  $r=Invoke-WebRequest -UseBasicParsing -Method POST -Uri 'https://anthares-ara-vercel-reserve.vercel.app/v1/device/heartbeat' -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 20
  [pscustomobject]@{ok=([int]$r.StatusCode -ge 200 -and [int]$r.StatusCode -lt 300);stage='heartbeat';status=[int]$r.StatusCode;body=$r.Content}|ConvertTo-Json -Compress
  exit 0
}catch{
  $status=$null
  if($_.Exception.Response){try{$status=[int]$_.Exception.Response.StatusCode.value__}catch{}}
  [pscustomobject]@{ok=$false;stage='heartbeat';status=$status;error=$_.Exception.Message}|ConvertTo-Json -Compress
  exit 7
}
