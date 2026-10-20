$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$work='D:\AntharsWork'
$primary=Join-Path $root 'anthares-remote-agent-v4-c8.exe'
$reserve=Join-Path $root 'anthares-remote-agent-v4.exe'
$agentEnv=Join-Path $root 'agent-env.ps1'
$queueLoader=Join-Path $root 'load-issue-queue-auth.ps1'
$state=Join-Path $work 'ara-failover-state.json'
$log=Join-Path $work 'ara-failover.log'
$graceSeconds=90
$pollSeconds=10
$missingSince=$null

function Log([string]$m){
  try{
    "$(Get-Date -Format o) $m"|Add-Content -LiteralPath $log -Encoding UTF8
    $lines=@(Get-Content -LiteralPath $log -ErrorAction SilentlyContinue)
    if($lines.Count -gt 50){$lines|Select-Object -Last 50|Set-Content -LiteralPath $log -Encoding UTF8}
  }catch{}
}
function Get-Primary {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {$_.Name -eq 'anthares-remote-agent-v4-c8.exe' -and $_.SessionId -eq 0})
}
function Get-Reserve {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {$_.Name -eq 'anthares-remote-agent-v4.exe'})
}
function Stop-Reserve([string]$why){
  foreach($p in @(Get-Reserve)){
    try{
      Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
      Log("reserve stopped pid=$($p.ProcessId) reason=$why")
    }catch{
      Log("reserve stop failed pid=$($p.ProcessId): $($_.Exception.Message)")
    }
  }
}
function Start-Reserve {
  if(-not(Test-Path $reserve)){Log('reserve binary missing');return}
  $transition=$null;$held=$false
  try{
    $transition=New-Object System.Threading.Mutex($false,'Global\AntharesRemoteExecutionTransitionV1')
    $held=$transition.WaitOne(10000)
    if(-not $held){Log('reserve start skipped: transition lock busy');return}
    if(@(Get-Primary).Count -gt 0){Log('reserve start skipped: primary recovered');return}
    if(@(Get-Reserve).Count -gt 0){return}
    if(Test-Path $agentEnv){. $agentEnv}
    if(Test-Path $queueLoader){. $queueLoader}
    $env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'
        $selector=Join-Path $root 'ara-http-selector.ps1'
    if(Test-Path $selector){
      . $selector
      $choice=Select-AraHttpTransport -Token $env:ANTHARES_DEVICE_TOKEN -Device 'DESKTOP-FTDK0HP'
      $env:ANTHARES_CONTROL_URL=$choice.origin
      Log("reserve transport selected: $($choice.reason)")
    }else{
      $env:ANTHARES_CONTROL_URL='https://anthares-remote-primary.vercel.app'
      Log('reserve transport selector unavailable; private queues preferred')
    }
    $env:ANTHARES_ALLOW_SHELL='1'
    $env:ANTHARES_WORK_ROOT='D:\AntharsWork'
    Start-Process -FilePath $reserve -WorkingDirectory $root -WindowStyle Hidden
    Log('reserve started')
  }catch{
    Log("reserve start failed: $($_.Exception.Message)")
  }finally{
    if($held -and $transition){try{$transition.ReleaseMutex()}catch{}}
    if($transition){$transition.Dispose()}
  }
}
function Write-State([string]$mode,[int]$primaryCount,[int]$reserveCount){
  try{
    [pscustomobject]@{
      updated_at=(Get-Date).ToUniversalTime().ToString('o')
      mode=$mode
      primary_count=$primaryCount
      reserve_count=$reserveCount
      grace_seconds=$graceSeconds
      primary_binary=(Split-Path $primary -Leaf)
      reserve_binary=(Split-Path $reserve -Leaf)
    }|ConvertTo-Json|Set-Content -LiteralPath $state -Encoding UTF8
  }catch{}
}

$created=$false
try{
  $mutex=New-Object System.Threading.Mutex(
    $true,
    'Global\AntharesRemoteFailoverArbiterV1',
    [ref]$created
  )
  if(-not $created){exit 0}
  Log('arbiter started')
  while($true){
    $p=@(Get-Primary)
    $r=@(Get-Reserve)
    if($p.Count -ge 1){
      $missingSince=$null
      if($r.Count -gt 0){
        Stop-Reserve 'primary healthy'
        Start-Sleep -Seconds 1
        $r=@(Get-Reserve)
      }
      Write-State 'primary' $p.Count $r.Count
    } else {
      if($null -eq $missingSince){
        $missingSince=[DateTimeOffset]::UtcNow
        Log('primary missing; grace timer started')
      }
      $age=([DateTimeOffset]::UtcNow-$missingSince).TotalSeconds
      if($age -ge $graceSeconds -and $r.Count -eq 0){
        Start-Reserve
        Start-Sleep -Seconds 3
        $r=@(Get-Reserve)
      }
      if($r.Count -gt 1){
        $keep=$r|Sort-Object ProcessId|Select-Object -First 1
        $r|Where-Object {$_.ProcessId -ne $keep.ProcessId}|
          ForEach-Object{
            try{
              Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }catch{}
          }
        $r=@(Get-Reserve)
      }
      Write-State $(if($r.Count -ge 1){'reserve'}else{'waiting'}) 0 $r.Count
    }
    Start-Sleep -Seconds $pollSeconds
  }
} finally {
  if($created -and $mutex){
    try{$mutex.ReleaseMutex()}catch{}
    $mutex.Dispose()
  }
}


