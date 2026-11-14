# Agent 06 — SpawnDroid capacity admission offline, fail-closed
STATUS: PARTIAL
AREA: kwai
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43596415122
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43596415122/job/132451763948
COMMIT: 20e5ac334262498a30235fb7e8a0f12e817ec088 (isolated branch)
SUPERSEDES: 20261114-agent06-spawndroid-admission-running.md

## Baseline
- Neon cortesqueue production deployment 77 is active.
- Kwai real proof has historically reconciled posts on both accounts; no cloud-SpawnDroid publisher is authorized.
- Main selector android_execution.cloud_cutover.enabled=false.
- Existing physical/MEmu backup routes are unchanged.
- GitLab main trails GitHub main; do not force mirror or promote from the peer without explicit content-equivalence reconciliation.

## Change
Isolated Python module with strict current Hobby snapshot, per-account real evidence requirements, separate phase timestamps, P95 and failure reserve, global 200-minute pool shared across both accounts, 15-minute bound, daily 100 cap, verified Neon snapshot, 06:00–23:00 exclusive local window and minimum effective spacing. Pure cancel-quota disposition forbids retry on unknown terminal/effect and treats HTTP 429 as concurrency. Code has NO transport for actual session cancellation, no posting side effects, no cutover flag, no secrets.

## Decisive CI evidence
Actions run 43596415122, job 132451763948, ubuntu-24.04:
- Python module/test compilation PASSED.
- 10 unittest contract tests PASSED; 0 errors/failures.
- SPAWNDROID_200M_MONTHLY_SHARED_POOL_GUARD_PASS
- SPAWNDROID_NO_BILLING_OR_STALE_QUOTA_FAIL_CLOSED_PASS
- SPAWNDROID_15MIN_SESSION_BILLING_GUARD_PASS
- SPAWNDROID_UNCERTAIN_NEVER_RESENT_PASS
- SPAWNDROID_EFFECTIVE_SPACING_AND_23H_EXCLUSION_PASS
- SPAWNDROID_NEON_ACCOUNT_CAP_100_PASS
- SPAWNDROID_CANCEL_FIRST_QUOTA_AND_UNKNOWN_SIDE_EFFECTS_PASS
- SPAWNDROID_OFFLINE_CONTRACT_SIGNALS=PASS

## Live read-only audit (not an executor test)
Production read-only SELECT: primary 623 confirmed, 0 queued, 0 unresolved; secondary 62 confirmed, 37 queued, 0 unresolved; both zero unexpired STARTED/QUEUED leases. Three historical primary records confirmed without remote_id remain and need separate reconciliation if addressed. No modification to queue. Read-only inventory of existing Windows services found legacy physical Kwai daemon processes; they were preserved.

## TEST_VALIDITY
Offline synthetic fixtures ONLY; no real SpawnDroid start, login, Android media transfer, posting or independent PC-off proof in this agent's changes. Capacity values produced by fixtures are NOT measured throughput.

## Result and production gate
PARTIAL; code and offline CI validated. The agents 01-05 must supply genuine APK, Android session, dual login, authorized media posting, independent public verification, and repeatable auth evidence. Integrate actual SpawnDroid cancel/terminal readback, Neon lease, media lifecycle, quota provenance, and migration rollback before promotion. Retain cloud_cutover.enabled=false until acceptance. No money spent, no publication induced, no producer disabled.
