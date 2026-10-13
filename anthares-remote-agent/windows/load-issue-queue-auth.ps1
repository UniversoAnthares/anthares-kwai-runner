# Loads issue-queue credentials into this process without printing secrets.
# Secrets are protected with Windows DPAPI LocalMachine so the SYSTEM service
# can decrypt credentials provisioned by an administrator on the same machine.
$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\AntharesRemoteAgent\secrets'
$configPath = Join-Path $root 'issue-queue.json'
if (-not (Test-Path $configPath)) { return }

function Unprotect-ARASecret([string]$encoded) {
    if ([string]::IsNullOrWhiteSpace($encoded)) { return '' }
    $entropy = [Text.Encoding]::UTF8.GetBytes('AntharesRemoteAgentIssueQueueV1')
    $cipher = [Convert]::FromBase64String($encoded)
    $plain = [Security.Cryptography.ProtectedData]::Unprotect(
        $cipher,
        $entropy,
        [Security.Cryptography.DataProtectionScope]::LocalMachine
    )
    try { return [Text.Encoding]::UTF8.GetString($plain) }
    finally { [Array]::Clear($plain, 0, $plain.Length) }
}

$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($config.github_repository -and [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_REPOSITORY)) {
    $env:ANTHARES_GITHUB_QUEUE_REPOSITORY = [string]$config.github_repository
}
if ($config.github_author -and [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_AUTHOR)) {
    $env:ANTHARES_GITHUB_QUEUE_AUTHOR = [string]$config.github_author
}
if ($config.github_token_dpapi -and [string]::IsNullOrWhiteSpace($env:ANTHARES_GITHUB_QUEUE_TOKEN)) {
    $env:ANTHARES_GITHUB_QUEUE_TOKEN = Unprotect-ARASecret ([string]$config.github_token_dpapi)
}
if ($config.gitlab_project -and [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_PROJECT)) {
    $env:ANTHARES_GITLAB_QUEUE_PROJECT = [string]$config.gitlab_project
}
if ($config.gitlab_author -and [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_AUTHOR)) {
    $env:ANTHARES_GITLAB_QUEUE_AUTHOR = [string]$config.gitlab_author
}
if ($config.gitlab_token_dpapi -and [string]::IsNullOrWhiteSpace($env:ANTHARES_GITLAB_QUEUE_TOKEN)) {
    $env:ANTHARES_GITLAB_QUEUE_TOKEN = Unprotect-ARASecret ([string]$config.gitlab_token_dpapi)
}
if ($config.interval_seconds) {
    $env:ANTHARES_ISSUE_QUEUE_INTERVAL_SECONDS = [string][int]$config.interval_seconds
}
