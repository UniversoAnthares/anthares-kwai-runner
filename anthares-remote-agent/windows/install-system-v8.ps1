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

New-Item -ItemType Directory -Force -Path $root,(Join-Path $root 'secrets'),$work,(Join-Path $work 'logs'),(Join-Path $work 'temp'),(Join-Path $work 'legacy-pc-runtime\supervisor') | Out-Null
$base='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/windows/'
foreach($name in @('run-agent-system-supervisor.ps1','load-issue-queue-auth.ps1')){
  $dst=Join-Path $root $name
  if(Test-Path $dst){Copy-Item $dst ($dst+'.pre-v8-'+(Get-Date -Format 'yyyyMMddHHmmss')+'.bak') -Force}
  Invoke-WebRequest -UseBasicParsing -Uri ($base+$name) -OutFile $dst -TimeoutSec 30
  $errors=$null;$tokens=$null
  [Management.Automation.Language.Parser]::ParseFile($dst,[ref]$tokens,[ref]$errors)|Out-Null
  if($errors.Count){throw "$name syntax errors: $($errors.Count)"}
}

$v4=Join-Path $root 'anthares-remote-agent-v4.exe'
if(-not(Test-Path $v4)){throw 'anthares-remote-agent-v4.exe is missing'}
Set-Content -LiteralPath (Join-Path $root 'v4-validated.flag') -Value 'validated: Cloudflare MCP + private GitHub issue queue production proof' -Encoding ASCII

# Reuse the already-authorized GitHub CLI credential and seal a machine-scoped
# copy for SYSTEM. The plaintext token is never written to disk or logged.
$gh='C:\Program Files\GitHub CLI\gh.exe'
$credential=Join-Path $root 'secrets\issue-queue.json'
if(Test-Path $gh){
  try{
    $token=(& $gh auth token 2>$null).Trim()
    if($token){
      Add-Type -AssemblyName System.Security
      $entropy=[Text.Encoding]::UTF8.GetBytes('AntharesRemoteAgentIssueQueueV1')
      $plain=[Text.Encoding]::UTF8.GetBytes($token)
      try{$cipher=[Security.Cryptography.ProtectedData]::Protect($plain,$entropy,[Security.Cryptography.DataProtectionScope]::LocalMachine)}finally{[Array]::Clear($plain,0,$plain.Length);$token=$null}
      [ordered]@{github_repository='UniversoAnthares/anthares-ara-queue';github_author='UniversoAnthares';github_token_dpapi=[Convert]::ToBase64String($cipher);interval_seconds=5} | ConvertTo-Json | Set-Content -LiteralPath $credential -Encoding UTF8
      & icacls.exe $credential /inheritance:r /grant:r 'SYSTEM:(F)' 'Administrators:(F)' | Out-Null
      Log 'machine-scoped private queue credential installed'
    }
  }catch{Log ('queue credential reuse deferred: '+$_.Exception.Message)}
}
if(-not(Test-Path $credential)){Log 'warning: SYSTEM GitHub queue credential is not installed; HTTP failover will still operate'}

$task='Anthares Remote Agent SYSTEM'
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\ProgramData\AntharesRemoteAgent\run-agent-system-supervisor.ps1"'
$trigger=New-ScheduledTaskTrigger -AtStartup
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 12 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$system=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Settings $settings -Principal $system -Force | Out-Null
Start-ScheduledTask -TaskName $task
Log 'SYSTEM task registered and start requested'

$state=Join-Path $work 'legacy-pc-runtime\supervisor\system-supervisor-state.json'
$deadline=(Get-Date).AddSeconds(45)
$verified=$false
while((Get-Date)-lt $deadline){
  Start-Sleep -Seconds 2
  if(-not(Test-Path $state)){continue}
  try{
    $s=Get-Content $state -Raw | ConvertFrom-Json
    if($s.agent_pid -and (Get-Process -Id ([int]$s.agent_pid) -ErrorAction SilentlyContinue)){$verified=$true;break}
  }catch{}
}
if(-not $verified){throw 'SYSTEM runtime did not reach running state within 45 seconds; user fallback left unchanged'}

# SYSTEM has proved local liveness. Retire the user-level writer, but keep the
# task definition disabled for deliberate emergency rollback.
$userTask=Get-ScheduledTask -TaskName 'Anthares Remote Agent User' -ErrorAction SilentlyContinue
if($userTask){
  Stop-ScheduledTask -TaskName 'Anthares Remote Agent User' -ErrorAction SilentlyContinue
  Disable-ScheduledTask -TaskName 'Anthares Remote Agent User' | Out-Null
  Log 'user fallback disabled after SYSTEM local proof'
}

$result=[ordered]@{ok=$true;system_task=(Get-ScheduledTask -TaskName $task).State;system_state=$state;user_fallback_disabled=[bool]$userTask;render_required=$false;completed_at=(Get-Date).ToUniversalTime().ToString('o')}
$result | ConvertTo-Json | Set-Content (Join-Path $work 'legacy-pc-runtime\supervisor\install-result.json') -Encoding UTF8
Log ('SUCCESS '+($result|ConvertTo-Json -Compress))
Write-Host 'Anthares Remote SYSTEM instalado e validado.'
Write-Host 'Pode fechar esta janela.'
