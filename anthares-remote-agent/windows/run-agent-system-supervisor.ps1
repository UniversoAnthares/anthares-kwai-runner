# Anthares human reboot consent guard: preserve SYSTEM; remove only reboot rights.
. 'C:\ProgramData\AntharesRebootConsent\native.ps1'
foreach($rebootPrivilege in @('SeShutdownPrivilege','SeRemoteShutdownPrivilege')) {
 [AntharesRebootToken]::Remove($PID,$rebootPrivilege)
 if([AntharesRebootToken]::Present($PID,$rebootPrivilege)){throw 'Reboot consent guard failed'}
}
$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$envFile=Join-Path $root 'agent-env.ps1'
if(Test-Path $envFile){. $envFile}
$queueAuthLoader=Join-Path $root 'load-issue-queue-auth.ps1'
$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'
$env:ANTHARES_MAX_CONCURRENT='8'
$env:ANTHARES_WORK_ROOT='D:\AntharsWork'
$env:TEMP='D:\AntharsWork\temp'
$env:TMP=$env:TEMP
# Vercel + Neon is the normal low-latency control plane.
# GitLab and GitHub private issue queues remain independent recovery transports.
$httpControl='https://anthares-remote-primary.vercel.app'
Remove-Item Env:ANTHARES_CONTROL_PRIMARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_SECONDARY_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_CONTROL_TERTIARY_URL -ErrorAction SilentlyContinue
$logRoot='D:\AntharsWork\logs'
$runtimeRoot='D:\AntharsWork\legacy-pc-runtime\supervisor'
@('D:\AntharsWork\temp',$logRoot,'D:\AntharsWork\ara-jobs',$runtimeRoot)|ForEach-Object{New-Item -ItemType Directory -Force -Path $_|Out-Null}
$exe=Join-Path $root 'anthares-remote-agent-v4-c8.exe'
$stdout=Join-Path $logRoot 'agent-v4-system.stdout.log'
$stderr=Join-Path $logRoot 'agent-v4-system.stderr.log'
$stateFile=Join-Path $runtimeRoot 'system-supervisor-state.json'
$created=$false
$mutex=New-Object System.Threading.Mutex($true,'Global\AntharesRemoteSystemSupervisorV12',[ref]$created)
if(-not $created){exit 0}
function Load-QueueAuth{if(Test-Path $queueAuthLoader){try{. $queueAuthLoader}catch{}}}
function Queue-Configured{
  return ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))) -or
         ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN)))
}
. (Join-Path $root 'ara-http-selector.ps1')
$script:HttpChosen=$false
function Configure-HttpTransport {
  param([switch]$Refresh)
  if([string]::IsNullOrWhiteSpace($env:ANTHARES_DEVICE_TOKEN)){
    Remove-Item Env:ANTHARES_CONTROL_URL -ErrorAction SilentlyContinue
    return $false
  }
  if($Refresh -or -not $script:HttpChosen){
    $choice=Select-AraHttpTransport -Token $env:ANTHARES_DEVICE_TOKEN -Device $env:ANTHARES_DEVICE_ID
    $env:ANTHARES_CONTROL_URL=$choice.origin
    $script:HttpChosen=$true
    try{
      ('{0} selection={1} origin={2}' -f [DateTimeOffset]::UtcNow.ToString('o'),$choice.reason,$choice.origin) |
        Add-Content -Path (Join-Path $logRoot 'ara-http-selector.log') -Encoding UTF8
    }catch{}
  }
  return $true
}
function Save-State([string]$reason,[int]$agentPid=0){
  $httpEnabled=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_CONTROL_URL))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_DEVICE_TOKEN))
  $githubQueue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))
  $gitlabQueue=(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))
  try{[pscustomobject]@{
    active_control=if($httpEnabled){$env:ANTHARES_CONTROL_URL}else{'private-issue-queues'}
    mode=if($httpEnabled){'single-process-dual-transport'}else{'issue-queues-only'}
    recovery_transport='gitlab+github-private-issue-queues';reason=$reason
    updated_at=(Get-Date).ToUniversalTime().ToString('o');supervisor_pid=$PID;agent_pid=$agentPid
    device_id=$env:ANTHARES_DEVICE_ID;identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    session=(Get-Process -Id $PID -ErrorAction SilentlyContinue).SessionId;binary=(Split-Path $exe -Leaf)
    max_concurrent=[int]$env:ANTHARES_MAX_CONCURRENT
    github_queue=$githubQueue
    gitlab_queue=$gitlabQueue
    dual_queue_redundancy=($githubQueue -and $gitlabQueue)
    http_control_enabled=$httpEnabled;http_control=if($httpEnabled){$env:ANTHARES_CONTROL_URL}else{$null}
    single_executor=$true;work_root=$env:ANTHARES_WORK_ROOT;install_root=$root
    stdout_path=$stdout;stderr_path=$stderr
  }|ConvertTo-Json -Depth 4|Set-Content -Path $stateFile -Encoding UTF8}catch{}
}
try{
  while($true){
    # Reload protected device configuration before every supervised agent launch.
    if(Test-Path $envFile){. $envFile}
    Load-QueueAuth
    if(-not (Queue-Configured)){Save-State 'waiting-for-private-queue-credential';Start-Sleep 15;continue}
    [void](Configure-HttpTransport -Refresh)
    if(-not (Test-Path $exe)){Save-State 'binary-missing';Start-Sleep 10;continue}
    try{
      $transition=$null;$transitionHeld=$false
      try{
        $transition=New-Object System.Threading.Mutex($false,'Global\AntharesRemoteExecutionTransitionV1')
        $transitionHeld=$transition.WaitOne(10000)
        if(-not $transitionHeld){throw 'execution_transition_lock_busy'}
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -eq 'anthares-remote-agent-v4.exe'} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}
        # A stopped SYSTEM task may leave its child agent running.
        # Adopt that already healthy canonical agent instead of creating
        # a second consumer of the same queues.
        $existing=@(Get-CimInstance Win32_Process -Filter "Name='anthares-remote-agent-v4-c8.exe'" -ErrorAction Stop |
          Where-Object {$_.SessionId -eq 0 -and $_.ExecutablePath -ieq $exe})
        if($existing.Count -gt 1){throw 'multiple-canonical-agents'}
        if($existing.Count -eq 1){
          $p=Get-Process -Id $existing[0].ProcessId -ErrorAction Stop
          Save-State 'adopted-existing-canonical-agent' $p.Id
        }else{
          $p=Start-Process -FilePath $exe -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        }
      }finally{
        if($transitionHeld -and $transition){try{$transition.ReleaseMutex()}catch{}}
        if($transition){$transition.Dispose()}
      }
      $mode=if($env:ANTHARES_CONTROL_URL){'running-vercel-selected-with-private-queue-recovery'}else{'running-private-queue'}
      Save-State $mode $p.Id
      while(-not $p.HasExited){Start-Sleep 10;Load-QueueAuth;[void](Configure-HttpTransport);Save-State $mode $p.Id}
      Save-State ('agent-exited:'+ $p.ExitCode)
    }catch{Save-State ('start-failed:'+ $_.Exception.GetType().Name)}
    Start-Sleep 2
  }
}finally{try{$mutex.ReleaseMutex()}catch{};$mutex.Dispose()}


