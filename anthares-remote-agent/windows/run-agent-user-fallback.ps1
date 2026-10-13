$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
. (Join-Path $root 'agent-env.ps1')

$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'
$env:ANTHARES_WORK_ROOT='D:\AntharsWork'
$env:TEMP='D:\AntharsWork\temp'
$env:TMP=$env:TEMP

$roots=@(([string]$env:ANTHARES_ALLOWED_ROOTS -split ';') | ForEach-Object {$_.Trim()} | Where-Object {$_})
if($roots -notcontains 'D:\AntharsWork'){$roots+='D:\AntharsWork'}
$env:ANTHARES_ALLOWED_ROOTS=($roots | Select-Object -Unique) -join ';'
New-Item -ItemType Directory -Force -Path 'D:\AntharsWork\logs','D:\AntharsWork\temp','D:\AntharsWork\legacy-pc-runtime\ara' | Out-Null

$primary=([string]$env:ANTHARES_CONTROL_PRIMARY_URL).Trim().TrimEnd('/')
$secondary=([string]$env:ANTHARES_CONTROL_SECONDARY_URL).Trim().TrimEnd('/')
if([string]::IsNullOrWhiteSpace($primary)-or $primary -match 'onrender\.com'){$primary='https://anthares-ara-backup.anthares1.workers.dev'}
if([string]::IsNullOrWhiteSpace($secondary)-or $secondary -match 'onrender\.com'){$secondary='https://anthares-ara-reserva.anthares1.workers.dev'}
function Test-Control([string]$origin){
  if([string]::IsNullOrWhiteSpace($origin)){return $false}
  foreach($path in @('/healthz','/health')){
    try{$r=Invoke-WebRequest -UseBasicParsing -Uri ($origin+$path) -TimeoutSec 6;if([int]$r.StatusCode -ge 200 -and [int]$r.StatusCode -lt 300){return $true}}catch{}
  }
  return $false
}
$control=if(Test-Control $primary){$primary}elseif(Test-Control $secondary){$secondary}else{$primary}
$env:ANTHARES_CONTROL_URL=$control

$legacy=Join-Path $root 'anthares-remote-agent.exe'
$v4=Join-Path $root 'anthares-remote-agent-v4.exe'
$v4Validated=Test-Path (Join-Path $root 'v4-validated.flag')
$exe=if($v4Validated -and (Test-Path $v4)){$v4}elseif(Test-Path $legacy){$legacy}elseif(Test-Path $v4){$v4}else{$legacy}
$processName=[IO.Path]::GetFileNameWithoutExtension($exe)

# Native v4 queue transport is enabled only after its production marker exists.
# The credential is read once from GitHub CLI's keyring inside this hidden task;
# it is never persisted by this script or placed in process arguments.
if($processName -eq 'anthares-remote-agent-v4'){
  $gh='C:\Program Files\GitHub CLI\gh.exe'
  if(Test-Path $gh){
    try{
      $token=(& $gh auth token 2>$null).Trim()
      if($token){
        $env:ANTHARES_GITHUB_QUEUE_REPOSITORY='UniversoAnthares/anthares-ara-queue'
        $env:ANTHARES_GITHUB_QUEUE_AUTHOR='UniversoAnthares'
        $env:ANTHARES_GITHUB_QUEUE_TOKEN=$token
        $env:ANTHARES_ISSUE_QUEUE_INTERVAL_SECONDS='5'
      }
    }catch{}
  }
}

$out='D:\AntharsWork\logs\agent-user.stdout.log'
$err='D:\AntharsWork\logs\agent-user.stderr.log'
$launchLog='D:\AntharsWork\logs\agent-user-launch.log'
$state='D:\AntharsWork\legacy-pc-runtime\ara\user-fallback-state.json'
function Save-State([string]$reason,[int]$agentPid=0){
  try{
    [pscustomobject]@{
      updated_at=(Get-Date).ToUniversalTime().ToString('o');device_id=$env:ANTHARES_DEVICE_ID
      binary=(Split-Path $exe -Leaf);control=$control;primary=$primary;secondary=$secondary
      github_queue=[bool]$env:ANTHARES_GITHUB_QUEUE_TOKEN
      identity=$env:USERNAME;session=(Get-Process -Id $PID).SessionId;watchdog_pid=$PID;agent_pid=$agentPid
      reason=$reason;render_required=$false;work_root=$env:ANTHARES_WORK_ROOT
    } | ConvertTo-Json | Set-Content -Path $state -Encoding UTF8
  }catch{}
}

while($true){
  $running=@(Get-Process -Name $processName -ErrorAction SilentlyContinue)
  if($running.Count -gt 0){
    Save-State 'supervising-existing-agent' $running[0].Id
    Start-Sleep -Seconds 5
    continue
  }

  # When v4 is the validated target, retire legacy writers before launch.
  if($processName -eq 'anthares-remote-agent-v4'){
    $obsolete=@(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard' -ErrorAction SilentlyContinue)
    foreach($proc in $obsolete){try{Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}catch{}}
    if($obsolete.Count -gt 0){Start-Sleep -Milliseconds 800}
  }

  try{
    "$(Get-Date -Format o) starting $(Split-Path $exe -Leaf) queue=$([bool]$env:ANTHARES_GITHUB_QUEUE_TOKEN) control=$control" | Add-Content $launchLog
    $proc=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    Save-State 'started-agent' $proc.Id
    while(-not $proc.HasExited){Start-Sleep -Seconds 5; Save-State 'running' $proc.Id}
    Save-State ('agent-exited:'+ $proc.ExitCode)
  }catch{Save-State ('start-failed:'+ $_.Exception.GetType().Name)}
  Start-Sleep -Seconds 2
}
