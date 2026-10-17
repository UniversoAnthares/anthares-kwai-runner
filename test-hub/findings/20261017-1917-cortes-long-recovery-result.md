# CORTES long policy and upload recovery audit
STATUS: PARTIAL
AREA: queue
DATE: 2026-10-17
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39055418321 ; https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39057397351
COMMIT: 7a42deb7dd41856644ba98391b9270763f4928f6
SUPERSEDES: test-hub/findings/20261017-1914-lease-cortes-long-recovery.md
LEASE: CLOSED

## Decisive evidence
Run 1: RuntimeError Microedicao sem duracao minima, floor 480 seconds. Run 2: clipper.VideoStorageFull during WordPress FTP reservation, 20 GB combined limit. These were different causes.
Prior main commits 0d1fdc8 and 53ee6db exist and remove early four-candidate truncation and the 480-second floor for CORTES. They did not solve storage pressure or retention after failure.

## Corrections published
- Prefer accumulating tails into invalid bases before enlarging valid masters. If greedy allocation produces fewer than three, exhaust memoized legal merge states before reporting insufficiency. Regression includes [120,300,270,90,180] seconds, which greedy cannot rescue but search can.
- Reuse canonical duration constants and technical/literary priority. Recheck every surviving candidate using measured bytes before choosing the final four; do not prematurely discard a replacement candidate.
- Keep appended segment metadata in actual playback order.
- Check storage before expensive analysis and final upload set; preserve the authoritative reservation limit.
- Retain final masters and SHA256 recovery manifest outside Actions checkout in Path.home()/AntharesCortes/long-recovery or CORTES_LONG_STATE_DIR. Resume exact bytes without analysis/render. Resume fourth item even when three already registered. Corrupt checkpoints and partial pre-checkpoint legacy registries fail closed for reconciliation.
- Keep masters until full destination lifecycle verification; do not delete them in upload-failure finally. Successful SystemExit no longer writes a false traceback.

## Validation
31 focused tests passed: long policy, recovery, canonical lifecycle and YouTube duration policy. Syntax and diff checks passed. Actual FFmpeg video+audio append passed with two one-second synthetic inputs, measured output 2.0 seconds. No network publication or new E2E run was initiated.
GitHub main confirmed at 7a42deb7dd41856644ba98391b9270763f4928f6 after ordinary fast-forward push. GitLab main 1b6d6dd95f49b2b30f563a4a6ae3445f8e6c0e9f lacks these long-worker files; no blind reconciliation or mirror performed.
Daily workflow API reports active; cron 10:00 UTC corresponds to 06:00 America/Cuiaba. Active schedule is not proof of successful completion.

## Remaining limitation
No storage bytes were deleted and no 20 GB limit was raised. Current remote capacity and a successful complete real run are not proven. Existing pending masters must be drained/verified under canonical retention policy before any cleanup. Do not label this as full-system PROVEN.
