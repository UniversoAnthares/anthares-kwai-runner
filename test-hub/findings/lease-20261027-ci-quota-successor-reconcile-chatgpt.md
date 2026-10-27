# Lease — reconcile successful CI GitHub quota fallback
STATUS: RUNNING
AREA: github-ci/gitlab-quota-successor-confirmation
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40510154187
JOB: none
COMMIT: 7c211f0f4e7ec50f74e43335076712df0d6599c3
SUPERSEDES: none

Owner ChatGPT. Scope: add passive authenticated Vercel endpoint to mark already-successful known GitHub rescue runs CONFIRMED in Neon; extend watcher only inside existing duplicate detection path, never dispatch extra workloads. Lease expires within 30 minutes.

BASELINE_PROVEN: source pipeline 2994547840 reserved in Neon and published GitHub CI run 40510154187 SUCCESS; manual exact-SHA reconciliation persisted FALLBACK_CONFIRMED. Automatic watcher now records FALLBACK_SUBMITTED after HTTP 204.
FAILED_AVOIDED: a workflow dispatch HTTP 204 does not prove remote success; do not treat queued/pending/error as published/succeeded. Never repeat a workflow to make a result look successful.
SUCCESS_SIGNAL: natural subsequent watcher observations can verify exact GitHub workflow_run id and completed success before transitioning FALLBACK_SUBMITTED to FALLBACK_CONFIRMED.
FAILURE_SIGNAL: mismatch of repo, workflow, sha or status never updates ledger.
TEST_VALIDITY: production remote read + Neon CAS only, no synthetic quota event or ad hoc test workflow.
