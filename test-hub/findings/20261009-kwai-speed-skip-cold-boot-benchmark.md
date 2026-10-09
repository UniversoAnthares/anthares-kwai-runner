# Skip cold boot when full AVD snapshot cache hits
STATUS: RUNNING
DATE: 2026-10-09
AREA: kwai-speed
PREVIOUS_RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37934430597
NEW_RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37935480964
COMMIT: 7021ca9d4787bfc03b76737d11dbb0ef40c07e27

## Previous verified result
Cache hit for kwai-speed-avd-fullstate-android35-v2. CROSS_RUN_SNAPSHOT_ACTUAL_LOAD=true; CROSS_RUN_SNAPSHOT_BOOT_SECONDS=5; emulator reported Successfully loaded snapshot 'kwai-ready' using 2563 ms. Baseline cold boot took 35 seconds; TOTAL_SECONDS=99 was measured before cross-run restore, so does not represent total-to-snapshot-ready.

## Change
The isolated benchmark now skips Boot clean Android and measure on a full AVD cache hit, ensures /dev/kvm permissions in the cross-run path, and reports CROSS_RUN_TOTAL_TO_BOOT_SECONDS from initial timing. The new run will test whether bypassing the cold boot reduces end-to-end startup. No login agent changes and no local PC.
