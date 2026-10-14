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
  Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'))
  exit 0
}
Log ('elevated identity='+$identity.Name)

New-Item -ItemType Directory -Force -Path $root,$work,(Join-Path $work 'logs'),(Join-Path $work 'temp'),(Join-Path $work 'ara-jobs'),(Join-Path $work 'legacy-pc-runtime\supervisor') | Out-Null
$base='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/anthares-remote-agent/windows/'
$critical=@('run-agent-system-supervisor.ps1','load-issue-queue-auth.ps1','recovery-watchdog.ps1','recovery-watchdog-loop.ps1')
$scriptHashes=[ordered]@{}
foreach($name in $critical){
  $dst=Join-Path $root $name
  if(Test-Path $dst){Copy-Item $dst ($dst+'.pre-v8-'+(Get-Date -Format 'yyyyMMddHHmmss')+'.bak') -Force}
  Invoke-WebRequest -UseBasicParsing -Uri ($base+$name) -OutFile $dst -TimeoutSec 30
  $errors=$null;$tokens=$null
  [Management.Automation.Language.Parser]::ParseFile($dst,[ref]$tokens,[ref]$errors)|Out-Null
  if($errors.Count){throw "$name syntax errors: $($errors.Count)"}
  Copy-Item $dst ($dst+'.lastgood') -Force
  $scriptHashes[$name]=(Get-FileHash $dst -Algorithm SHA256).Hash
}

$v4=Join-Path $root 'anthares-remote-agent-v4.exe'
if(-not(Test-Path $v4)){throw 'anthares-remote-agent-v4.exe is missing'}
$v4Hash=(Get-FileHash $v4 -Algorithm SHA256).Hash
Copy-Item $v4 (Join-Path $root 'anthares-remote-agent-v4.lastgood.exe') -Force
[ordered]@{v4_sha256=$v4Hash;script_sha256=$scriptHashes;updated_at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $root 'integrity-baseline.json') -Encoding UTF8
Set-Content -LiteralPath (Join-Path $root 'v4-validated.flag') -Value ('validated sha256='+$v4Hash) -Encoding ASCII
Log ('V4 pinned sha256='+$v4Hash)

$credential=Join-Path $root 'secrets\issue-queue.json'
if(-not(Test-Path $credential)){throw 'existing SYSTEM private queue credential is missing'}
$loader=Join-Path $root 'load-issue-queue-auth.ps1'
Remove-Item Env:ANTHARES_GITHUB_QUEUE_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_GITHUB_QUEUE_REPOSITORY -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_GITLAB_QUEUE_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:ANTHARES_GITLAB_QUEUE_PROJECT -ErrorAction SilentlyContinue
. $loader
$queueReady=(((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY))) -or ((-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN))-and(-not [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT))))
if(-not $queueReady){throw 'SYSTEM private queue credential exists but could not be loaded'}
if([string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN) -or [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY)){throw 'GitHub private queue is required for Phase 4 end-to-end cutover proof'}
Log 'private queue credential validated without exposing token'

function Register-SystemTask([string]$name,[string]$script){
  $action=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$script+'"') -WorkingDirectory $root
  $trigger=New-ScheduledTaskTrigger -AtStartup
  $settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
  $system=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
  Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $system -Force | Out-Null
}

