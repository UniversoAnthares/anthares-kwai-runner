$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$work='D:\AntharsWork'
$log=Join-Path $work 'logs\install-system-v8.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
function Log([string]$m){"$(Get-Date -Format o) $m" | Tee-Object -FilePath $log -Append}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=[Security.Principal.WindowsPrincipal]::new($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
  Log 'requesting elevation'
  Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'))
  exit 0
}
Log ('elevated identity='+$identity.Name)

New-Item -ItemType Directory -Force -Path $root,$work,(Join-Path $work 'logs'),(Join-Path $work 'temp'),(Join-Path $work 'legacy-pc-runtime\supervisor') | Out-Null
$base='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/windows/'
foreach($name in @('run-agent-system-supervisor.ps1','load-issue-queue-auth.ps1','recovery-watchdog.ps1','recovery-watchdog-loop.ps1')){
  $dst=Join-Path $root $name
  if(Test-Path $dst){Copy-Item $dst ($dst+'.pre-v8-'+(Get-Date -Format 'yyyyMMddHHmmss')+'.bak') -Force}
  Invoke-WebRequest -UseBasicParsing -Uri ($base+$name) -OutFile $dst -TimeoutSec 30
  $errors=$null;$tokens=$null
  [Management.Automation.Language.Parser]::ParseFile($dst,[ref]$tokens,[ref]$errors)|Out-Null
  if($errors.Count){throw "$name syntax errors: $($errors.Count)"}
}

$v4=Join-Path $root 'anthares-remote-agent-v4.exe'
if(-not(Test-Path $v4)){throw 'anthares-remote-agent-v4.exe is missing'}
$v4Hash=(Get-FileHash $v4 -Algorithm SHA256).Hash
Copy-Item $v4 (Join-Path $root 'anthares-remote-agent-v4.lastgood.exe') -Force
[ordered]@{v4_sha256=$v4Hash;updated_at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content (Join-Path $root 'integrity-baseline.json') -Encoding UTF8
Set-Content -LiteralPath (Join-Path $root 'v4-validated.flag') -Value ('validated sha256='+$v4Hash) -Encoding ASCII
Log ('V4 pinned sha256='+$v4Hash)

$credential=Join-Path $root 'secrets\issue-queue.json'
if(-not(Test-Path $credential)){throw 'existing SYSTEM private queue credential is missing'}

function Register-SystemTask([string]$name,[string]$script){
  $action=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$script+'"') -WorkingDirectory $root
  $trigger=New-ScheduledTaskTrigger -AtStartup
  $settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
  $system=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
  Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $system -Force | Out-Null
}

$canonicalTask='Anthares Remote Agent SYSTEM'
$watchdogTask='Anthares Remote Recovery Watchdog'
Register-SystemTask $canonicalTask (Join-Path $root 'run-agent-system-supervisor.ps1')
Register-SystemTask $watchdogTask (Join-Path $root 'recovery-watchdog-loop.ps1')
Stop-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue
Stop-ScheduledTask -TaskName $watchdogTask -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName $canonicalTask
Start-ScheduledTask -TaskName $watchdogTask
Log 'SYSTEM supervisor and watchdog registered and started'

$state=Join-Path $work 'legacy-pc-runtime\supervisor\system-supervisor-state.json'
$deadline=(Get-Date).AddSeconds(60)
$verified=$false
$agentPid=0
while((Get-Date)-lt $deadline){
  Start-Sleep -Seconds 2
  $agents=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq 0 -and $_.Name -eq 'anthares-remote-agent-v4.exe'})
  if($agents.Count -gt 0){$agentPid=[int]$agents[0].ProcessId;$verified=$true;break}
}
if(-not $verified){throw 'V4 SYSTEM runtime did not reach session 0 within 60 seconds; legacy transport left intact'}

$result=[ordered]@{ok=$true;v4_sha256=$v4Hash;system_v4_pid=$agentPid;system_task=(Get-ScheduledTask -TaskName $canonicalTask).State;watchdog_task=(Get-ScheduledTask -TaskName $watchdogTask).State;system_state=$state;legacy_preserved_until_queue_proof=$true;jobs_path_migration_performed=$false;render_required=$false;completed_at=(Get-Date).ToUniversalTime().ToString('o')}
$result | ConvertTo-Json | Set-Content (Join-Path $work 'legacy-pc-runtime\supervisor\install-result.json') -Encoding UTF8
Log ('SUCCESS '+($result|ConvertTo-Json -Compress))
Write-Host 'Anthares Remote V4 SYSTEM instalado e validado localmente.'
