# TikTok canary follow-up: five safe preflights
STATUS: RUNNING
AREA: tiktok-safe-preflight
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37404780109
COMMIT: 1a571c2245275721fc66d903bb8f440ffdaea518
SUPERSEDES: none

BASELINE_PROVEN: run 37404235739 proved synthetic MP4 generation/ffprobe and TikTok session readiness, but the canary stopped before enqueue because curl combined --fail-with-body with -f.
FAILED_AVOIDED: no started or /publish in these probes; no duplicate canary; do not duplicate the separately leased tiktok-canary-media-harness-fiveway area.
SUCCESS_SIGNAL: five independent jobs complete: control-health, queue-health, render-health, session-status, session-test.
FAILURE_SIGNAL: any job returns HTTP/auth/contract failure.
TEST_VALIDITY: each matrix job runs independently and performs no queue mutation and no publication.

## Parallel implementation
Real canary workflow commit b2958039d186b3a2b4552b0dd4de76aa679ef21d removes the curl flag conflict and disables the legacy workflow_dispatch publish job that attempted an empty VIDEO_URL.

## Current scheduler state
All five jobs are created but queued behind the repository-wide GitHub Actions backlog. No in-progress runner was available at last check. Do not create duplicate runs while this run remains queued.
