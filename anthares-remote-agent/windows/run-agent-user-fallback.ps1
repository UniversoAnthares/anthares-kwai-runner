$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$envFile=Join-Path $root 'agent-env.ps1'
if(Test-Path $envFile){. $envFile}
$queueAuthLoader=Join-Path $root 'load-issue-queue-auth.ps1'

# Emergency fallback only. It never selects Render, Cloudflare, Northflank or
# another HTTP controller automatically; the private issue queue is canonical.
$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'
Remove-Item Env:ANTHARES_CONTROL_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_PRIMARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_SECONDARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_TERTIARY_URL -ErrorAction SilentlyContinue
$env:ANTHARES_WORK_ROOT='D:\AntharsWork'
$env:TEMP='D:\AntharsWork\temp'
$env:TMP=$env:TEMP

$roots=@(([string]$env:ANTHARES_ALLOWED_ROOTS -split ';') | ForEach-Object {$_.Trim()} | Where-Object {$_})
if($roots -notcontains 'D:\AntharsWork'){$roots+='D:\AntharsWork'}
$env:ANTHARES_ALLOWED_ROOTS=($roots | Select-Object -Unique) -join ';'
New-Item -ItemType Directory -Force -Path 'D:\AntharsWork\logs','D:\AntharsWork\temp','D:\AntharsWork\legacy-pc-runtime\ara','D:\AntharsWork\ara-jobs' | Out-Null

$legacy=Join-Path $root 'anthares-remote-agent.exe'
$v4=Join-Path $root 'anthares-remote-agent-v4.exe'
$v4Validated=Test-Path (Join-Path $root 'v4-validated.flag')
$exe=if($v4Validated -and (Test-Path $v4)){$v4}elseif(Test-Path $v4){$v4}elseif(Test-Path $legacy){$legacy}else{$v4}
$processName=[IO.Path]::GetFileNameWithoutExtension($exe)

function Load-QueueAuth {
  if(Test-Path $queueAuthLoader){
    try{. $queueAuthLoader}catch{}
  }
  if(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN) -or -not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN)){return}
  # Last-resort user-session recovery: read an existing GitHub CLI credential;
  # never print or persist it and never place it in process arguments.
  $gh='C:\Program Files\GitHub CLI\gh.exe'
  if(Test-Path $gh){
    try{
      $token=(& $gh auth token 2>$null | Select-Object -First 1).Trim()
      if($token){
        $env:ANTHARES_GITHUB_QUEUE_REPOSITORY='UniversoAnthares/anthares-ara-queue'
        $env:ANTHARES_GITHUB_QUEUE_AUTHOR='UniversoAnthares'
        $env:ANTHARES_GITHUB_QUEUE_TOKEN=$token
        $env:ANTHARES_ISSUE_QUEUE_INTERVAL_SECONDS='20'
      }
    }catch{}
  }
}
function Queue-Configured {
  return ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY)) -and (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))) -or
         ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT)) -and (-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN)))
}

$out='D:\AntharsWork\logs\agent-user.stdout.log'
$err='D:\AntharsWork\logs\agent-user.stderr.log'
$launchLog='D:\AntharsWork\logs\agent-user-launch.log'
$state='D:\AntharsWork\legacy-pc-runtime\ara\user-fallback-state.json'
function Save-State([string]$reason,[int]$agentPid=0){
  try{
    [pscustomobject]@{
      updated_at=(Get-Date).ToUniversalTime().ToString('o');device_id=$env:ANTHARES_DEVICE_ID
      binary=(Split-Path $exe -Leaf);control='private-issue-queues';mode='issue-queues-only'
      github_queue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))
      gitlab_queue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))
      identity=$env:USERNAME;session=(Get-Process -Id $PID).SessionId;watchdog_pid=$PID;agent_pid=$agentPid
      reason=$reason;render_required=$false;cloudflare_required=$false;http_control_enabled=$false;work_root=$env:ANTHARES_WORK_ROOT
    } | ConvertTo-Json | Set-Content -Path $state -Encoding UTF8
  }catch{}
}

while($true){
  Load-QueueAuth
  if(-not (Queue-Configured)){
    Save-State 'waiting-for-private-queue-credential'
    Start-Sleep -Seconds 15
    continue
  }

  $running=@(Get-Process -Name $processName -ErrorAction SilentlyContinue)
  if($running.Count -gt 0){
    Save-State 'supervising-existing-agent' $running[0].Id
    Start-Sleep -Seconds 10
    continue
  }

  if($processName -eq 'anthares-remote-agent-v4'){
    $obsolete=@(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard' -ErrorAction SilentlyContinue)
    foreach($proc in $obsolete){try{Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}catch{}}
    if($obsolete.Count -gt 0){Start-Sleep -Milliseconds 800}
  }

  try{
    "$(Get-Date -Format o) starting $(Split-Path $exe -Leaf) mode=issue-queues-only" | Add-Content $launchLog
    $proc=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    Save-State 'started-agent' $proc.Id
    while(-not $proc.HasExited){Start-Sleep -Seconds 10; Load-QueueAuth; Save-State 'running-private-queue' $proc.Id}
    Save-State ('agent-exited:'+ $proc.ExitCode)
  }catch{Save-State ('start-failed:'+ $_.Exception.GetType().Name)}
  Start-Sleep -Seconds 2
}
