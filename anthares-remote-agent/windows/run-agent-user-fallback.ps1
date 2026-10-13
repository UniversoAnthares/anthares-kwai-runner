$ErrorActionPreference='Stop'
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

# User-session fallback obtains the existing GitHub credential from GitHub CLI's
# credential store at runtime. The token is never written by this script.
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

$primary=([string]$env:ANTHARES_CONTROL_PRIMARY_URL).Trim().TrimEnd('/')
if([string]::IsNullOrWhiteSpace($primary)-or $primary -match 'onrender\.com'){
  $primary='https://anthares-ara-backup.anthares1.workers.dev'
}
$env:ANTHARES_CONTROL_URL=$primary

$legacy=Join-Path $root 'anthares-remote-agent.exe'
$v4=Join-Path $root 'anthares-remote-agent-v4.exe'
$exe=if(Test-Path $legacy){$legacy}elseif(Test-Path $v4){$v4}else{$legacy}

# One canonical writer per device. Prefer the agent that has already passed the
# end-to-end Cloudflare heartbeat and remote-exec validation on this machine.
$legacyRunning=@(Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard' -ErrorAction SilentlyContinue)
if($legacyRunning.Count -gt 0){
  "$(Get-Date -Format o) proven legacy agent already running; fallback exits" | Add-Content 'D:\AntharsWork\logs\agent-user-launch.log'
  exit 0
}
$v4Running=@(Get-Process -Name 'anthares-remote-agent-v4' -ErrorAction SilentlyContinue)
if((Test-Path $legacy) -and $v4Running.Count -gt 0){
  foreach($proc in $v4Running){try{Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}catch{}}
  Start-Sleep -Milliseconds 800
}elseif($v4Running.Count -gt 0){
  exit 0
}

$out='D:\AntharsWork\logs\agent-user.stdout.log'
$err='D:\AntharsWork\logs\agent-user.stderr.log'
$state='D:\AntharsWork\legacy-pc-runtime\ara\user-fallback-state.json'
[pscustomobject]@{updated_at=(Get-Date).ToUniversalTime().ToString('o');device_id=$env:ANTHARES_DEVICE_ID;binary=(Split-Path $exe -Leaf);control=$primary;github_queue=[bool]$env:ANTHARES_GITHUB_QUEUE_TOKEN;identity=$env:USERNAME;session=(Get-Process -Id $PID).SessionId;render_required=$false;work_root=$env:ANTHARES_WORK_ROOT} | ConvertTo-Json | Set-Content -Path $state -Encoding UTF8
"$(Get-Date -Format o) starting $(Split-Path $exe -Leaf) queue=$([bool]$env:ANTHARES_GITHUB_QUEUE_TOKEN) control=$primary" | Add-Content 'D:\AntharsWork\logs\agent-user-launch.log'
& $exe 1>>$out 2>>$err
