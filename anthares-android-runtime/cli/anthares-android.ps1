param(
    [Parameter(Position=0)][ValidateSet('status','health','devices','backends','recover','start','stop','reset','foreground','launch','identity','ui','lease','release')][string]$Command='status',
    [switch]$AllowBackendReset,
    [string]$Owner='cli',
    [int]$TtlSeconds=120,
    [switch]$Pretty
)
$ErrorActionPreference='Stop'

# MEmuHyperv stores the canonical media registry under the desktop owner's profile.
# Anthares Remote executes as SYSTEM, so every MEmu operation must load that registry.
$env:USERPROFILE='C:\Users\Lucas'
$env:HOMEDRIVE='C:'
$env:HOMEPATH='\Users\Lucas'

$module=Join-Path $PSScriptRoot '..\src\AntharesAndroidRuntime.psm1'
Import-Module $module -Force

try {
    switch ($Command) {
        'status' { $result=Get-AntharesAndroidHealth }
        'health' { $result=Get-AntharesAndroidHealth }
        'devices' { $result=Get-AdbDevices }
        'backends' { $result=Get-MEmuInfo }
        'recover' { $result=Repair-AdbTransport -AllowBackendReset:$AllowBackendReset }
        'start' { $result=Start-MEmuBackend }
        'stop' { $result=Stop-MEmuBackend }
        'reset' { $result=Reset-MEmuBackend }
        'foreground' { $result=Get-ForegroundApp }
        'launch' { $result=Start-Kwai }
        'identity' { $result=Get-KwaiIdentitySignal }
        'ui' { $result=Get-UiDump }
        'lease' { $result=Acquire-DeviceLease -Owner $Owner -TtlSeconds $TtlSeconds }
        'release' { $result=Release-DeviceLease -Owner $Owner }
    }
    if ($Pretty) { $result | ConvertTo-Json -Depth 10 } else { $result | ConvertTo-Json -Depth 10 -Compress }
    if ($result.PSObject.Properties.Name -contains 'ok' -and -not $result.ok) { exit 2 }
    exit 0
} catch {
    [ordered]@{ok=$false;failure_class='ANTHARES_COMPONENT_FAILURE';error=$_.Exception.Message} | ConvertTo-Json -Compress
    exit 3
}
