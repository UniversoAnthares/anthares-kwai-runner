# QA TikTok synthetic canary harness 5-way
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-06
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: test-hub/findings/20261006-0230-qa-tiktok-real-canary-ffmpeg-harness-invalid.md

BASELINE_PROVEN: run 37403086793 never tested TikTok publication because ffmpeg was absent.
FAILED_AVOIDED: no publication and no session mutation; test only five independent cloud media-generation/provisioning mechanisms.
SUCCESS_SIGNAL: mechanism creates a valid non-empty MP4 locally on runner.
FAILURE_SIGNAL: mechanism cannot provision/generate a usable MP4.
TEST_VALIDITY: runner shell/Python must execute; network-dependent variants report separately.

## Objetivo
Find at least one deterministic no-PC canary media preparation path before another real publication attempt.