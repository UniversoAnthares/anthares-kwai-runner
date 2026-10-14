$ErrorActionPreference='SilentlyContinue'
# Retired by Phase 4. A second HTTP/user-session supervisor violates the
# single-writer SYSTEM/session-0 invariant and can resurrect legacy control.
# Canonical recovery is recovery-watchdog-loop.ps1 -> recovery-watchdog.ps1.
$root='C:\ProgramData\AntharesRemoteAgent'
$state='D:\AntharsWork\legacy-pc-runtime\supervisor\dual-supervisor-retired.json'
try{
  New-Item -ItemType Directory -Force -Path (Split-Path $state) | Out-Null
  [pscustomobject]@{
    retired=$true
    replacement=(Join-Path $root 'recovery-watchdog-loop.ps1')
    canonical_executor='SYSTEM/session-0'
    canonical_transport='private-issue-queues'
    render_required=$false
    updated_at=(Get-Date).ToUniversalTime().ToString('o')
  } | ConvertTo-Json | Set-Content -Path $state -Encoding UTF8
}catch{}
exit 0
