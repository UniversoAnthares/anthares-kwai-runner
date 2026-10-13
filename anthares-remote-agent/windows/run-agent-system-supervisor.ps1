$ErrorActionPreference='Continue'
$root='D:\AntharsWork\AntharesRemoteAgent'
$envFile=Join-Path $root 'agent-env.ps1'
if(Test-Path $envFile){. $envFile}
$queueAuthLoader=Join-Path $root 'load-issue-queue-auth.ps1'
$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'
$env:ANTHARES_WORK_ROOT='D:\AntharsWork'
$env:TEMP='D:\AntharsWork\temp'
$env:TMP=$env:TEMP
Remove-Item Env:ANTHARES_CONTROL_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_PRIMARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_SECONDARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_TERTIARY_URL -ErrorAction SilentlyContinue
$logRoot='D:\AntharsWork\logs'
$runtimeRoot='D:\AntharsWork\legacy-pc-runtime\supervisor'
@('D:\AntharsWork\temp',$logRoot,'D:\AntharsWork\ara-jobs',$runtimeRoot)|ForEach-Object{New-Item -ItemType Directory -Force -Path $_|Out-Null}
$exe=Join-Path $root 'anthares-remote-agent-v4.exe'
$stdout=Join-Path $logRoot 'agent-system.stdout.log'
$stderr=Join-Path $logRoot 'agent-system.stderr.log'
$stateFile=Join-Path $runtimeRoot 'system-supervisor-state.json'
$created=$false
$mutex=New-Object System.Threading.Mutex($true,'Global\AntharesRemoteSystemSupervisorV10',[ref]$created)
if(-not $created){exit 0}
function Load-QueueAuth{if(Test-Path $queueAuthLoader){try{. $queueAuthLoader}catch{}}}
function Queue-Configured{
  return ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))) -or
         ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN)))
}
function Save-State([string]$reason,[int]$agentPid=0){
  try{[pscustomobject]@{
    active_control='private-issue-queues';mode='issue-queues-only';reason=$reason
    updated_at=(Get-Date).ToUniversalTime().ToString('o');supervisor_pid=$PID;agent_pid=$agentPid
    device_id=$env:ANTHARES_DEVICE_ID;identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    session=(Get-Process -Id $PID -ErrorAction SilentlyContinue).SessionId;binary=(Split-Path $exe -Leaf)
    github_queue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))
    gitlab_queue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))
    http_control_enabled=$false;work_root=$env:ANTHARES_WORK_ROOT;install_root=$root
    stdout_path=$stdout;stderr_path=$stderr
  }|ConvertTo-Json -Depth 4|Set-Content -Path $stateFile -Encoding UTF8}catch{}
}
try{
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{
    $_.SessionId -eq 0 -and $_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'
  }|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}catch{}}
  Start-Sleep -Milliseconds 700
  while($true){
    Load-QueueAuth
    if(-not (Queue-Configured)){Save-State 'waiting-for-private-queue-credential';Start-Sleep 15;continue}
    if(-not (Test-Path $exe)){Save-State 'binary-missing';Start-Sleep 10;continue}
    try{
      $p=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
      Save-State 'running-private-queue' $p.Id
      while(-not $p.HasExited){Start-Sleep 10;Load-QueueAuth;Save-State 'running-private-queue' $p.Id}
      Save-State ('agent-exited:'+ $p.ExitCode)
    }catch{Save-State ('start-failed:'+ $_.Exception.GetType().Name)}
    Start-Sleep 2
  }
}finally{try{$mutex.ReleaseMutex()}catch{};$mutex.Dispose()}
