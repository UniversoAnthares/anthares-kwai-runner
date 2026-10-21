param(
 [string]$RuntimeRoot='D:\AntharsWork\cortes-social-browser-20261020',
 [string]$RepoRoot=''
)
$ErrorActionPreference='Stop'
$source=if($RepoRoot){Join-Path $RepoRoot 'tools\threads_cloud_local_gate.mjs'}else{'https://raw.githubusercontent.com/UniversoAnthares/anthares-kwai-runner/main/tools/threads_cloud_local_gate.mjs'}
$destination=Join-Path $RuntimeRoot 'threads_cloud_local_gate.mjs'
$staged=$destination+'.staged.mjs'
if($RepoRoot){Copy-Item $source $staged -Force}else{Invoke-WebRequest -UseBasicParsing $source -OutFile $staged -TimeoutSec 25}
$node='C:\Program Files\nodejs\node.exe'
& $node --check $staged
if($LASTEXITCODE -ne 0){throw 'LOCAL_GATE_SYNTAX_INVALID'}
if(Test-Path $destination){Copy-Item $destination ($destination+'.before-cloud-gate.bak') -Force}
Move-Item -Force $staged $destination
$script=Join-Path $RuntimeRoot 'auto-threads.ps1'
if(!(Test-Path $script)){throw 'LOCAL_PUBLISHER_SCHEDULER_MISSING'}
$before=$script+'.before-cloud-gate.bak'
if(!(Test-Path $before)){Copy-Item $script $before -Force}
$content=[IO.File]::ReadAllText($script)
$anchor=" if("+'$gateCode'+" -ne 0){Record ('LOCAL_STANDBY_GATE_ERROR='+"+'$gateCode'+");exit 2}"
if(!$content.Contains('CLOUD_HANDOFF_GUARD')){
 if(!$content.Contains($anchor)){throw 'LOCAL_PUBLISHER_ANCHOR_CHANGED'}
 $addition=@'
 # CLOUD_HANDOFF_GUARD: reconcile cloud evidence before local publication.
 $cloudGate=Join-Path $root 'threads_cloud_local_gate.mjs'
 if(!(Test-Path $cloudGate)){Record 'CLOUD_HANDOFF_GUARD_MISSING';exit 2}
 $cloudOutput=@(& 'C:\Program Files\nodejs\node.exe' $cloudGate 2>&1)
 $cloudCode=$LASTEXITCODE
 foreach($line in $cloudOutput){Record ('CLOUD_HANDOFF_GUARD '+[string]$line)}
 if($cloudCode -eq 20){Record 'CLOUD_HANDOFF_RESERVED_LOCAL_WAIT';exit 0}
 if($cloudCode -ne 0){Record ('CLOUD_HANDOFF_GUARD_FAILED='+$cloudCode);exit 2}
'@
 $candidate=$script+'.cloud-gate-tmp'
 [IO.File]::WriteAllText($candidate,$content.Replace($anchor,$anchor+[Environment]::NewLine+$addition),(New-Object System.Text.UTF8Encoding($false)))
 $tokens=$null;$errors=$null
 [System.Management.Automation.Language.Parser]::ParseFile($candidate,[ref]$tokens,[ref]$errors)|Out-Null
 if($errors.Count){Remove-Item $candidate -Force;throw 'SCHEDULER_SYNTAX_INVALID'}
 Move-Item -Force $candidate $script
}
& $node $destination
if($LASTEXITCODE -ne 0){throw 'LOCAL_GATE_INITIAL_STATUS_FAILED'}
Write-Output 'THREADS_CLOUD_GATE_INSTALLED=1'
