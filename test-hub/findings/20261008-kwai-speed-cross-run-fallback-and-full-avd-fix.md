# Cross-run Android snapshot: cache hit but cold-boot fallback
STATUS: PARTIAL
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37860106590
JOB: 113593532277
COMMIT: 6abbf331883da3f7515f3134ec3bb764b2c6db98
SUPERSEDES: 20261008-kwai-speed-snapshot-archive-proof.md

## PROVEN
Run completed SUCCESS. Cache hit for snapshot kwai-speed-avd-snapshot-android35-v1; restored archive 947101991 bytes. PREP_TOTAL_SECONDS=0; COLD_BOOT_SECONDS=31; TOTAL_SECONDS=220; CROSS_RUN_SNAPSHOT_BOOT_SECONDS=26; CROSS_RUN_SNAPSHOT_RESULT=BOOTED. But emulator log explicitly reports 'Device cache does not have requested snapshot kwai-ready', 'Failed to load snapshot kwai-ready', and cold boot fallback. Thus actual cross-run snapshot restore FAILED. Same-run save subsequently FAILED (likely emulator state interference). Do not label the 26-second boot as snapshot acceleration.

## ROOT CAUSE HYPOTHESIS
Only snapshots/kwai-ready directory was archived; full AVD device state, including disk/cache metadata, not transported. Cache transfer itself succeeded.

## FIX / NEXT
Commit ed7136059a63b1bd10ee3e2913206d1a6d30d869 packages entire kwai-speed.avd directory plus kwai-speed.ini under a new cache key kwai-speed-avd-fullstate-android35-v2, and logs CROSS_RUN_SNAPSHOT_ACTUAL_LOAD=false on explicit cold boot fallback. First new run creates full archive; a subsequent separate run must validate true load. No kwai-login files changed; no local PC.
