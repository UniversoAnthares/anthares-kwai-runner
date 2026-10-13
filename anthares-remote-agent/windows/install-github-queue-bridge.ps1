# Installs the optional GitHub queue bridge without changing the existing ARA service.
# Run elevated only after provisioning a private repository and a read/write Issues token.
param(
  [Parameter(Mandatory=$true)][string]$Repository,
  [string]$ScriptPath = (Join-Path $PSScriptRoot 'github-queue-bridge.ps1'),
  [switch]$Start
)
$ErrorActionPreference = 'Stop'
if ($Repository -notmatch '^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$') { throw 'Invalid repository' }
if (-not (Test-Path $ScriptPath)) { throw 'Bridge script not found' }
if (-not $env:ANTHARES_GITHUB_QUEUE_TOKEN) { throw 'Set ANTHARES_GITHUB_QUEUE_TOKEN securely before installation' }
$headers = @{Authorization = "Bearer $env:ANTHARES_GITHUB_QUEUE_TOKEN"; Accept = 'application/vnd.github+json'; 'X-GitHub-Api-Version' = '2022-11-28'}
$info = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repository" -Headers $headers -TimeoutSec 15
if (-not $info.private) { throw 'Queue repository must be private' }
$dest = 'C:\ProgramData\AntharesRemoteAgent\github-queue-bridge.ps1'
New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
Copy-Item $ScriptPath $dest -Force
Write-Host "Bridge staged at $dest for private repository $Repository"
Write-Host 'No existing ARA service or supervisor was modified.'
if ($Start) {
  throw 'Automatic startup is intentionally disabled until credential persistence and end-to-end tests are validated.'
}
