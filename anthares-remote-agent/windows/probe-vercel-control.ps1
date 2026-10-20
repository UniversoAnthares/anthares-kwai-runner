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
$routes=@('https://anthares-remote-primary.vercel.app','https://anthares-remote-secondary.vercel.app')
$results=@()
foreach($base in $routes){
  try{
    $j=Invoke-RestMethod -Method Get -Uri ($base+'/v1/device/auth-check') -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    $ready=[bool]($j.ok -eq $true -and $j.backend -eq 'vercel-neon')
    $results += [pscustomobject]@{url=$base;ready=$ready}
  }catch{
    $status='network'
    if($_.Exception.Response){try{$status=[int]$_.Exception.Response.StatusCode}catch{}}
    $results += [pscustomobject]@{url=$base;ready=$false;http_status=$status}
  }
}
$healthy=@($results|Where-Object{$_.ready}).Count
[pscustomobject]@{ok=($healthy -ge 1);stage='authenticated_read_only_health';healthy_endpoints=$healthy;endpoints=$results}|ConvertTo-Json -Compress -Depth 4
if($healthy -ge 1){exit 0}
exit 7
