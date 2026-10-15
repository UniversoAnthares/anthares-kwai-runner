$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$supervisor=Join-Path $root 'run-agent-system-supervisor.ps1'
$envFile=Join-Path $root 'agent-env.ps1'
$stateDir='D:\AntharsWork\legacy-pc-runtime\supervisor'
$modeFile=Join-Path $stateDir 'transport-mode.json'
if(-not (Test-Path $supervisor)){throw 'supervisor script missing'}
if(-not (Test-Path $envFile)){throw 'agent env file missing'}

# Persist the routing decision without exposing or deleting existing credentials.
$envText=Get-Content -LiteralPath $envFile -Raw
$modeLine='$env:ANTHARES_PRIMARY_TRANSPORT=''gitlab_issue_queue'''
if($envText -match '(?m)^\$env:ANTHARES_PRIMARY_TRANSPORT=.*$'){
  $envText=[regex]::Replace($envText,'(?m)^\$env:ANTHARES_PRIMARY_TRANSPORT=.*$',$modeLine)
}else{
  $envText=$envText.TrimEnd()+"`r`n"+$modeLine+"`r`n"
}
Set-Content -LiteralPath $envFile -Value $envText -Encoding UTF8

# Make the supervisor honor queue-primary mode while preserving the Cloudflare token in agent-env.ps1.
$s=Get-Content -LiteralPath $supervisor -Raw
$needle="$httpControl='https://anthares-ara-backup.anthares1.workers.dev'"
$insert=@"
`$httpControl='https://anthares-ara-backup.anthares1.workers.dev'
# Queue-primary emergency routing. Cloudflare credentials remain on disk but HTTP is disabled unless mode is changed.
if(`$env:ANTHARES_PRIMARY_TRANSPORT -eq 'gitlab_issue_queue'){
  Remove-Item Env:ANTHARES_DEVICE_TOKEN -ErrorAction SilentlyContinue
}
"@
if($s -notmatch "Queue-primary emergency routing"){
  if(-not $s.Contains($needle)){throw 'http control anchor not found'}
  $s=$s.Replace($needle,$insert.TrimEnd())
  Set-Content -LiteralPath $supervisor -Value $s -Encoding UTF8
}

New-Item -ItemType Directory -Force -Path $stateDir|Out-Null
[pscustomobject]@{
  primary='gitlab_private_issue_queue'
  secondary='github_private_issue_queue'
  tertiary='cloudflare_http_control'
  cloudflare_http_active=$false
  applied_at=(Get-Date).ToUniversalTime().ToString('o')
  reboot_required_for_supervisor_reload=$true
}|ConvertTo-Json -Depth 3|Set-Content -LiteralPath $modeFile -Encoding UTF8

$task=Get-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -ErrorAction Stop
[pscustomobject]@{
  ok=$true
  task=$task.TaskName
  state=[string]$task.State
  enabled=[bool]$task.Settings.Enabled
  principal=$task.Principal.UserId
  transport_mode='gitlab_private_issue_queue'
  github_redundancy='configured_by_existing_agent_credentials'
  cloudflare='tertiary_disabled_until_reenabled'
  mode_file=$modeFile
}|ConvertTo-Json -Compress
