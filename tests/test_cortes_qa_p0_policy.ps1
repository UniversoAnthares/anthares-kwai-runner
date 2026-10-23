$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\tools\cortes_qa_p0_policy.ps1')
function Assert-Equal([string]$Got,[string]$Expected,[string]$Case) {
    if($Got -cne $Expected){throw ('QA_POLICY_TEST_FAILED '+$Case+' got='+$Got+' expected='+$Expected)}
}
function Assert-True([bool]$Actual,[string]$Case) {
    if(-not $Actual){throw ('QA_POLICY_TEST_FAILED '+$Case)}
}
$body='QA-P0-FINGERPRINT:x; Independent Codeberg QA report #29 account=linkedin/personal-primary status=github_workflow_visibility_lost'
Assert-True (Test-QaLinkedinPersonalIncident '[QA P0][linkedin] Falha de publicação' $body) 'current-incident'
Assert-True (Test-QaLinkedinPersonalIncident '[QA-P0][linkedin] Falha' 'CORTES LinkedIn personal') 'legacy-incident'
Assert-True (-not (Test-QaLinkedinPersonalIncident '[QA P0][linkedin] Buffer falhou' 'account=linkedin/corporate-buffer status=github_workflow_visibility_lost')) 'corporate-fenced'
Assert-True (-not (Test-QaLinkedinPersonalIncident '[QA P0][facebook] Falha' $body)) 'network-fenced'
Assert-True (-not (Test-QaLinkedinPersonalIncident '[QA P0][linkedin] Falha' 'account=linkedin/personal-primary status=unknown-error')) 'unapproved-stage'
$now=[datetime]::Parse('2026-10-23T14:00:00Z').ToUniversalTime()
function Run([string]$Status,[string]$When,[string]$Event='schedule') {
    return [pscustomobject]@{status=$Status;created_at=$When;event=$Event}
}
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs $null -NowUtc $now) 'WORKFLOW_VISIBILITY_UNKNOWN_NO_DISPATCH' 'api-unknown'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @() -NowUtc $now) 'LINKEDIN_PERSONAL_PRIMARY_DISPATCH_ALLOWED' 'no-runs'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @((Run 'in_progress' '2026-10-23T13:00:00Z')) -NowUtc $now) 'WORKFLOW_ACTIVE_OR_QUEUED_NO_DISPATCH' 'active'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @((Run 'queued' '2026-10-23T12:00:00Z')) -NowUtc $now) 'WORKFLOW_ACTIVE_OR_QUEUED_NO_DISPATCH' 'stalled-still-queued'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @((Run 'completed' '2026-10-23T13:55:00Z')) -NowUtc $now) 'RECENT_WORKFLOW_NO_DISPATCH_PUBLICATION_UNVERIFIED' 'recent'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @((Run 'completed' '2026-10-23T13:53:00Z' 'workflow_dispatch')) -NowUtc $now) 'RECENT_WORKFLOW_NO_DISPATCH_PUBLICATION_UNVERIFIED' 'dispatch-cooldown'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @((Run 'completed' '2026-10-23T12:00:00Z')) -NowUtc $now) 'LINKEDIN_PERSONAL_PRIMARY_DISPATCH_ALLOWED' 'missing-heartbeat'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @((Run 'completed' '2026-10-23T12:00:00Z'),(Run 'queued' '2026-10-23T13:59:00Z')) -NowUtc $now) 'WORKFLOW_ACTIVE_OR_QUEUED_NO_DISPATCH' 'active-overrides-old'
Assert-Equal (Get-QaLinkedinPersonalDecision -Runs @([pscustomobject]@{status='completed';created_at='bad'}) -NowUtc $now) 'WORKFLOW_VISIBILITY_UNKNOWN_NO_DISPATCH' 'invalid-date'
Write-Output 'QA_P0_POLICY_SELFTEST=PASS cases=13'
