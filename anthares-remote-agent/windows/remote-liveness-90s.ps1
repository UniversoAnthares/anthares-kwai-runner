param([switch]$Once,[switch]$SimulatePrimaryFailure)
$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$log=Join-Path $root 'remote-liveness-90s.log'
$stamp=Join-Path $root 'remote-liveness-last-restart.txt'
$state='D:\AntharsWork\legacy-pc-runtime\supervisor\system-supervisor-state.json'
$task='Anthares Remote Agent SYSTEM'
$primary='https://anthares-remote-primary.vercel.app'
$secondary='https://anthares-remote-secondary.vercel.app'
$device='DESKTOP-FTDK0HP'
$created=$false
if(-not $Once){
  $mutex=New-Object System.Threading.Mutex($true,'Global\AntharesRemoteLiveness90s',[ref]$created)
  if(-not $created){exit 0}
}
function Log([string]$v){
  try{
    ('{0} {1}' -f [DateTimeOffset]::UtcNow.ToString('o'),$v)|Add-Content $log -Encoding UTF8
    if((Get-Item $log).Length -gt 60000){@(Get-Content $log -Tail 100)|Set-Content $log -Encoding UTF8}
  }catch{}
}
function Probe([string]$url,[string]$token){
  try{
    return Invoke-RestMethod -Method Get -Uri ($url+'/v1/device/status') -Headers @{Authorization=('Bearer '+$token);'X-Anthares-Device'=$device} -TimeoutSec 7 -ErrorAction Stop
  }catch{return $null}
}
function Restart-Safely([string]$reason,$status){
  if($Once){Log ('SIMULATION would_restart='+$reason);return}
  $agents=@(Get-CimInstance Win32_Process -Filter "Name='anthares-remote-agent-v4-c8.exe'" | Where-Object {$_.SessionId -eq 0})
  $super=Get-ScheduledTask -TaskName $task -ErrorAction Stop
  if($agents.Count -ne 1 -or $super.State -ne 'Running'){Log ('DEFER wrong_agent_count='+$agents.Count);return}
  if($status -and ([int]$status.leased -gt 0 -or [int]$status.uncertain -gt 0 -or [int]$status.queued -gt 0)){Log 'DEFER jobs_in_flight';return}
  $last=[DateTimeOffset]::MinValue
  if(Test-Path $stamp){try{$last=[DateTimeOffset]::Parse((Get-Content $stamp -Raw).Trim())}catch{}}
  if(([DateTimeOffset]::UtcNow-$last).TotalSeconds -lt 300){Log 'DEFER cutover_cooldown';return}
  $gate=New-Object System.Threading.Mutex($false,'Global\AntharesRemoteExecutionTransitionV1')
  $held=$false
  try{
    $held=$gate.WaitOne(2000)
    if(-not $held){Log 'DEFER transition_mutex_busy';return}
    [DateTimeOffset]::UtcNow.ToString('o')|Set-Content $stamp -Encoding ASCII
    Log ('CUTOVER_START reason='+$reason+' pid='+$agents[0].ProcessId)
    Stop-ScheduledTask -TaskName $task -ErrorAction Stop
    Start-Sleep -Seconds 1
    Stop-Process -Id $agents[0].ProcessId -Force -ErrorAction Stop
    Start-Sleep -Seconds 1
    Start-ScheduledTask -TaskName $task -ErrorAction Stop
    Log 'CUTOVER_SUPERVISOR_STARTED'
  }catch{
    Log ('CUTOVER_ERROR type='+$_.Exception.GetType().Name)
    try{Start-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue}catch{}
  }finally{
    if($held){try{$gate.ReleaseMutex()}catch{}}
    $gate.Dispose()
  }
}
$unavailable=0
$opposite=0
$iteration=0
try{
do{
  try{
    . (Join-Path $root 'agent-env.ps1')
    $token=$env:ANTHARES_DEVICE_TOKEN
    if([string]::IsNullOrWhiteSpace($token)){Log 'SKIP missing_device_token';if($Once){break};Start-Sleep 30;continue}
    $current=$primary
    try{$current=[string](Get-Content $state -Raw | ConvertFrom-Json).active_control}catch{}
    $agents=@(Get-CimInstance Win32_Process -Filter "Name='anthares-remote-agent-v4-c8.exe'" -ErrorAction SilentlyContinue | Where-Object {$_.SessionId -eq 0})
    $p=$null
    if(-not $SimulatePrimaryFailure){$p=Probe $primary $token}
    $s=$null
    if($null -eq $p -or $current -eq $secondary -or $SimulatePrimaryFailure){$s=Probe $secondary $token}
    $good=if($null -ne $p){$p}else{$s}
    if($null -eq $good){
      $unavailable++
      Log ('BOTH_HTTP_UNAVAILABLE tries='+$unavailable+' local_agent_count='+$agents.Count)
      if($agents.Count -eq 0 -and $unavailable -ge 3){
        if(-not $Once){try{Start-ScheduledTask -TaskName 'Anthares Remote Recovery' -ErrorAction Stop}catch{}}
        Log 'RECOVERY_TRIGGER local_agent_absent';$unavailable=0
      }
    }else{
      $unavailable=0
      $seen=[DateTimeOffset]::Parse([string]$good.heartbeat.time)
      $age=([DateTimeOffset]::UtcNow-$seen).TotalSeconds
      $needsMove=(($current -eq $primary -and $null -eq $p -and $null -ne $s) -or ($current -eq $secondary -and $null -ne $p))
      if($needsMove){$opposite++}else{$opposite=0}
      if($Once -or ($iteration % 10 -eq 0)){Log ('PROBE '+$(if($p){'primary'}else{'secondary'})+' age='+[int]$age+' current='+$current+' local_agents='+$agents.Count+' switch_checks='+$opposite)}
      if($needsMove -and $opposite -ge 3){Restart-Safely 'verified_other_endpoint' $good;$opposite=0}
      elseif($age -gt 90 -and $agents.Count -eq 1){Restart-Safely 'stale_heartbeat' $good}
      elseif($agents.Count -eq 0){
        if(-not $Once){try{Start-ScheduledTask -TaskName 'Anthares Remote Recovery' -ErrorAction Stop}catch{}}
        Log 'RECOVERY_TRIGGER no_local_agent'
      }
    }
    if($Once -and $SimulatePrimaryFailure){Log ('SIMULATED_PRIMARY_FAILURE secondary_reachable='+[bool]($null -ne $s))}
  }catch{Log ('WATCHDOG_ERROR '+$_.Exception.GetType().Name)}
  $iteration++
  if(-not $Once){Start-Sleep -Seconds 30}
}while(-not $Once)
}finally{
  if(-not $Once -and $mutex){try{$mutex.ReleaseMutex()}catch{};$mutex.Dispose()}
}
