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
$cache='C:\Users\Lucas\.cache\huggingface'
if(Test-Path (Join-Path $cache 'hub\models--Systran--faster-whisper-small')){ $env:HF_HOME=$cache }
# Keep ASR wheels isolated from other CORTES publishers and system Python.
$qaDeps=Join-Path $root '.pinterest-qa-deps'
$hasASR=(Test-Path (Join-Path $qaDeps 'faster_whisper\__init__.py'))
$hasFFmpeg=(Test-Path (Join-Path $qaDeps 'imageio_ffmpeg\__init__.py'))
if(-not ($hasASR -and $hasFFmpeg)){
  New-Item -ItemType Directory -Force -Path $qaDeps | Out-Null
  $ErrorActionPreference='Continue'
  & py -3 -m pip install --no-input --disable-pip-version-check --prefer-binary --target $qaDeps faster-whisper==1.2.1 imageio-ffmpeg==0.6.0 2>&1 | Out-Null
  $result=$LASTEXITCODE
  $ErrorActionPreference='Stop'
  if($result -ne 0){ throw 'PINTEREST_QA_ASR_DEPENDENCIES_UNAVAILABLE' }
}
$env:PYTHONPATH=$qaDeps+[IO.Path]::PathSeparator+$env:PYTHONPATH
$worker=Join-Path $root 'tools\cortes_pinterest_metadata_qa.py'
if(-not(Test-Path $worker)){throw 'PINTEREST_QA_WORKER_MISSING'}
& py -3 $worker --max-clips 3
exit $LASTEXITCODE
