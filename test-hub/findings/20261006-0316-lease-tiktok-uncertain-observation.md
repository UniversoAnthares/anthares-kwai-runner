# Lease tiktok-publish observation-only reconcile after v2 UNCERTAIN
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: test-hub/findings/20261006-0314-tiktok-real-canary-v2-uncertain.md
LEASE_AREA: tiktok-publish
EXPIRES: 2026-10-06T03:45:00Z

BASELINE_PROVEN: run 37407210637 crossed publication_started with exact account ready, then Render was OOM-killed at 512Mi and returned 502; workflow marked CANARY_STATE=UNCERTAIN.
FAILED_AVOIDED: absolutely no /publish call and no retry. Causal action is observation-only profile inventory after the service restart.
SUCCESS_SIGNAL: authenticated read-only inventory finds exactly one new post attributable to the canary and returns its remote_id, allowing reconcile/complete without republish.
FAILURE_SIGNAL: inventory is valid and proves no matching/new canary post; job remains UNCERTAIN until absence is strong enough for an explicit future retry decision.
TEST_VALIDITY: Render service healthy, central session restored, exact account identity ready, and inventory operation itself completes without OOM/challenge/harness error.

## Objective
Resolve the existing UNCERTAIN canary by observation only. Never create a second TikTok publication from this lease.