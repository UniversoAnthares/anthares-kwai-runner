$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$golden=Join-Path $root 'recovery\golden'
$manifestPath=Join-Path $golden 'manifest.json'
$watchdog=Join-Path $root 'recovery-watchdog.ps1'
$log=Join-Path $root 'recovery-watchdog-loop.log'
$critical=@('run-agent-system-supervisor.ps1','load-issue-queue-auth.ps1','recovery-watchdog.ps1')
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Add-Content -Path $log -Encoding UTF8}catch{}}
function Get-ExpectedHash([string]$name){
  try{
    if(-not(Test-Path $manifestPath)){return ''}
    $m=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8|ConvertFrom-Json
    return [string]$m.files.$name.sha256
  }catch{return ''}
}
function Restore-Golden([string]$name){
  $live=Join-Path $root $name
  $good=Join-Path $golden $name
  $expected=Get-ExpectedHash $name
  if([string]::IsNullOrWhiteSpace($expected)-or-not(Test-Path $good)){return}
  try{
    if((Get-FileHash -LiteralPath $good -Algorithm SHA256).Hash -ne $expected){Log("golden copy rejected: $name");return}
    $restore=(-not(Test-Path $live))
    if(-not $restore){$restore=((Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash -ne $expected)}
    if($restore){Copy-Item -LiteralPath $good -Destination $live -Force;Log("restored validated golden $name")}
  }catch{Log("failed restoring $name: $($_.Exception.Message)")}
}
while($true){
  foreach($name in $critical){Restore-Golden $name}
  try{& $watchdog}catch{Log("loop failed: $($_.Exception.Message)")}
  Start-Sleep -Seconds 30
}
