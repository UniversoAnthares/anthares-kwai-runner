# R07.6 ISO-03 — multiprocessor writer QA, eight races, one effect per race

STATUS: PROVEN
AREA: architecture / tiktok / kwai / CORTES-ISO-03
DATE: 2026-10-25
OWNER: chatgpt-ops
JOB: r07-iso03-concurrency-20261025
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40206885192
JOB: 121209628097
COMMIT: f02a022be349151fa0569cb9e6a06e8b9dd465aa
SUPERSEDES: none

## BASELINE_PROVEN
R07.6 item 10 requires testing single writer and fencing for one account in isolated QA, with the Kwai fanout remaining in shadow. Existing draft PRs #1338 and #1369 established the SQLite QA broker, thread contention and POSIX-UID ACL exercises. This experiment is an **independent process-concurrency layer** on top of branch `chatgpt/iso03-qa-uid-import-fix-r0723` and does not modify earlier files.

## FAILED_AVOIDED
Never perform destructive testing on Neon, a live publisher, a posting queue, social accounts or production OS identities. No uncertain receipt is retried. Without verified IAM, DB row-level negative principal tests and other preconditions, never declare production isolation or cutover allowed.

## SUCCESS_SIGNAL
Eight iterations of six distinct Python operating-system child processes (48 child processes total) race to claim a single pre-enqueued TikTok QA event per iteration after a synchronized filesystem barrier. For each event exactly one winner records one SQLite effect; other five candidates lose. Total 8 confirmed, 8 effects and 0 cross-network effects. An uncertain item cannot be claimed or confirmed without evidence, a Kwai claim is denied on TikTok, and a Kwai fanout produces 4 non-executable shadow intents.

## FAILURE_SIGNAL
Any execution returns a nonzero exit status, more than one winner per event, any duplicate effect, a cross-network effect, unverified UNCERTAIN replay, actual publisher invocation, or an orphan subprocess after cleanup.

## TEST_VALIDITY
- Cloud VM independent Floot (existing project): `python3 -B -m unittest discover -s control_plane -p test_r07_iso03_multiprocess.py -v` => 3/3 PASS, exit=0, 0.425 sec test wall time. Source SHA256 `515b56375d27e570941ce66a1f4e3df0e47d51e753011cf4e63ad2c13bfe7a18`; disposable temp tree removed in `finally`.
- GitHub Actions real hosted Ubuntu runner: run 40206885192, job 121209628097, all steps SUCCESS; `Ran 3 tests in 0.630s; OK`. Markers `ISO03_QA_ONLY=1`, `ISO03_CUTOVER_AUTHORIZED=0`, `ISO03_PUBLISHER_INVOKED=0`. Code revision `f02a022be349151fa0569cb9e6a06e8b9dd465aa` before this finding-only commit.
- Parallel Anthares Control Plane workflow run 40206885159 completed SUCCESS on same SHA.
- Test module Git blob SHA `fb61917f45d3b2ac2f67b974a9dd69954e2c10b7`; CI workflow Git blob SHA `1185933b395d7aa6942986eac49a7290b0177422`.

## Result and limits
**CORTES-ISO-03 PROVEN in the R07.6 independent QA package for the one TikTok QA cell**, with Kwai unchanged; not PROVEN for production single-writer, ACL/IAM, Neon RLS, GitHub environment permissions, real publication or failover. The test and workflow live only in draft PR #1381 (stacked, not merged or deployed). Existing PRs #1338/#1369/#1371 remain unchanged. No secrets, token values, network calls, posts, paid resources or database writes outside the temp QA fixture.

## Rollback
Close draft PR #1381 without merging; its two files and this append-only evidence file have no production coupling. Clean up of processes and temporary SQLite QA root is in try/finally. Preserve other agents' branches and running jobs.
