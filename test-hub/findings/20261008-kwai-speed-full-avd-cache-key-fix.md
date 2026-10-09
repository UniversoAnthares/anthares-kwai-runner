# Full AVD archive created; cache-key mismatch corrected
STATUS: PARTIAL
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37861611187
JOB: 113598440096
COMMIT: 9c8c7f8c19b5a2a908a97767baba4a991af2bd88
SUPERSEDES: 20261008-kwai-speed-full-avd-tar-race-fix.md

## PROVEN
Run 37861611187 completed SUCCESS. Android image, emulator and Kwai vault caches restored. PREP_TOTAL_SECONDS=0; COLD_BOOT_SECONDS=37; TOTAL_SECONDS=77. Same-run snapshot save=4s and snapshot reboot=4s. Emulator was stopped before archive. Full AVD archive was created successfully: PORTABLE_SNAPSHOT_ARCHIVE_BYTES=2733508971. No tar file-changed race.

## BUG FOUND
Restore expected key kwai-speed-avd-fullstate-android35-v2, but save step still used kwai-speed-avd-snapshot-android35-v1. Consequently the new full-state v2 cache could not be consumed by an independent runner even though the archive itself was validly created.

## FIX
Commit 45f2b8dca95576984592b88eb97de8c4735fdb73 makes actions/cache/save use the same key kwai-speed-avd-fullstate-android35-v2. Push-triggered run 37875245895 will create the correct v2 cache. A subsequent independent runner is required to prove real cross-run snapshot load and <10s boot. Do not claim cross-run acceleration before emulator logs show a successful kwai-ready snapshot load without cold-boot fallback.

## COORDINATION
Only .github/workflows/kwai-startup-speed-benchmark.yml and kwai-speed findings changed. No kwai-login workflow/script modified. No local PC used.
