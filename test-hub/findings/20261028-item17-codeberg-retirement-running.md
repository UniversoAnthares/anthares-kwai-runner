# AOI item 17 — Codeberg legacy workflow quarantine
STATUS: RUNNING
AREA: architecture/codeberg-retirement
DATE: 2026-10-28
RUN: one scoped source quarantine; no production job
JOB: none
COMMIT: 82d1c420f3ec18d893809bcce78e8322a3757ec6
SUPERSEDES: none
LEASE: owner ChatGPT AOI item17; confined to 27 historical .forgejo/workflows and item17 docs, expires on terminal result.

BASELINE_PROVEN: GitHub remains canonical, GitLab and Hostinger Forgejo are recovery providers, Codeberg is suspended and ineligible. GitHub workflows with Codeberg destinations have job-level false gates (PRs #1727, #1736, #1791, #1809). Production publishers are separately controlled. Forgejo main Actions was disabled on the latest read; PR #1816 for the principal CI remains OPEN, adds a new independent workflow, and explicitly requires historical jobs to be quarantined before enabling Actions.
FAILED_AVOIDED: no Codeberg API calls, no social publication or promotion, no GitLab historic ref writes, no hoster Actions admin changes, no new plans/quotas, and no changes to sandbox workflows.
SUCCESS_SIGNAL: each inherited .forgejo/workflows job has an immutable false gate and each inherited workflow has no push, cron, or workflow_run trigger. Historical source retained. A targeted static check reports 27/27 safe, with GitHub operational Codeberg jobs already fail-closed.
FAILURE_SIGNAL: any historical job left callable, a new primary provider enabled, concurrent branch HEAD drift, syntax invalidity or GitHub write refusal.
TEST_VALIDITY: compare original full file blobs with changes, inspect exact triggers and job if-gates; one static verification only, followed by merge and main readback. No live publishing probe.
