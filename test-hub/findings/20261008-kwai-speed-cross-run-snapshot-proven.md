# Cross-run Android snapshot reuse proven
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37875245895
ATTEMPT: 2
JOB: 113642887099
SOURCE_CACHE_BUILD_JOB: 113642226915
COMMIT: 45f2b8dca95576984592b88eb97de8c4735fdb73
SUPERSEDES: 20261008-kwai-speed-full-avd-cache-key-fix.md

## PROVEN: full AVD cache creation
Attempt 1 / job 113642226915 completed SUCCESS. It created /tmp/kwai-portable-avd-full.tar.zst with PORTABLE_SNAPSHOT_ARCHIVE_BYTES=2713682499 and saved it under key kwai-speed-avd-fullstate-android35-v2. Same-run snapshot restore remained 4 seconds. The cache key now matches restore.

## PROVEN: independent hosted runner
Attempt 2 / job 113642887099 ran on a different GitHub-hosted Azure worker (centralus; distinct worker ID). Cache hit for kwai-speed-avd-fullstate-android35-v2, size ~2588 MiB / 2713352835 cached bytes, restored successfully. PORTABLE_SNAPSHOT_CACHE_HIT=true.

Cross-run signals from decoded job log:
- CROSS_RUN_SNAPSHOT_ARCHIVE_BYTES=2713682499
- CROSS_RUN_SNAPSHOT_BOOT_SECONDS=4
- CROSS_RUN_SNAPSHOT_RESULT=BOOTED
- emulator: Loading snapshot 'kwai-ready'...
- emulator: Successfully loaded snapshot 'kwai-ready' using 1768 ms
- no 'Failed to load snapshot kwai-ready' / cold-boot fallback in the cross-run snapshot log

Therefore cross-run snapshot reuse is PROVEN and snapshot-to-boot_completed is 4 seconds, below the 10-second target.

## BASELINE / SCOPE
The same attempt's conventional cold boot was 26 seconds. PREP_TOTAL_SECONDS=0 after caches were restored. TOTAL_SECONDS=88 includes checkout/cache restoration and the intentionally retained baseline cold boot, so it is not the optimized production startup path. Restoring the ~2.6 GiB full-AVD cache itself took about 26 seconds from cache action start to completion; the 4-second figure is the actual Android snapshot launch after the archive has been restored/extracted.

## NON-BLOCKING ISSUE
After the successful cross-run test, the workflow killed the emulator and then the later same-run snapshot-save experiment attempted adb emu snapshot save, producing connection refused. This did not affect the proven cross-run result. The benchmark should skip same-run generation/package work on AVD-cache hits and emit CROSS_RUN_SNAPSHOT_ACTUAL_LOAD=true on the explicit success log.

## COORDINATION
Only isolated kwai-startup-speed-benchmark.yml and kwai-speed findings are in scope. No kwai-login files changed. No local PC used.
