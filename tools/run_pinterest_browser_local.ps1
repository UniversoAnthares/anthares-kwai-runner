# CORTES Pinterest UI publisher: isolated Chrome profile; never touches personal tabs.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$authLoader = 'C:\ProgramData\AntharesRemoteAgent\agent-env.ps1'
if (-not (Test-Path $authLoader)) { throw 'ANTHARES_DEVICE_AUTH_LOADER_MISSING' }
. $authLoader
$env:ANTHARES_DEVICE_ID = 'DESKTOP-FTDK0HP'
$env:ANTHARES_SOCIAL_COMMIT = '1'
$env:CORTES_PINTEREST_LOCAL_ENABLED = '1'
$env:CORTES_CHROME_CDP_PORT = '9226'
$env:CORTES_PINTEREST_NEON_URL = 'https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/'
$profile = 'D:\AntharsWork\browser-profiles\AntharesPinterest'
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
if (-not (Test-Path $chrome)) { throw 'PINTEREST_CHROME_MISSING' }
$version = $null
try {$version = Invoke-RestMethod 'http://127.0.0.1:9226/json/version' -TimeoutSec 3} catch {}
if (-not $version) {
  $other = @(Get-CimInstance Win32_Process -Filter "name='chrome.exe'" |
    Where-Object {$_.CommandLine -match 'remote-debugging-port=9226'})
  if ($other.Count -gt 0) { throw 'PINTEREST_CDP_PORT_BUSY_UNVERIFIED' }
  New-Item -ItemType Directory -Force -Path $profile | Out-Null
  $args = @('--headless=new', '--remote-debugging-port=9226', '--remote-debugging-address=127.0.0.1',
    '--user-data-dir=' + $profile, '--profile-directory=Default', '--no-first-run',
    '--no-default-browser-check', '--disable-sync', '--disable-notifications',
    '--mute-audio', '--disable-audio-output','about:blank')
  Start-Process -FilePath $chrome -ArgumentList $args -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 3
  try {$version = Invoke-RestMethod 'http://127.0.0.1:9226/json/version' -TimeoutSec 4} catch {}
}
if (-not $version -or $version.Browser -notmatch '^Chrome/') { throw 'PINTEREST_CDP_UNAVAILABLE' }
$running = @(Get-CimInstance Win32_Process -Filter "name='chrome.exe'" |
  Where-Object {$_.CommandLine -match 'remote-debugging-port=9226' -and
     $_.CommandLine -like '*AntharesPinterest*' -and $_.CommandLine -notmatch ' --type='})
if ($running.Count -ne 1) { throw 'PINTEREST_CDP_PROFILE_MISMATCH' }
$runner = Join-Path $root 'tools\cortes_pinterest_browser_local.py'
if (-not (Test-Path $runner)) { throw 'CORTES_PINTEREST_BROWSER_WORKER_MISSING' }
& py -3 $runner
exit $LASTEXITCODE
