# Strict cross-run snapshot verification: independent runner passed
STATUS: PROVEN
DATE: 2026-10-09
AREA: kwai-speed
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37935754939/attempts/1
JOB: 113837253697
COMMIT: 9e099ebd16300afac964ecd6df8c2f4fbfa8795e

## Evidence
The strict-gated workflow completed successfully on a GitHub-hosted runner. Cache hits: Android image v1, emulator v1, full AVD snapshot kwai-speed-avd-fullstate-android35-v2, vault v1. CROSS_RUN_SNAPSHOT_BOOT_SECONDS=6, CROSS_RUN_TOTAL_TO_BOOT_SECONDS=67, CROSS_RUN_SNAPSHOT_RESULT=BOOTED, CROSS_RUN_SNAPSHOT_ACTUAL_LOAD=true. Emulator reported Successfully loaded snapshot 'kwai-ready' using 2217 ms.

## Follow-up independent replication
A second job attempt was requested using rerun_workflow_job on job 113837253697. RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37935754939/attempts/2. New job 113837994980 was queued at time of record. Do not mark the second attempt PROVEN until its logs are checked.

## Scope
No login agent files changed. No local PC used. Snapshot boot time and full preparation time are separate metrics.
