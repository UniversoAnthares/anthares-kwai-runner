$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$envFile=Join-Path $root 'agent-env.ps1'
if(Test-Path $envFile){. $envFile}
if([string]::IsNullOrWhiteSpace($env:ANTHARES_DEVICE_TOKEN)){throw 'device token missing'}
$sha=[System.Security.Cryptography.SHA256]::Create()
try{
  $bytes=[Text.Encoding]::UTF8.GetBytes($env:ANTHARES_DEVICE_TOKEN)
  $hash=($sha.ComputeHash($bytes)|ForEach-Object{$_.ToString('x2')}) -join ''
  [pscustomobject]@{device_id='DESKTOP-FTDK0HP';token_sha256=$hash;algorithm='sha256';token_exposed=$false}|ConvertTo-Json -Compress
}finally{$sha.Dispose()}
