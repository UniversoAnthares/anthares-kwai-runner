# Cross-run Android snapshot: confirmed load and streamlined benchmark
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-09
PREVIOUS_RUN: 37875245895 attempt 2
PREVIOUS_JOB: 113642887099
NEW_RUN: 37934430597
COMMIT: 50253917c41410d7a1a5900919821f73182cd51d

## VERIFIED EVIDENCE
On a separate hosted runner the cache key kwai-speed-avd-fullstate-android35-v2 was a hit. CROSS_RUN_SNAPSHOT_RESULT=BOOTED; CROSS_RUN_SNAPSHOT_BOOT_SECONDS=4. Emulator log explicitly says Successfully loaded snapshot 'kwai-ready' using 1768 ms. COLD_BOOT_SECONDS=26 and TOTAL_SECONDS=88 for baseline run, which includes initial cache restore and conventional boot. The 4s is post-extraction boot only, not total workflow elapsed time.

## IMPROVEMENT
Commit 50253917 tightens CROSS_RUN_SNAPSHOT_ACTUAL_LOAD to true only on explicit emulator success message, not a mere Loading snapshot line. It also skips redundant local snapshot save and full AVD re-archive when the cache already hits. Follow-up run 37934430597 triggered by this workflow change.

## COORDINATION
Only isolated startup speed workflow and speed finding changed. No kwai-login agent files touched. No local computer used. The cache is multi-GB, so end-to-end speed remains constrained by download/extraction.
