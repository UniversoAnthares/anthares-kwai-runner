# Install a non-secret local auth reference for the cloud Threads worker.
# This never reads/exports browser cookies, OAuth tokens, or refresh tokens.
param([string]$Root='D:\AntharsWork\cortes-social-browser-20261020')
$ErrorActionPreference='Stop'
$base='https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/'
$node='C:\Program Files\nodejs\node.exe'
if(!(Test-Path $node)){throw 'NODE_NOT_INSTALLED'}
$src=Join-Path $Root 'tools'
$cfg=Join-Path $Root 'config'
New-Item -ItemType Directory -Path $src,$cfg -Force|Out-Null
$script=Join-Path $src 'threads_cloud_auth_reference.mjs'
$manifest=Join-Path $cfg 'threads-cloud-auth-reference.json'
Invoke-WebRequest -UseBasicParsing ($base+'tools/threads_cloud_auth_reference.mjs') -OutFile ($script+'.new') -TimeoutSec 25
Invoke-WebRequest -UseBasicParsing ($base+'config/threads-cloud-auth-reference.json') -OutFile ($manifest+'.new') -TimeoutSec 25
& $node --check ($script+'.new')
if($LASTEXITCODE -ne 0){throw 'AUTH_REFERENCE_SCRIPT_SYNTAX_FAILED'}
$policy=Get-Content ($manifest+'.new') -Raw|ConvertFrom-Json
if($policy.schema -ne 'anthares.threads.auth-reference.v1' -or
   $policy.copy_browser_cookies -ne $false -or $policy.copy_access_token_to_folder -ne $false){
 throw 'AUTH_REFERENCE_POLICY_INVALID'
}
Move-Item -Force ($script+'.new') $script
Move-Item -Force ($manifest+'.new') $manifest
$task='Anthares CORTES Threads Cloud Auth Reference'
$action=New-ScheduledTaskAction -Execute $node -Argument ('"'+$script+'" --write') -WorkingDirectory $Root
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(3) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
Register-ScheduledTask -TaskName $task -User SYSTEM -RunLevel Highest -Action $action -Trigger $trigger -Settings $settings -Force|Out-Null
$folder=Join-Path $Root 'auth-references'
New-Item -ItemType Directory -Path $folder -Force|Out-Null
& icacls.exe $folder '/inheritance:r' '/grant:r' '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
if($LASTEXITCODE -ne 0){throw 'AUTH_REFERENCE_ACL_FAILED'}
& $node $script --write | Out-Null
if($LASTEXITCODE -ne 0){throw 'AUTH_REFERENCE_INITIAL_WRITE_FAILED'}
$data=Get-Content (Join-Path $folder 'threads-cloud-reference.json') -Raw|ConvertFrom-Json
if($data.credential_value_present -ne $false -or $data.browser_cookies_present -ne $false -or
   $data.account -ne 'universoanthares'){throw 'AUTH_REFERENCE_AUDIT_FAILED'}
Write-Output ('THREADS_REFERENCE_INSTALLED=true;TASK='+$task+';LOCAL_COUNT='+$data.local_confirmed_count)