function Invoke-GitHubQueueProof {
  $repo=[string]$env:ANTHARES_GITHUB_QUEUE_REPOSITORY
  $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
  if($repo -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'){throw 'invalid GitHub queue repository for proof'}
  $headers=@{Authorization=('Bearer '+$token);Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28';'User-Agent'='AntharesRemoteAgent-Phase4-Installer'}
  $jobId='ara-install-health-'+(Get-Date -Format 'yyyyMMddHHmmss')
  $job=[ordered]@{job_id=$jobId;device_id='DESKTOP-FTDK0HP';type='agent_health';args=@{};timeout_seconds=15}
  $issuePayload=[ordered]@{title=('ARA Phase 4 install proof '+$jobId);body=($job|ConvertTo-Json -Compress -Depth 6);labels=@('ara-queued')}
  $issue=Invoke-RestMethod -Method Post -Uri ('https://api.github.com/repos/'+$repo+'/issues') -Headers $headers -ContentType 'application/json' -Body ($issuePayload|ConvertTo-Json -Depth 6) -TimeoutSec 20
  $number=[int]$issue.number
  if($number -le 0){throw 'GitHub queue proof issue creation failed'}
  Log ('queue proof submitted issue='+$number+' job='+$jobId)
  $deadline=(Get-Date).AddSeconds(90)
  try{
    while((Get-Date)-lt $deadline){
      Start-Sleep -Seconds 3
      $comments=@(Invoke-RestMethod -Method Get -Uri ('https://api.github.com/repos/'+$repo+'/issues/'+$number+'/comments?per_page=30') -Headers $headers -TimeoutSec 20)
      foreach($comment in $comments){
        $body=[string]$comment.body
        if($body -notmatch '^ARA_RESULT_B64 part=1/1\s+([A-Za-z0-9+/=]+)\s*$'){continue}
        $decoded=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Matches[1]))
        $remoteResult=$decoded|ConvertFrom-Json
        if([string]$remoteResult.id -ne $jobId){continue}
        if(-not [bool]$remoteResult.ok){throw ('queue proof command failed: '+[string]$remoteResult.error)}
        $health=([string]$remoteResult.output)|ConvertFrom-Json
        if(-not [bool]$health.ok -or -not [bool]$health.queue_configured){throw 'agent_health proof returned unhealthy queue configuration'}
        if(-not [bool]$health.http_control){throw 'agent_health proof returned MCP HTTP transport disabled'}
        if([string]$health.device_id -ne 'DESKTOP-FTDK0HP'){throw 'agent_health proof returned wrong device'}
        return [pscustomobject]@{ok=$true;issue=$number;job_id=$jobId;agent_pid=[int]$health.pid;queue_providers=@($health.queue_providers);http_control=[bool]$health.http_control}
      }
    }
    throw 'GitHub queue proof timed out without ARA_RESULT_B64 response'
  }finally{
    try{Invoke-RestMethod -Method Patch -Uri ('https://api.github.com/repos/'+$repo+'/issues/'+$number) -Headers $headers -ContentType 'application/json' -Body '{"state":"closed"}' -TimeoutSec 15|Out-Null}catch{}
  }
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

$proof=Invoke-GitHubQueueProof
if(-not $proof.ok){throw 'Phase 4 queue proof failed; legacy transport left intact'}
Log ('dual-transport proof passed issue='+$proof.issue+' job='+$proof.job_id+' pid='+$proof.agent_pid)

foreach($oldTask in @('Anthares Remote Agent User','Anthares-GitHub-Queue-Bridge')){try{Disable-ScheduledTask -TaskName $oldTask -ErrorAction SilentlyContinue|Out-Null}catch{}}
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -ne 0 -and $_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'}|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}catch{}}

$result=[ordered]@{ok=$true;install_root=$root;work_root=$work;v4_sha256=$v4Hash;system_v4_pid=$agentPid;system_task=(Get-ScheduledTask -TaskName $canonicalTask).State;watchdog_task=(Get-ScheduledTask -TaskName $watchdogTask).State;system_state=$state;queue_credential_validated=$true;queue_end_to_end_proof=$true;mcp_http_transport_configured=$true;queue_proof_issue=$proof.issue;queue_proof_job_id=$proof.job_id;queue_providers=$proof.queue_providers;single_executor_enforced=$true;legacy_preserved_until_queue_proof=$false;jobs_path_migration_performed=$false;render_required=$false;completed_at=(Get-Date).ToUniversalTime().ToString('o')}
$result | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $work 'legacy-pc-runtime\supervisor\install-result.json') -Encoding UTF8
Log ('SUCCESS '+($result|ConvertTo-Json -Compress -Depth 5))
