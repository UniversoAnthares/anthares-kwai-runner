# CORTES Pinterest browser channel. No Pinterest API credentials are loaded.
# Reuse the already authorized Anthares device identity without printing secrets.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$authLoader = 'C:\ProgramData\AntharesRemoteAgent\agent-env.ps1'
if (-not (Test-Path $authLoader)) { throw 'ANTHARES_DEVICE_AUTH_LOADER_MISSING' }
. $authLoader
$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP'
$env:ANTHARES_SOCIAL_COMMIT = '1'
$env:CORTES_PINTEREST_LOCAL_ENABLED = '1'
$env:CORTES_CHROME_CDP_PORT = '9225'
$env:CORTES_QUEUE_URL = 'https://anthares-remote-primary.vercel.app/api/cortes-queue'
$runner = Join-Path $root 'tools\cortes_pinterest_browser_local.py'
if (-not (Test-Path $runner)) { throw 'CORTES_PINTEREST_BROWSER_WORKER_MISSING' }
& py -3 $runner
exit $LASTEXITCODE
