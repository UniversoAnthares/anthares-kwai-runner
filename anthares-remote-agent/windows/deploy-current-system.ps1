$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$work='D:\AntharsWork'
$stage=Join-Path $work 'temp\ara-current-deploy'
$backup=Join-Path $stage ('rollback-'+(Get-Date -Format 'yyyyMMddHHmmss'))
$log=Join-Path $work 'logs\deploy-current-system.log'
$result=Join-Path $work 'legacy-pc-runtime\supervisor\deploy-current-result.json'
$canonicalTask='Anthares Remote Agent SYSTEM'
$watchdogTask='Anthares Remote Recovery Watchdog'
$repo='UniversoAnthares/anthares-kwai-runner'
$releaseBase='https://github.com/'+$repo+'/releases/download/ara-v4-latest'
$rawBase='https://raw.githubusercontent.com/'+$repo+'/main/anthares-remote-agent/windows'
$tracked=@(
  'anthares-remote-agent-v4.exe','anthares-remote-agent-v4.lastgood.exe','integrity-baseline.json','v4-validated.flag',
  'run-agent-system-supervisor.ps1','run-agent-system-supervisor.ps1.lastgood',
  'load-issue-queue-auth.ps1','load-issue-queue-auth.ps1.lastgood',
  'recovery-watchdog.ps1','recovery-watchdog.ps1.lastgood',
  'recovery-watchdog-loop.ps1','recovery-watchdog-loop.ps1.lastgood'
)
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Tee-Object -FilePath $log -Append}catch{}}
function Stop-ARA{
  try{Stop-ScheduledTask -TaskName $watchdogTask -ErrorAction SilentlyContinue}catch{}
  try{Stop-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue}catch{}
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'}|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}catch{}}
}
function Start-ARA{
  try{Start-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue}catch{}
  try{Start-ScheduledTask -TaskName $watchdogTask -ErrorAction SilentlyContinue}catch{}
}
function Save-Rollback{
  New-Item -ItemType Directory -Force -Path $backup|Out-Null
  $present=@{}
  foreach($name in $tracked){
    $src=Join-Path $root $name
    $exists=Test-Path -LiteralPath $src
    $present[$name]=$exists
    if($exists){Copy-Item -LiteralPath $src -Destination (Join-Path $backup $name) -Force}
  }
  $present|ConvertTo-Json -Depth 3|Set-Content -LiteralPath (Join-Path $backup 'present.json') -Encoding UTF8
}
function Restore-Rollback{
  Stop-ARA
  $present=@{}
  try{$present=Get-Content -LiteralPath (Join-Path $backup 'present.json') -Raw|ConvertFrom-Json}catch{}
  foreach($name in $tracked){
    $dst=Join-Path $root $name
    $src=Join-Path $backup $name
    $wasPresent=$false
    try{$wasPresent=[bool]$present.$name}catch{}
    if($wasPresent -and (Test-Path -LiteralPath $src)){Copy-Item -LiteralPath $src -Destination $dst -Force}
    elseif(-not $wasPresent -and (Test-Path -LiteralPath $dst)){Remove-Item -LiteralPath $dst -Force -ErrorAction SilentlyContinue}
  }
  Start-ARA
}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=[Security.Principal.WindowsPrincipal]::new($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
  Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'))
  exit 0
}

New-Item -ItemType Directory -Force -Path $root,$stage,(Split-Path $log),(Split-Path $result)|Out-Null
Log ('begin elevated identity='+$identity.Name)
try{
  $newExe=Join-Path $stage 'anthares-remote-agent-v4.exe'
  $shaFile=Join-Path $stage 'anthares-remote-agent-v4.exe.sha256'
  $installer=Join-Path $stage 'install-system-v8.ps1'
  Invoke-WebRequest -UseBasicParsing -Uri ($releaseBase+'/anthares-remote-agent-v4.exe') -OutFile $newExe -TimeoutSec 60
  Invoke-WebRequest -UseBasicParsing -Uri ($releaseBase+'/anthares-remote-agent-v4.exe.sha256') -OutFile $shaFile -TimeoutSec 30
  Invoke-WebRequest -UseBasicParsing -Uri ($rawBase+'/install-system-v8.ps1') -OutFile $installer -TimeoutSec 30

  $expected=((Get-Content -LiteralPath $shaFile -Raw).Trim() -split '\s+')[0].ToUpperInvariant()
  if($expected -notmatch '^[0-9A-F]{64}$'){throw 'release checksum file is invalid'}
  $actual=(Get-FileHash -LiteralPath $newExe -Algorithm SHA256).Hash.ToUpperInvariant()
  if($actual -ne $expected){throw 'downloaded V4 checksum mismatch'}
  $errors=$null;$tokens=$null
  [Management.Automation.Language.Parser]::ParseFile($installer,[ref]$tokens,[ref]$errors)|Out-Null
  if($errors.Count){throw ('installer syntax errors: '+$errors.Count)}
  Log ('release verified sha256='+$actual)

  Save-Rollback
  Stop-ARA
  Copy-Item -LiteralPath $newExe -Destination (Join-Path $root 'anthares-remote-agent-v4.exe') -Force
  if((Get-FileHash -LiteralPath (Join-Path $root 'anthares-remote-agent-v4.exe') -Algorithm SHA256).Hash.ToUpperInvariant() -ne $actual){throw 'installed V4 checksum mismatch before installer'}

  & $installer
  $installResult=Join-Path $work 'legacy-pc-runtime\supervisor\install-result.json'
  if(-not(Test-Path -LiteralPath $installResult)){throw 'installer did not produce install-result.json'}
  $r=Get-Content -LiteralPath $installResult -Raw|ConvertFrom-Json
  if(-not [bool]$r.ok -or -not [bool]$r.queue_end_to_end_proof -or -not [bool]$r.mcp_http_transport_configured -or -not [bool]$r.single_executor_enforced -or [int]$r.system_v4_pid -le 0){throw 'installer did not prove canonical dual-transport runtime'}

  $out=[ordered]@{ok=$true;sha256=$actual;system_v4_pid=[int]$r.system_v4_pid;queue_end_to_end_proof=$true;mcp_http_transport_configured=$true;single_executor_enforced=$true;queue_proof_issue=$r.queue_proof_issue;rollback_dir=$backup;completed_at=(Get-Date).ToUniversalTime().ToString('o')}
  $out|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $result -Encoding UTF8
  Log ('SUCCESS '+($out|ConvertTo-Json -Compress))
}catch{
  $message=$_.Exception.Message
  Log ('FAILED '+$message)
  try{Restore-Rollback;Log 'rollback restored'}catch{Log ('rollback failed '+$_.Exception.Message)}
  [ordered]@{ok=$false;error=$message;rollback_dir=$backup;completed_at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath $result -Encoding UTF8
  throw
}
