$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$module=Join-Path $root 'src\AntharesAndroidRuntime.psm1'
$cli=Join-Path $root 'cli\anthares-android.ps1'
$watchdog=Join-Path $root 'watchdog\anthares-android-watchdog.ps1'

function Assert($Condition,[string]$Message){ if(-not $Condition){ throw $Message } }

Assert (Test-Path $module) 'module missing'
Assert (Test-Path $cli) 'cli missing'
Assert (Test-Path $watchdog) 'watchdog missing'

$moduleText=Get-Content $module -Raw
$cliText=Get-Content $cli -Raw
$watchdogText=Get-Content $watchdog -Raw

foreach($name in @('Get-AntharesAndroidHealth','Repair-AdbTransport','Get-KwaiIdentitySignal','Acquire-DeviceLease','Release-DeviceLease')){
    Assert ($moduleText -match [regex]::Escape($name)) ("missing function: "+$name)
}
foreach($state in @('RUNNING_TRANSPORT_OFFLINE','TRANSPORT_UNAUTHORIZED','ANDROID_BOOTING','APP_MISSING','ANDROID_READY','RECOVERY_EXHAUSTED')){
    Assert ($moduleText -match [regex]::Escape($state)) ("missing state/failure class: "+$state)
}
Assert ($moduleText -match "audio") 'audio state missing'
Assert ($moduleText -match '127\\.0\\.0\\.1') 'ADB endpoint discovery missing'
Assert ($cliText -match "USERPROFILE='C:\\\\Users\\\\Lucas'") 'canonical MEmu profile missing from CLI'
Assert ($watchdogText -match "USERPROFILE='C:\\\\Users\\\\Lucas'") 'canonical MEmu profile missing from watchdog'
Assert ($watchdogText -match 'activeLease') 'watchdog must respect active device lease'
Assert ($watchdogText -match 'BackoffMaxSeconds') 'watchdog backoff missing'

Write-Output '{"ok":true,"suite":"runtime-contract"}'
