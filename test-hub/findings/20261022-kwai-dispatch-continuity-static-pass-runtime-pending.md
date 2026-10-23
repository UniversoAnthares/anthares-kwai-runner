# Kwai dispatch continuity static regression — production installation pending
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-22
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39876921616
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39876921616/job/120164646458
COMMIT: 4b52723d07c9d65edb0f529b423964443c070152
SUPERSEDES: test-hub/findings/20261022-kwai-dispatch-continuity-lease.md

## BASELINE_PROVEN
Neon contains queued Kwai jobs and no active lease, latest confirmation 2026-10-22T17:50:48Z. Cloudflare /job default and Neon-client control-base inheritance in canonical Windows daemon are real static defects. Three recovery script files contained literal task output markers that prevented parsing. Windows remote controls unavailable; exact outage log from 14:50 BRT inaccessible.

## FAILED_AVOIDED
No live test posts, no restarting a possibly in-flight physical/MEmu publication, no Neon mutation, no bypass of central lease/uncertain state, no overwriting local dirty Windows repo, no forbidden direct push to protected main.

## SUCCESS_SIGNAL
PR static workflow 39876921616 job 120164646458 completed SUCCESS. Python tests, Python compile and PowerShell Parser::ParseFile steps all successful.

## FAILURE_SIGNAL
Merge denied; Windows remains unreachable; task not installed; ongoing real posts unverified. Those conditions prevent production closure.

## TEST_VALIDITY
Static test passes demonstrate parseable files, canonical queue routing contract and watchdog code safeguards only. They do not prove runtime installation, an active Task Scheduler entry, or a verified new Kwai publication.

## Consequência
Merge the approved PR through branch protections, deploy minimal changes to the actual dirty Windows runtime after reconnecting, install independent hidden scheduled watchdog, verify scheduled task + resumed leased jobs and genuine public video confirmation. Keep uncertain jobs quarantined.
