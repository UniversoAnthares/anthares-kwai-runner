# Read-only decision policy for LinkedIn personal QA P0. No network or writes.
function Test-QaLinkedinPersonalIncident {
    param([string]$Title,[string]$Body)
    $titleMatches = $Title -match '(?i)^\[QA[ -]P0\]\[linkedin(?:/personal-primary)?\]'
    $sourceMatches = $Body -match '(?i)(?:linkedin/personal-primary|CORTES LinkedIn personal)'
    $stageMatches = $Body -match '(?i)(?:github_workflow_visibility_lost|cloud_primary_heartbeat_lost|hosted_runner_stalled_over_23min|CORTES LinkedIn personal)'
    return [bool]($titleMatches -and $sourceMatches -and $stageMatches)
}

function Get-QaLinkedinPersonalDecision {
    param(
        [AllowNull()][object[]]$Runs,
        [datetime]$NowUtc = [datetime]::UtcNow
    )
    # Never dispatch if the API supplied malformed/incomplete evidence.
    if ($null -eq $Runs) { return 'WORKFLOW_VISIBILITY_UNKNOWN_NO_DISPATCH' }
    $active = @($Runs | Where-Object { $_.status -in @('queued','pending','in_progress','waiting','requested') })
    if ($active.Count -gt 0) { return 'WORKFLOW_ACTIVE_OR_QUEUED_NO_DISPATCH' }
    $ordered = @($Runs | Sort-Object { try { [datetime]$_.created_at } catch { [datetime]::MinValue } } -Descending)
    if ($ordered.Count -eq 0) { return 'LINKEDIN_PERSONAL_PRIMARY_DISPATCH_ALLOWED' }
    $newest = $ordered[0]
    if (-not $newest.created_at -or -not $newest.status -or $newest.status -ne 'completed') {
        return 'WORKFLOW_VISIBILITY_UNKNOWN_NO_DISPATCH'
    }
    try { $created = ([datetimeoffset]::Parse([string]$newest.created_at)).UtcDateTime }
    catch { return 'WORKFLOW_VISIBILITY_UNKNOWN_NO_DISPATCH' }
    $minutes = ($NowUtc.ToUniversalTime() - $created).TotalMinutes
    if ($minutes -lt 0) { return 'WORKFLOW_VISIBILITY_UNKNOWN_NO_DISPATCH' }
    # A completed run needs time for independent proof; a manual repair also
    # gets a cooldown, avoiding repeated dispatches for an open incident.
    if ($minutes -lt 20) { return 'RECENT_WORKFLOW_NO_DISPATCH_PUBLICATION_UNVERIFIED' }
    return 'LINKEDIN_PERSONAL_PRIMARY_DISPATCH_ALLOWED'
}
