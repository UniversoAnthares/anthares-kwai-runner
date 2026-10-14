$ErrorActionPreference = 'Continue'
$root = 'C:\ProgramData\AntharesRemoteAgent'
$breakGlass = Join-Path $root 'allow-http-compat.flag'
$stateFile = Join-Path $root 'standard-supervisor-state.json'
if(-not(Test-Path $breakGlass)){
    try{[pscustomobject]@{active_control='';reason='retired-http-compat-break-glass-required';updated_at=(Get-Date).ToUniversalTime().ToString('o');canonical='private-issue-queues';render_required=$false}|ConvertTo-Json|Set-Content -Path $stateFile -Encoding UTF8}catch{}
    exit 0
}
. (Join-Path $root 'agent-env.ps1')

# Legacy standard HTTP supervisor: explicit break-glass only. Render is retired.
$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP'
$primary = 'https://anthares-ara-backup.anthares1.workers.dev'
$secondary = 'https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run'
$exe = Join-Path $root 'anthares-remote-agent-standard.exe'
$stdout = Join-Path $root 'agent-standard.stdout.log'
$stderr = Join-Path $root 'agent-standard.stderr.log'
$forceSecondary = Join-Path $root 'force-secondary.flag'

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\AntharesRemoteAgentStandardSupervisor', [ref]$created)
if (-not $created) { exit 0 }

function Test-Control([string]$origin){try{$r=Invoke-WebRequest -UseBasicParsing -Uri ($origin+'/healthz') -TimeoutSec 12;return([int]$r.StatusCode -ge 200 -and [int]$r.StatusCode -lt 300)}catch{return $false}}
function Save-State([string]$active,[string]$reason,[int]$agentPid=0){try{[pscustomobject]@{active_control=$active;reason=$reason;updated_at=(Get-Date).ToUniversalTime().ToString('o');supervisor_pid=$PID;agent_pid=$agentPid;device_id=$env:ANTHARES_DEVICE_ID;break_glass=$true;render_required=$false}|ConvertTo-Json|Set-Content -Path $stateFile -Encoding UTF8}catch{}}
function Choose-Control {
    if(Test-Path $forceSecondary){if(Test-Control $secondary){return $secondary};if(Test-Control $primary){return $primary};return $null}
    if(Test-Control $primary){return $primary};if(Test-Control $secondary){return $secondary};return $null
}
function Preferred-Alternate([string]$active){foreach($candidate in @($primary,$secondary)){if($candidate -ne $active -and (Test-Control $candidate)){return $candidate}};return $null}

try{
  while($true){
    if(-not(Test-Path $breakGlass)){Save-State '' 'break-glass-revoked';break}
    Get-Process -Name 'anthares-remote-agent-standard' -ErrorAction SilentlyContinue|ForEach-Object{try{Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue}catch{}}
    $active=Choose-Control
    if(-not $active){Save-State '' 'all-controls-unavailable';Start-Sleep 10;continue}
    $env:ANTHARES_CONTROL_URL=$active
    Save-State $active 'agent-start'
    try{$proc=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr}catch{Save-State $active ('start-failed:'+ $_.Exception.GetType().Name);Start-Sleep 10;continue}
    Save-State $active 'running' $proc.Id
    $failures=0
    while(-not $proc.HasExited){
      Start-Sleep 15
      if(-not(Test-Path $breakGlass)){try{Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}catch{};break}
      if(Test-Control $active){$failures=0;continue}
      $failures++
      if($failures -lt 2){continue}
      $alternate=Preferred-Alternate $active
      if($alternate){Save-State $active ('switching-to:'+ $alternate) $proc.Id;try{Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}catch{};break}
      Save-State $active 'active-unhealthy-no-alternate' $proc.Id;$failures=0
    }
    if($proc.HasExited){Save-State $active ('agent-exited:'+ $proc.ExitCode)}
    Start-Sleep 2
  }
}finally{try{$mutex.ReleaseMutex()}catch{};$mutex.Dispose()}
