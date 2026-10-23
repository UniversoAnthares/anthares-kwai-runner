# CORTES P0 safe, bounded repair playbook executed only after verified QA-P0.
# This invokes existing fenced recovery paths; it never edits clips or retries
# started/uncertain posts. A dispatch ACK is not media-publication proof.
param([Parameter(Mandatory=$true)][int]$IssueNumber)
$ErrorActionPreference='Stop'
if($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or
    $env:GITHUB_REPOSITORY -ne 'UniversoAnthares/anthares-kwai-runner'){
    throw 'QA_AUTOHEAL_TRUSTED_RUNNER_REQUIRED'
}
$token=$env:GITHUB_TOKEN
if(!$token){throw 'QA_AUTOHEAL_GITHUB_AUTH_REQUIRED'}
$headers=@{'Authorization'='Bearer '+$token;'Accept'='application/vnd.github+json';'User-Agent'='CORTES-P0-autoheal/1'}
$root='https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner'
$issue=Invoke-RestMethod -Uri ($root+'/issues/'+$IssueNumber) -Headers $headers -TimeoutSec 18
$labels=@($issue.labels|ForEach-Object{$_.name})
if($issue.state -ne 'open' -or $labels -notcontains 'QA-P0' -or
    [string]$issue.title -notmatch '^\[QA[ -]P0\]' -or $issue.pull_request){
    throw 'QA_AUTOHEAL_INCIDENT_NOT_AUTHORIZED'
}
$action='DIAGNOSTIC_ONLY_NO_APPROVED_REPAIR'
$body=([string]$issue.body)
. (Join-Path $PSScriptRoot 'cortes_qa_p0_policy.ps1')
$diagnostic='NO_AUTOMATED_REPAIR_CONTRACT'
$title=([string]$issue.title)
$local=[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow,'Central Brazilian Standard Time')
$isDaily=($title -match '(?i)cortes|daily|produtor' -and
          $body -match '(?i)zero masters|sem masters|P0_DAILY_PRODUCER_ZERO_MASTERS|HTTP 502')
$isPersonal=Test-QaLinkedinPersonalIncident -Title $title -Body $body
if($isDaily){
    $url='https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/?action=round-health'
    $health=Invoke-RestMethod -Uri $url -TimeoutSec 20
    if($health.ok -ne $true -or $health.round_timezone -ne 'America/Campo_Grande'){
        throw 'QA_AUTOHEAL_NEON_HEALTH_INVALID'
    }
    if([int]$health.today_master_count -eq 0 -and $local.Hour -ge 7 -and $local.Hour -lt 21){
        $task='Anthares CORTES Shorts Daytime Recovery 20min'
        $scheduled=Get-ScheduledTask -TaskName $task -ErrorAction Stop
        if($scheduled.State -eq 'Disabled'){throw 'QA_AUTOHEAL_TASK_DISABLED'}
        Start-ScheduledTask -TaskName $task -ErrorAction Stop
        $action='DAILY_PRODUCER_WATCHDOG_WAKEUP_ACCEPTED'
    }else{$action='DAILY_NEON_PRESENT_OR_OUTSIDE_WINDOW'}
}elseif($isPersonal){
    # The publisher is protected by its own Neon lease/started/uncertain CAS.
    # This QA path only dispatches the approved existing workflow; it never
    # constructs, retries or marks any individual media item as published.
    $workflow='cortes-linkedin-personal-fallback-cloud.yml'
    $endpoint=$root+'/actions/workflows/'+$workflow
    $runs=Invoke-RestMethod -Uri ($endpoint+'/runs?per_page=30&branch=main') -Headers $headers -TimeoutSec 22
    if($null -eq $runs -or $null -eq $runs.workflow_runs) {
        throw 'QA_LINKEDIN_WORKFLOW_READBACK_INVALID'
    }
    $decision=Get-QaLinkedinPersonalDecision -Runs @($runs.workflow_runs) -NowUtc ([datetime]::UtcNow)
    $latest=@($runs.workflow_runs | Sort-Object created_at -Descending | Select-Object -First 1)
    $lastId=if($latest.Count -gt 0){[string]$latest[0].id}else{'none'}
    $diagnostic='workflow='+$workflow+';latest_run_id='+$lastId+';decision='+$decision
    if($decision -eq 'LINKEDIN_PERSONAL_PRIMARY_DISPATCH_ALLOWED'){
        $data=ConvertTo-Json -Compress @{ref='main'}
        Invoke-RestMethod -Uri ($endpoint+'/dispatches') -Method Post -Headers $headers -Body $data -ContentType 'application/json' -TimeoutSec 22|Out-Null
        $action='LINKEDIN_PERSONAL_PRIMARY_DISPATCH_ACCEPTED'
        $diagnostic+=';dispatch_ack_only=true;publication_verified=false'
    }else{
        $action=$decision
    }
}
if($env:GITHUB_OUTPUT){
    Add-Content -LiteralPath $env:GITHUB_OUTPUT -Value ('action='+$action) -Encoding UTF8
    Add-Content -LiteralPath $env:GITHUB_OUTPUT -Value ('diagnostic='+$diagnostic) -Encoding UTF8
}
Write-Output ('CORTES_QA_P0_AUTOHEAL_ACTION='+$action)
Write-Output ('CORTES_QA_P0_DIAGNOSTIC='+$diagnostic)
