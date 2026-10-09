# Cross-run Android startup: remove redundant work
STATUS: RUNNING
DATE: 2026-10-09
AREA: kwai-speed
WORKFLOW_COMMIT: 9473aa786cc871bbe3db4d01098397141b46a368
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37938287543

## Proven baseline
Run 37935754939 attempt 1: 6s snapshot boot; 67s total-to-boot; explicit snapshot load confirmed.
Run 37935754939 attempt 2: 7s snapshot boot; 64s total-to-boot; explicit snapshot load confirmed.
Cache key kwai-speed-avd-fullstate-android35-v2 and full archive 2713682499 bytes preserved.

## New independent experiment
Remove tar --zstd -tf full archive scan, which needlessly decompresses the large archive before actual extraction. Remove redundant adb emulator shutdown before restoring AVD on a fresh runner. Add CROSS_RUN_ARCHIVE_EXTRACT_SECONDS. Keep explicit snapshot-load gate, full cache and all earlier PROVEN findings intact.

## Constraints
No login-agent modifications; no local PC; hosted GitHub Actions only. Results pending. Do not mark experiment PROVEN until logs show successful load and actual measured timings.
