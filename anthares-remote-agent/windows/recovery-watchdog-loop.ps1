$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$watchdog=Join-Path $root 'recovery-watchdog.ps1'
$log=Join-Path $root 'recovery-watchdog-loop.log'
$critical=@('run-agent-system-supervisor.ps1','load-issue-queue-auth.ps1','recovery-watchdog.ps1')
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Add-Content -Path $log -Encoding UTF8}catch{}}
function Restore-LastGood([string]$name){
  $live=Join-Path $root $name
  $good=$live+'.lastgood'
  if(-not(Test-Path $good)){return}
  $restore=$false
  if(-not(Test-Path $live)){$restore=$true}
  else{try{$restore=((Get-FileHash -LiteralPath $live -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $good -Algorithm SHA256).Hash)}catch{$restore=$true}}
  if($restore){
    try{Copy-Item -LiteralPath $good -Destination $live -Force;Log("restored validated lastgood $name")}catch{Log("failed restoring $name: $($_.Exception.Message)")}
  }
}
while($true){
  foreach($name in $critical){Restore-LastGood $name}
  try{& $watchdog}catch{Log("loop failed: $($_.Exception.Message)")}
  Start-Sleep -Seconds 30
}
