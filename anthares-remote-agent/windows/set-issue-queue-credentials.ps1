# One-time local credential provisioning for the ARA issue queue transports.
# Tokens are accepted as SecureString and written only as DPAPI LocalMachine blobs.
[CmdletBinding()]
param(
    [string]$GithubRepository = 'UniversoAnthares/anthares-ara-queue',
    [Security.SecureString]$GithubToken,
    [string]$GithubAuthor = 'UniversoAnthares',
    [string]$GitlabProject = 'universo-anthares-group/anthares-kwai-runner',
    [Security.SecureString]$GitlabToken,
    [string]$GitlabAuthor = 'UniversoAnthares',
    [ValidateRange(10,300)][int]$IntervalSeconds = 20,
    [switch]$KeepExistingMissingTokens
)
$ErrorActionPreference = 'Stop'
try { Add-Type -AssemblyName System.Security -ErrorAction Stop } catch { throw 'System.Security is required for DPAPI queue credentials' }
$root = 'C:\ProgramData\AntharesRemoteAgent\secrets'
$configPath = Join-Path $root 'issue-queue.json'
New-Item -ItemType Directory -Path $root -Force | Out-Null

function Protect-ARASecret([Security.SecureString]$secret) {
    if ($null -eq $secret) { return $null }
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        $plainText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $plain = [Text.Encoding]::UTF8.GetBytes($plainText)
        $entropy = [Text.Encoding]::UTF8.GetBytes('AntharesRemoteAgentIssueQueueV1')
        try {
            $cipher = [System.Security.Cryptography.ProtectedData]::Protect(
                $plain,
                $entropy,
                [System.Security.Cryptography.DataProtectionScope]::LocalMachine
            )
            return [Convert]::ToBase64String($cipher)
        } finally {
            [Array]::Clear($plain, 0, $plain.Length)
            $plainText = $null
        }
    } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

$existing = $null
if ((Test-Path $configPath) -and $KeepExistingMissingTokens) { try { $existing = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch {} }
$githubCipher = Protect-ARASecret $GithubToken
$gitlabCipher = Protect-ARASecret $GitlabToken
if (-not $githubCipher -and $existing) { $githubCipher = [string]$existing.github_token_dpapi }
if (-not $gitlabCipher -and $existing) { $gitlabCipher = [string]$existing.gitlab_token_dpapi }
if (-not $githubCipher -and -not $gitlabCipher) { throw 'At least one queue token is required (or use -KeepExistingMissingTokens with an existing credential file).' }

$config = [ordered]@{
    version = 1; github_repository = $GithubRepository; github_author = $GithubAuthor; github_token_dpapi = $githubCipher
    gitlab_project = $GitlabProject; gitlab_author = $GitlabAuthor; gitlab_token_dpapi = $gitlabCipher
    interval_seconds = $IntervalSeconds; updated_at = (Get-Date).ToUniversalTime().ToString('o')
}
$tmp = $configPath + '.tmp'
$config | ConvertTo-Json | Set-Content -LiteralPath $tmp -Encoding UTF8
Move-Item -LiteralPath $tmp -Destination $configPath -Force
& icacls.exe $root /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
& icacls.exe $configPath /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null
Write-Output 'ARA issue queue credentials stored with DPAPI LocalMachine; token values were not printed.'
