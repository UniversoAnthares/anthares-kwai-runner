# Kwai portable snapshot cache: archive creation proven
STATUS: PARTIAL
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37859479898
JOB: 113591526958
COMMIT: 4104ab3a39627b3671b6267f5b8065268cc0f4ee
SUPERSEDES: 20261008-kwai-speed-triple-cache-snapshot-proven.md

## PROVEN
Hosted run 37859479898 completed SUCCESS. PREP_TOTAL_SECONDS=0; COLD_BOOT_SECONDS=37; TOTAL_SECONDS=63; SNAPSHOT_SAVE_SECONDS=4; SNAPSHOT_RESTORE_BOOT_SECONDS=4; SNAPSHOT_RESTORE_RESULT=BOOTED. Portable snapshot archive /tmp/kwai-portable-avd.tar.zst produced with 947101991 bytes. GitHub cache saved under kwai-speed-avd-snapshot-android35-v1. Cache hit absent on first creation as expected.

## NOT YET PROVEN
A separate hosted runner can restore and actually load the snapshot; boot_completed alone may indicate a fallback cold boot. Inspect emulator log for explicit snapshot load confirmation.

## NEXT
Commit 6abbf331883da3f7515f3134ec3bb764b2c6db98 adds separate-run archive cache restore, extract and snapshot boot attempt with explicit CROSS_RUN_SNAPSHOT_* signals. Inspect new run logs; if cache hit and boot succeed, verify emulator snapshot load lines before claiming true snapshot reuse. No login agent workflow changed; no local PC.
