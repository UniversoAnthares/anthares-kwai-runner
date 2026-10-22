# Autonomous Pinterest media 24h + transcript metadata QA on existing Windows user.
# Device secrets remain in the private agent-env loader. Does not publish.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$loader='C:\ProgramData\AntharesRemoteAgent\agent-env.ps1'
if(-not(Test-Path $loader)){throw 'PINTEREST_QA_AGENT_AUTH_MISSING'}
. $loader
$env:ANTHARES_DEVICE_ID='DESKTOP-FTDK0HP'
$env:CORTES_PINTEREST_NEON_URL='https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/'
$env:CORTES_CHROME_CDP_PORT='9226'
# Keep ASR wheels isolated from other CORTES publishers and system Python.
$qaDeps=Join-Path $root '.pinterest-qa-deps'
if(Test-Path (Join-Path $qaDeps 'faster_whisper\__init__.py')){
  $env:PYTHONPATH=$qaDeps+[IO.Path]::PathSeparator+$env:PYTHONPATH
}
$worker=Join-Path $root 'tools\cortes_pinterest_metadata_qa.py'
if(-not(Test-Path $worker)){throw 'PINTEREST_QA_WORKER_MISSING'}
& py -3 $worker --max-clips 3
exit $LASTEXITCODE
