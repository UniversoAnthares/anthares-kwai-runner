# Lease — quota cancel redundant Anthares Remote
STATUS: RUNNING
AREA: Anthares Remote / CI quota cancel
DATE: 2026-10-27
RUN: pending
JOB: pending
COMMIT: 14c19971109644eda731646e07b23de4344ae84a
SUPERSEDES: none

Owner ChatGPT. Objective: Windows SYSTEM scheduled fallback independent of GitHub Actions; signed caller uses Vercel central Neon claim and exact provider cancel receipt. Scope new Windows script and api/provider-cancel.mjs, deployed only after review. Existing GitHub watcher untouched.
Proven baseline: GitHub watcher run 40530808280 success but AppVeyor=NOT_CONFIGURED/Bitrise=NOT_CONFIGURED; ARA Windows SYSTEM active; quota controller Neon READY.
Safety: no secrets in repo/issue/log, no fabricated quota, no parallel active claims, no replay, no auto-retry after uncertain, no publication.
Acceptance: live installed scheduled task + health readback, new Vercel verified auth endpoint, deployment includes both routes; credential status marked truthfully.
