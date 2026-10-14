# Phase 5: enable GitLab as a second private issue-queue transport.
# The caller must run elevated and provide the token as a SecureString.
# The token is validated in memory and persisted only as a DPAPI LocalMachine blob.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][Security.SecureString]$GitlabToken,
    [string]$GitlabProject = 'universo-anthares-group/anthares-kwai-runner',
    [string]$GitlabAuthor = 'UniversoAnthares'
)
$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\AntharesRemoteAgent'
$secretRoot = Join-Path $root 'secrets'
$configPath = Join-Path $secretRoot 'issue-queue.json'
$canonicalTask = 'Anthares Remote Agent SYSTEM'
$statePath = 'D:\AntharsWork\legacy-pc-runtime\supervisor\system-supervisor-state.json'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Administrative elevation is required to provision the SYSTEM queue credential.'
}
if (-not (Test-Path -LiteralPath $configPath)) { throw 'Canonical issue-queue credential file is missing.' }
try { Add-Type -AssemblyName System.Security -ErrorAction Stop } catch { throw 'System.Security is required for DPAPI queue credentials.' }

function Protect-ARASecret([Security.SecureString]$secret) {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        $plainText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        if ([string]::IsNullOrWhiteSpace($plainText)) { throw 'GitLab token is empty.' }
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
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Test-GitLabToken([Security.SecureString]$secret) {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        $plainText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        if ([string]::IsNullOrWhiteSpace($plainText)) { throw 'GitLab token is empty.' }
        $headers = @{ 'PRIVATE-TOKEN' = $plainText; 'User-Agent' = 'AntharesRemoteAgent-Phase5' }
        $encodedProject = [Uri]::EscapeDataString($GitlabProject)
        $project = Invoke-RestMethod -Method Get -Uri ('https://gitlab.com/api/v4/projects/' + $encodedProject) -Headers $headers -TimeoutSec 20
        if (-not $project -or [string]$project.path_with_namespace -ne $GitlabProject) { throw 'GitLab token resolved the wrong project.' }
        if ([string]$project.visibility -ne 'private') { throw 'Refusing non-private GitLab queue project.' }
        [void](Invoke-RestMethod -Method Get -Uri ('https://gitlab.com/api/v4/projects/' + $encodedProject + '/issues?state=opened&labels=ara-queued&per_page=1') -Headers $headers -TimeoutSec 20)
        return $true
    } finally {
        $plainText = $null
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

[void](Test-GitLabToken $GitlabToken)
$existing = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace([string]$existing.github_token_dpapi)) { throw 'GitHub canonical credential would be lost; refusing Phase 5 activation.' }
$gitlabCipher = Protect-ARASecret $GitlabToken
$interval = 20
if ($existing.interval_seconds) { $interval = [Math]::Max(10,[Math]::Min(300,[int]$existing.interval_seconds)) }
$config = [ordered]@{
    version = 1
    github_repository = if ($existing.github_repository) { [string]$existing.github_repository } else { 'UniversoAnthares/anthares-ara-queue' }
    github_author = if ($existing.github_author) { [string]$existing.github_author } else { 'UniversoAnthares' }
    github_token_dpapi = [string]$existing.github_token_dpapi
    gitlab_project = $GitlabProject
    gitlab_author = $GitlabAuthor
    gitlab_token_dpapi = $gitlabCipher
    interval_seconds = $interval
    updated_at = (Get-Date).ToUniversalTime().ToString('o')
}
$tmp = $configPath + '.phase5.tmp'
$config | ConvertTo-Json | Set-Content -LiteralPath $tmp -Encoding UTF8
& icacls.exe $secretRoot /inheritance:r /grant:r '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
Move-Item -LiteralPath $tmp -Destination $configPath -Force
& icacls.exe $configPath /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' | Out-Null

Stop-ScheduledTask -TaskName $canonicalTask -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Start-ScheduledTask -TaskName $canonicalTask -ErrorAction Stop
$deadline = (Get-Date).AddSeconds(60)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    if (-not (Test-Path -LiteralPath $statePath)) { continue }
    try {
        $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ([bool]$state.github_queue -and [bool]$state.gitlab_queue) { $ready = $true; break }
    } catch {}
}
if (-not $ready) { throw 'GitLab credential was stored, but the SYSTEM supervisor did not report both queues ready within 60 seconds.' }
[pscustomobject]@{
    ok = $true
    github_queue = $true
    gitlab_queue = $true
    gitlab_project = $GitlabProject
    token_persisted_as = 'DPAPI LocalMachine'
    token_printed = $false
    system_task_restarted = $true
} | ConvertTo-Json -Compress
