# Lease — CI quota stale GitLab successor readback
STATUS: RUNNING
AREA: github-ci/gitlab-quota-successor-confirmation
DATE: 2026-10-30
RUN: none
JOB: none
COMMIT: branch fix/gitlab-quota-stale-confirm-20261030
SUPERSEDES: none

Owner: ChatGPT, item 5 of the 21 fixed Anthares items.
Scope: repair passive reconciliation of already-submitted and already-successful GitHub quota fallback runs. No new dispatch, no platform quota simulation, no publication.
Lease expires in 30 minutes.
BASELINE_PROVEN: Neon has 18 FALLBACK_CONFIRMED and 1 FALLBACK_SUBMITTED (gitlab:87307248:3005500025, 2026-10-29). Current watcher only searches GitLab pipeline failures from the last 90 minutes; once older, the existing passive confirmation branch is never revisited.
FAILED_AVOIDED: GitHub 204 is submission only. Confirm only exact successful workflow_dispatch successor, expected repository/flow/SHA, existing ledger reservation and OIDC. Never retry an uncertain remote action.
SUCCESS_SIGNAL: existing completion is reconciled by /api/gitlab-confirm, with exact success readback and zero new dispatches; regression tests pass.
FAILURE_SIGNAL: no matching successful successor or unavailable API leaves ledger unchanged.
TEST_VALIDITY: tests use mocked providers; production state must be separately verified.