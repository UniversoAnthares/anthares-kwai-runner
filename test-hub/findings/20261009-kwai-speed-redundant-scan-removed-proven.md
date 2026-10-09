# Full AVD snapshot startup: 50-second result
STATUS: PROVEN
DATE: 2026-10-09
AREA: kwai-speed
WORKFLOW_COMMIT: 9473aa786cc871bbe3db4d01098397141b46a368
RUN_ATTEMPT_1: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37938287543/attempts/1
JOB_ATTEMPT_1: 113845826536
RUN_ATTEMPT_2: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37938287543/attempts/2

## First independent runner: PROVEN
Job success, no failed steps. Cache hits for Android image, emulator binary, complete AVD snapshot v2 and vault.
CROSS_RUN_ARCHIVE_EXTRACT_SECONDS=7
CROSS_RUN_SNAPSHOT_START_FROM_T0_SECONDS=44
CROSS_RUN_SNAPSHOT_BOOT_SECONDS=6
CROSS_RUN_TOTAL_TO_BOOT_SECONDS=50
CROSS_RUN_SNAPSHOT_RESULT=BOOTED
CROSS_RUN_SNAPSHOT_ACTUAL_LOAD=true
Emulator explicitly logged Successfully loaded snapshot 'kwai-ready' using 2637 ms.

## Comparison and caveat
Previous independent attempt: 64s total, 7s snapshot boot.
Current independent attempt: 50s total, 6s snapshot boot.
14s lower observed time is not yet a statistically isolated improvement: hosted runner and cache transfer variation can contribute.
Changes removed redundant full archive listing and unnecessary adb shutdown before restore. Full AVD cache key unchanged.

## Follow-up
GitHub job rerun requested successfully; run attempt 2 queued at time of this finding. Must inspect its own logs before declaring the second attempt PROVEN.

## Constraints
No local PC, no login agent changes. All earlier PROVEN findings preserved.
