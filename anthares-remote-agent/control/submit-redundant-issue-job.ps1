# Submits the SAME job_id to GitHub and GitLab private queues.
# The Windows agent's durable receipt is keyed by job_id, so mirrored delivery is
# at-most-once even if both providers are healthy at the same time.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Type,
    [hashtable]$Args = @{},
    [string]$DeviceId = 'DESKTOP-FTDK0HP',
    [ValidateRange(1,120)][int]$TimeoutSeconds = 30,
    [string]$JobId = ('ara-' + [Guid]::NewGuid().ToString('N')),
    [string]$GithubRepository = 'UniversoAnthares/anthares-ara-queue',
    [string]$GitlabProject = 'universo-anthares-group/anthares-kwai-runner'
)
$ErrorActionPreference = 'Stop'
if ($JobId -notmatch '^[A-Za-z0-9_-]{1,128}$') { throw 'Unsafe JobId' }
if ($DeviceId -notmatch '^[A-Za-z0-9_.-]{1,128}$') { throw 'Unsafe DeviceId' }
if ([string]::IsNullOrWhiteSpace($Type)) { throw 'Type is required' }

$job = [ordered]@{
    job_id = $JobId
    device_id = $DeviceId
    type = $Type.Trim()
    args = $Args
    timeout_seconds = $TimeoutSeconds
}
$description = $job | ConvertTo-Json -Compress -Depth 8
$title = "ARA job $JobId — $($Type.Trim())"
$outcomes = [ordered]@{ job_id = $JobId; github = 'not-configured'; gitlab = 'not-configured' }
$success = 0

$githubToken = [string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
if (-not [string]::IsNullOrWhiteSpace($githubToken)) {
    try {
        if ($GithubRepository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') { throw 'Invalid GitHub repository' }
        $ghHeaders = @{
            Authorization = "Bearer $githubToken"
            Accept = 'application/vnd.github+json'
            'X-GitHub-Api-Version' = '2022-11-28'
            'User-Agent' = 'AntharesRemoteControl/0.4.0'
        }
        $ghApi = "https://api.github.com/repos/$GithubRepository"
        $meta = Invoke-RestMethod -Headers $ghHeaders -Uri $ghApi -TimeoutSec 15
        if (-not $meta.private) { throw 'GitHub queue repository must be private' }
        $body = @{title=$title; body=$description; labels=@('ara-queued')} | ConvertTo-Json -Depth 5
        $created = Invoke-RestMethod -Method Post -Headers $ghHeaders -ContentType 'application/json' -Body $body -Uri "$ghApi/issues" -TimeoutSec 20
        $outcomes.github = [ordered]@{ok=$true; number=$created.number; url=$created.html_url}
        $success++
    } catch {
        $outcomes.github = [ordered]@{ok=$false; error=$_.Exception.Message}
    }
}

$gitlabToken = [string]$env:ANTHARES_GITLAB_QUEUE_TOKEN
if (-not [string]::IsNullOrWhiteSpace($gitlabToken)) {
    try {
        if ($GitlabProject -notmatch '^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+$') { throw 'Invalid GitLab project' }
        $glHeaders = @{'PRIVATE-TOKEN'=$gitlabToken; 'User-Agent'='AntharesRemoteControl/0.4.0'}
        $encodedProject = [Uri]::EscapeDataString($GitlabProject)
        $glApi = "https://gitlab.com/api/v4/projects/$encodedProject"
        $meta = Invoke-RestMethod -Headers $glHeaders -Uri $glApi -TimeoutSec 15
        if ($meta.visibility -eq 'public') { throw 'GitLab queue project must not be public' }
        $body = @{
            title = $title
            description = $description
            labels = 'ara-queued'
            confidential = $true
        } | ConvertTo-Json -Depth 5
        $created = Invoke-RestMethod -Method Post -Headers $glHeaders -ContentType 'application/json' -Body $body -Uri "$glApi/issues" -TimeoutSec 20
        $outcomes.gitlab = [ordered]@{ok=$true; iid=$created.iid; url=$created.web_url}
        $success++
    } catch {
        $outcomes.gitlab = [ordered]@{ok=$false; error=$_.Exception.Message}
    }
}

if ($success -eq 0) {
    $outcomes | ConvertTo-Json -Depth 6
    throw 'No issue queue provider accepted the job.'
}
$outcomes | ConvertTo-Json -Depth 6
