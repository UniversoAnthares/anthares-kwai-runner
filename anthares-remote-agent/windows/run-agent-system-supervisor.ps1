$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$envFile=Join-Path $root 'agent-env.ps1'
if(Test-Path $envFile){. $envFile}
$queueAuthLoader=Join-Path $root 'load-issue-queue-auth.ps1'
$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'

$workRoot=([string]$env:ANTHARES_WORK_ROOT).Trim()
if([string]::IsNullOrWhiteSpace($workRoot)){$workRoot='D:\AntharsWork'}
$logRoot=Join-Path $workRoot 'logs'
$runtimeRoot=Join-Path $workRoot 'legacy-pc-runtime\supervisor'
@($workRoot,(Join-Path $workRoot 'temp'),$logRoot,$runtimeRoot)|ForEach-Object{try{New-Item -ItemType Directory -Path $_ -Force|Out-Null}catch{}}
$env:ANTHARES_WORK_ROOT=$workRoot
$env:TEMP=Join-Path $workRoot 'temp';$env:TMP=$env:TEMP

# Render is deliberately excluded. Two Cloudflare routes are followed by an
# independent Northflank controller. v4 also polls private GitHub/GitLab queues.
$primary=([string]$env:ANTHARES_CONTROL_PRIMARY_URL).Trim().TrimEnd('/')
$secondary=([string]$env:ANTHARES_CONTROL_SECONDARY_URL).Trim().TrimEnd('/')
$tertiary=([string]$env:ANTHARES_CONTROL_TERTIARY_URL).Trim().TrimEnd('/')
if([string]::IsNullOrWhiteSpace($primary)-or $primary -match 'onrender\.com'){$primary='https://anthares-ara-backup.anthares1.workers.dev'}
if([string]::IsNullOrWhiteSpace($secondary)-or $secondary -match 'onrender\.com'){$secondary='https://anthares-ara-reserva.anthares1.workers.dev'}
if([string]::IsNullOrWhiteSpace($tertiary)-or $tertiary -match 'onrender\.com'){$tertiary='https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run'}

$v4Exe=Join-Path $root 'anthares-remote-agent-v4.exe'
$legacyExe=Join-Path $root 'anthares-remote-agent.exe'
$exe=if(Test-Path $v4Exe){$v4Exe}else{$legacyExe}
$stdout=Join-Path $logRoot 'agent-system.stdout.log'
$stderr=Join-Path $logRoot 'agent-system.stderr.log'
$stateFile=Join-Path $runtimeRoot 'system-supervisor-state.json'

$created=$false
$mutex=New-Object System.Threading.Mutex($true,'Global\AntharesRemoteSystemSupervisorV8',[ref]$created)
if(-not $created){exit 0}

function Load-QueueAuth{
  if(Test-Path $queueAuthLoader){try{. $queueAuthLoader}catch{}}
}
function Github-QueueConfigured{return(-not[string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY))-and(-not[string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))}
function Gitlab-QueueConfigured{return(-not[string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT))-and(-not[string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))}
function Test-Control([string]$origin){
  if([string]::IsNullOrWhiteSpace($origin)){return $false}
  foreach($path in @('/healthz','/health')){try{$r=Invoke-WebRequest -UseBasicParsing -Uri ($origin+$path) -TimeoutSec 8;if([int]$r.StatusCode -ge 200-and[int]$r.StatusCode -lt 300){return $true}}catch{}}
  return $false
}
function Candidate-Controls{@($primary,$secondary,$tertiary)|Where-Object{-not[string]::IsNullOrWhiteSpace($_)}|Select-Object -Unique}
function Choose-Control{foreach($c in Candidate-Controls){if(Test-Control $c){return $c}};return $null}
function Preferred-Alternate([string]$active){foreach($c in Candidate-Controls){if($c -ne $active -and (Test-Control $c)){return $c}};return $null}
function Save-State([string]$active,[string]$reason,[int]$agentPid=0){
  try{[pscustomobject]@{active_control=$active;reason=$reason;updated_at=(Get-Date).ToUniversalTime().ToString('o');supervisor_pid=$PID;agent_pid=$agentPid;device_id=$env:ANTHARES_DEVICE_ID;identity='SYSTEM';session=0;binary=(Split-Path $exe -Leaf);github_queue=[bool](Github-QueueConfigured);gitlab_queue=[bool](Gitlab-QueueConfigured);render_required=$false;control_candidates=@($primary,$secondary,$tertiary);work_root=$workRoot}|ConvertTo-Json -Depth 4|Set-Content $stateFile -Encoding UTF8}catch{}
}

try{
  Load-QueueAuth
  Get-Process -Name 'anthares-remote-agent','anthares-remote-agent-standard','anthares-remote-agent-v4' -ErrorAction SilentlyContinue|Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Milliseconds 800
  while($true){
    Load-QueueAuth
    $active=Choose-Control
    if(-not $active){
      # v4 still provides private issue-queue recovery while HTTP controls are
      # unavailable. Use primary as a nonfunctional HTTP target so the process
      # remains alive and the independent queue goroutine can continue polling.
      $active=$primary
      $reason='http-controls-unavailable-queue-recovery'
    }else{$reason='agent-start'}
    $env:ANTHARES_CONTROL_URL=$active
    Save-State $active $reason
    try{$proc=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr}catch{Save-State $active ('start-failed:'+$_.Exception.GetType().Name);Start-Sleep 5;continue}
    Save-State $active 'running' $proc.Id
    $failures=0;$primaryHealthy=0
    while(-not $proc.HasExited){
      Start-Sleep 10;Load-QueueAuth
      if(Test-Control $active){$failures=0}else{$failures++}
      if($active -ne $primary){if(Test-Control $primary){$primaryHealthy++}else{$primaryHealthy=0}}else{$primaryHealthy=0}
      if($primaryHealthy -ge 6){Save-State $active 'primary-stable-failback' $proc.Id;Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue;break}
      if($failures -ge 2){$alt=Preferred-Alternate $active;if($alt){Save-State $active ('switching-to:'+$alt) $proc.Id;Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue;break}else{Save-State $active 'http-controls-unavailable-queue-recovery' $proc.Id;$failures=0}}
      Save-State $active 'running' $proc.Id
    }
    Start-Sleep 2
  }
}finally{try{$mutex.ReleaseMutex()}catch{};$mutex.Dispose()}
