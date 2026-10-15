param(
    [string]$RuntimePath = "C:\ProgramData\AntharesRemoteAgent\android-runtime\anthares-android-runtime-v2.ps1",
    [ValidateSet('IDLE','LEASED','STARTED','COMMITTING','UNCERTAIN','VERIFIED')]
    [string]$PublicationState = 'IDLE'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $RuntimePath)) {
    $repoRuntime = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'windows\android-runtime\anthares-android-runtime.ps1'
    if (Test-Path $repoRuntime) {
        $RuntimePath = $repoRuntime
    } else {
        throw "Anthares Android Runtime missing: $RuntimePath"
    }
}

# The bridge intentionally owns no ADB path, MEmu port or VM transport details.
# Those belong to Anthares Android Runtime. Selection is fail-closed at the
# irreversible publication boundary.
& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $RuntimePath `
    -Command select `
    -Target auto `
    -PublicationState $PublicationState `
    -AllowBackendStart

exit $LASTEXITCODE
