$ErrorActionPreference='Continue'
$root='C:\ProgramData\AntharesRemoteAgent'
$log=Join-Path $root 'recovery-watchdog.log'
$state=Join-Path $root 'recovery-watchdog-state.json'
$canonicalTask='Anthares Remote Agent SYSTEM'

function Log([string]$m){ try{"$(Get-Date -Format o) $m" | Add-Content -Path $log -Encoding UTF8}catch{} }
function Get-AuxServices {
  @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match 'meshagent|meshcentral|winremote' -or $_.DisplayName -match 'mesh agent|meshcentral|winremote' -or $_.PathName -match 'meshagent|meshcentral|winremote'
  })
}
function Repair-Service($svc){
  try{
    if($svc.StartMode -eq 'Disabled'){ sc.exe config $svc.Name start= auto | Out-Null }
    sc.exe failure $svc.Name reset= 86400 actions= restart/5000/restart/15000/restart/30000 | Out-Null
    sc.exe failureflag $svc.Name 1 | Out-Null
    $fresh=Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if($fresh -and $fresh.Status -ne 'Running'){ Start-Service -Name $svc.Name -ErrorAction SilentlyContinue; Log("restarted auxiliary service $($svc.Name)") }
  }catch{ Log("aux repair failed $($svc.Name): $($_.Exception.GetType().Name)") }
}

$systemAgents=@(Get-Process -Name 'anthares-remote-agent-v4','anthares-remote-agent' -ErrorAction SilentlyContinue | Where-Object {$_.SessionId -eq 0})
$task=Get-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue
if($task){
  if($systemAgents.Count -eq 0 -or $task.State -ne 'Running'){
    try{ Start-ScheduledTask -TaskName $canonicalTask -ErrorAction Stop; Log('started canonical SYSTEM task') }catch{ Log("canonical task start failed: $($_.Exception.GetType().Name)") }
  }
}else{ Log('canonical SYSTEM task missing') }

$aux=Get-AuxServices
foreach($svc in $aux){ Repair-Service $svc }

try{
  [pscustomobject]@{
    updated_at=(Get-Date).ToUniversalTime().ToString('o')
    canonical_task_present=[bool]$task
    canonical_task_state=if($task){[string]$task.State}else{'missing'}
    system_agent_count=$systemAgents.Count
    auxiliary_services=@($aux | ForEach-Object {$_.Name})
    role='canonical-root-recovery'
  } | ConvertTo-Json -Depth 4 | Set-Content -Path $state -Encoding UTF8
}catch{}
