# One-shot Phase 5 token intake. Runs as SYSTEM, never prints the token.
$ErrorActionPreference='Stop'
$tokenFile='C:\Users\Lucas\Downloads\ara-gitlab-token.txt'
$activator='C:\ProgramData\AntharesRemoteAgent\enable-gitlab-queue.ps1'
$status='C:\ProgramData\AntharesRemoteAgent\phase5-gitlab-intake-status.json'
$deadline=(Get-Date).AddMinutes(20)
try{
  while((Get-Date)-lt $deadline -and -not(Test-Path -LiteralPath $tokenFile)){Start-Sleep -Seconds 2}
  if(-not(Test-Path -LiteralPath $tokenFile)){throw 'token-file-timeout'}
  $plain=(Get-Content -LiteralPath $tokenFile -Raw -Encoding UTF8).Trim()
  if([string]::IsNullOrWhiteSpace($plain)){throw 'token-file-empty'}
  $secure=ConvertTo-SecureString $plain -AsPlainText -Force
  $plain=$null
  Remove-Item -LiteralPath $tokenFile -Force -ErrorAction SilentlyContinue
  $result=& $activator -GitlabToken $secure
  $secure=$null
  [pscustomobject]@{ok=$true;completed_at=(Get-Date).ToUniversalTime().ToString('o');result=($result -join "`n");token_file_deleted=(-not(Test-Path -LiteralPath $tokenFile));token_printed=$false}|ConvertTo-Json -Compress|Set-Content -LiteralPath $status -Encoding UTF8
}catch{
  try{Remove-Item -LiteralPath $tokenFile -Force -ErrorAction SilentlyContinue}catch{}
  [pscustomobject]@{ok=$false;completed_at=(Get-Date).ToUniversalTime().ToString('o');error=$_.Exception.Message;token_file_deleted=(-not(Test-Path -LiteralPath $tokenFile));token_printed=$false}|ConvertTo-Json -Compress|Set-Content -LiteralPath $status -Encoding UTF8
  exit 1
}
