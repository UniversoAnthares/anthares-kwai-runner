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

$gh='C:\Program Files\GitHub CLI\gh.exe'
function Load-QueueAuth {
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
Load-QueueAuth

$primary=([string]$env:ANTHARES_CONTROL_PRIMARY_URL).Trim().TrimEnd('/')
if([string]::IsNullOrWhiteSpace($primary)-or $primary -match 'onrender\.com'){
  $primary='https://anthares-ara-backup.anthares1.workers.dev'
}
$env:ANTHARES_CONTROL_URL=$primary

$legacy=Join-Path $root 'anthares-remote-agent.exe'
$v4=Join-Path $root 'anthares-remote-agent-v4.exe'
$exe=if(Test-Path $legacy){$legacy}elseif(Test-Path $v4){$v4}else{$legacy}
$processName=[IO.Path]::GetFileNameWithoutExtension($exe)
$out='D:\AntharsWork\logs\agent-user.stdout.log'
$err='D:\AntharsWork\logs\agent-user.stderr.log'
$launchLog='D:\AntharsWork\logs\agent-user-launch.log'
$state='D:\AntharsWork\legacy-pc-runtime\ara\user-fallback-state.json'

function Save-State([string]$reason,[int]$agentPid=0){
  try{
    [pscustomobject]@{
      updated_at=(Get-Date).ToUniversalTime().ToString('o');device_id=$env:ANTHARES_DEVICE_ID
      binary=(Split-Path $exe -Leaf);control=$primary;github_queue=[bool]$env:ANTHARES_GITHUB_QUEUE_TOKEN
      identity=$env:USERNAME;session=(Get-Process -Id $PID).SessionId;watchdog_pid=$PID;agent_pid=$agentPid
      reason=$reason;render_required=$false;work_root=$env:ANTHARES_WORK_ROOT
    } | ConvertTo-Json | Set-Content -Path $state -Encoding UTF8
  }catch{}
}

# Persistent hidden watchdog for the non-elevated fallback. It supervises the
# already-proven agent and only launches a replacement after the agent exits.
while($true){
  Load-QueueAuth
  $running=@(Get-Process -Name $processName -ErrorAction SilentlyContinue)
  if($running.Count -gt 0){
    Save-State 'supervising-existing-agent' $running[0].Id
    Start-Sleep -Seconds 5
    continue
  }

  if($processName -eq 'anthares-remote-agent' -and (Test-Path $legacy)){
    $v4Running=@(Get-Process -Name 'anthares-remote-agent-v4' -ErrorAction SilentlyContinue)
    foreach($proc in $v4Running){try{Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}catch{}}
  }

  try{
    "$(Get-Date -Format o) starting $(Split-Path $exe -Leaf) queue=$([bool]$env:ANTHARES_GITHUB_QUEUE_TOKEN) control=$primary" | Add-Content $launchLog
    $proc=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    Save-State 'started-agent' $proc.Id
    while(-not $proc.HasExited){
      Start-Sleep -Seconds 5
      Save-State 'running' $proc.Id
    }
    Save-State ('agent-exited:'+ $proc.ExitCode)
  }catch{
    Save-State ('start-failed:'+ $_.Exception.GetType().Name)
  }
  Start-Sleep -Seconds 2
}
