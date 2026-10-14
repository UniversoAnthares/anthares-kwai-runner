param(
    [string]$RepoRoot = "D:\AntharesWork\anthares-kwai-runner",
    [string]$PhysicalSerial = "993fce720408",
    [string]$MEmuSerial = "127.0.0.1:21503",
    [string]$AdbPath = "D:\Program Files\Microvirt\MEmu\adb.exe"
)

$ErrorActionPreference = 'Stop'

$router = Join-Path $RepoRoot 'tools\android_executor_router.py'
$probe  = Join-Path $RepoRoot 'tools\android_device_adapters.py'
if (-not (Test-Path $router)) { throw "Canonical router missing: $router" }
if (-not (Test-Path $probe))  { throw "Device adapter missing: $probe" }
if (-not (Test-Path $AdbPath)) { throw "ADB missing: $AdbPath" }

$env:ANTHARES_ADB = $AdbPath
$env:ANTHARES_PHYSICAL_ADB_SERIAL = $PhysicalSerial
$env:ANTHARES_PHYSICAL_KWAI_PACKAGE = 'kwai.lite.video'
$env:ANTHARES_MEMU_ADB_SERIAL = $MEmuSerial
$env:ANTHARES_MEMU_KWAI_PACKAGE = 'com.kwai.video'

# Authentication remains fail-closed. These flags are intentionally not invented
# here. A session/identity probe must set them to 1 only after proving the expected
# Kwai account on each executor.

$python = (Get-Command python -ErrorAction Stop).Source
$statusJson = & $python $probe
if ($LASTEXITCODE -ne 0) { throw 'Android device probe failed' }

$env:ANTHARES_EXECUTOR_STATUS_JSON = $statusJson
$env:ANTHARES_EXECUTOR_WORKLOAD = 'kwai_publish'
& $python $router
exit $LASTEXITCODE
