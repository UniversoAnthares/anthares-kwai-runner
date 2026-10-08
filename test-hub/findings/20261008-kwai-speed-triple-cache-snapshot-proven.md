# Kwai speed triple-cache and same-run snapshot evidence
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37859160736; 37859208163
JOB: 113590514878; 113590668426
COMMIT: 1f44d86e7e7ed0f05b39d594fb4f4c6e199d7a1a; ed798f96629f22f15925f9d92349ea705c42352b
SUPERSEDES: 20261008-kwai-speed-triple-cache-snapshot-experiment.md

## PROVEN: triple cache
Both GitHub Actions jobs completed success. Logs independently show cache hit and restore for Android image, emulator binary, and validated Kwai vault.

## TIMINGS FROM DECODED JOB LOGS
Run 37859160736: SDK_READY_SECONDS=0; VAULT_READY_SECONDS=1; PREP_TOTAL_SECONDS=1; COLD_BOOT_SECONDS=31; TOTAL_SECONDS=87.
Run 37859208163: SDK_READY_SECONDS=0; VAULT_READY_SECONDS=0; PREP_TOTAL_SECONDS=0; COLD_BOOT_SECONDS=29; TOTAL_SECONDS=68.
TOTAL_SECONDS starts at job Start timing and includes cache restore; PREP_TOTAL_SECONDS excludes cache restore. Do not misrepresent it as full preparation wall clock.

## PROVEN: same-run snapshot
Run 37859208163: SNAPSHOT_SAVE_SECONDS=8; SNAPSHOT_RESTORE_BOOT_SECONDS=3; SNAPSHOT_RESTORE_RESULT=BOOTED. This proves save/reboot within one runner only, not portability or authentication.

## FOLLOW-UP
Commit 4104ab3a39627b3671b6267f5b8065268cc0f4ee packages snapshot directory into /tmp/kwai-portable-avd.tar.zst and caches it; next run must prove archive creation/cache save, later run must prove cross-run restore. Snapshot contains no Kwai login credentials; never assert account login or publication.

## COORDINATION
Only isolated speed benchmark workflow and speed findings modified; kwai-login agent untouched. Free hosted runner, no PC.
