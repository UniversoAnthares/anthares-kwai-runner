# Autonomous Pinterest media 24h + transcript metadata QA on existing Windows user.
# Device secrets remain in the private agent-env loader. Does not publish.
$ErrorActionPreference='Stop'
trap {
  $log=Join-Path (Split-Path -Parent $PSScriptRoot) 'qa-health\pinterest-qa-exit.log'
  $dir=Split-Path -Parent $log
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $row=@{at=(Get-Date).ToUniversalTime().ToString('o');component='pinterest-metadata-qa';exit_code=1;stage='bootstrap';failure=$_.Exception.GetType().Name;line=$_.InvocationInfo.ScriptLineNumber}
  Add-Content -LiteralPath $log -Value ($row|ConvertTo-Json -Compress) -Encoding UTF8
  exit 1
}
$root=Split-Path -Parent $PSScriptRoot
$loader='C:\ProgramData\AntharesRemoteAgent\agent-env.ps1'
if(-not(Test-Path $loader)){throw 'PINTEREST_QA_AGENT_AUTH_MISSING'}
. $loader
$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'
$env:CORTES_PINTEREST_NEON_URL='https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/'
$env:CORTES_CHROME_CDP_PORT='9226'
$cache='C:\Users\Lucas\.cache\huggingface'
if(Test-Path (Join-Path $cache 'hub\models--Systran--faster-whisper-small')){ $env:HF_HOME=$cache }
# Dedicated, pinned ASR runtime: PyAV 19 broke faster-whisper 1.2.1
# (av.open no longer accepts metadata_errors). Dependency install belongs
# to the installer, not to each scheduled worker invocation.
$qaDeps=Join-Path $root '.pinterest-qa-deps-v2'
foreach($part in @('faster_whisper\__init__.py','av\__init__.py','imageio_ffmpeg\__init__.py')){
  if(-not(Test-Path (Join-Path $qaDeps $part))){
    throw 'PINTEREST_QA_PINNED_ASR_DEPENDENCIES_MISSING'
  }
}
$env:PYTHONPATH=$qaDeps+[IO.Path]::PathSeparator+$env:PYTHONPATH
& py -3 -c "import av,faster_whisper,imageio_ffmpeg; assert av.__version__ == '17.1.0'"
if($LASTEXITCODE -ne 0){ throw 'PINTEREST_QA_PYAV_ABI_MISMATCH' }
$worker=Join-Path $root 'tools\cortes_pinterest_metadata_qa.py'
if(-not(Test-Path $worker)){throw 'PINTEREST_QA_WORKER_MISSING'}
$diagDir=Join-Path $root 'qa-health'
New-Item -ItemType Directory -Force -Path $diagDir | Out-Null
$diagFile=Join-Path $diagDir 'pinterest-qa-exit.log'
& py -3 $worker --max-clips 3
$qaExit=$LASTEXITCODE
$event=@{at=(Get-Date).ToUniversalTime().ToString('o');component='pinterest-metadata-qa';exit_code=$qaExit}
Add-Content -LiteralPath $diagFile -Value ($event | ConvertTo-Json -Compress) -Encoding UTF8
exit $qaExit
