# Test Hub — CORTES cloud media staging extension
STATUS: RUNNING
AREA: architecture
UTC_DATE: 2026-10-24
JOB: ChatGPT/cortes-cloud-media-f3-staging-20261023
BASE_SHA: 74a18288a4c8748ee6a6d474704505bbe76c1938
OWNER: ChatGPT
LEASE_SCOPE: new cloud-media ingestion/transcription/long-rendering modules and isolated tests on feature/cortes-cloud-drive-replication-20261023; no publisher, cron, GitHub Actions, or live migration modifications
LEASE_DURATION: current focused implementation only, max 30 minutes after finding creation
POLICY_VERSION: 898630c1c5143f34
PEER: GitLab anthares-clipper feature branch absent; main is separate history and unchanged
PREFLIGHT: Anthares Remote governance policy.py preflight exit zero

## Baseline
83 offline tests (82 passed, 1 skip), PR #190 draft. Dedicated OAuth clients absent for all 3 Windows rclone remotes. External render and independent fallbacks not proven. SQL Neon only QA branch.

## Success gates
New code and tests only; source selection still locked per cortes_cycle_policy; full useful content partition without artificial cap; no social posting or deletion. Record output SHA and exact test totals.

## Failure gates
Abort if branch HEAD diverges without reconciliation, Test Hub same-scope conflict emerges, Google Drive OAuth unavailable, external quota exhausted or true rendering unsupported. No production promotion without E2E proof.

## Rollback
Keep new files exclusively on feature branch, never merge automatically. Do not modify existing publisher state or credentials.