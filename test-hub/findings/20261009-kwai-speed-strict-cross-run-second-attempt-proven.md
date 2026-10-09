# Strict cross-run snapshot: second independent attempt
STATUS: PROVEN
DATE: 2026-10-09
AREA: kwai-speed
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37935754939/attempts/2
JOB: 113837994980
WORKFLOW_COMMIT: 9e099ebd16300afac964ecd6df8c2f4fbfa8795e

## Independently verified evidence
GitHub-hosted rerun job completed SUCCESS with no failed steps.
Cache hits: kwai-speed-android35-google-apis-x86_64-v1, kwai-speed-emulator-ubuntu24-v1, kwai-speed-avd-fullstate-android35-v2, kwai-speed-vault-96650454576a2cf5-v1.
CROSS_RUN_SNAPSHOT_ARCHIVE_BYTES=2713682499
CROSS_RUN_SNAPSHOT_START_FROM_T0_SECONDS=57
CROSS_RUN_SNAPSHOT_BOOT_SECONDS=7
CROSS_RUN_TOTAL_TO_BOOT_SECONDS=64
CROSS_RUN_SNAPSHOT_RESULT=BOOTED
CROSS_RUN_SNAPSHOT_ACTUAL_LOAD=true
Emulator: Successfully loaded snapshot 'kwai-ready' using 2482 ms.

## Comparison
First strict attempt: 6s snapshot boot; 67s full startup.
Second strict attempt: 7s snapshot boot; 64s full startup.
Differences can be runner variability; do not infer an optimization from two samples.
No code fix required. No local PC and no login agent modification.
