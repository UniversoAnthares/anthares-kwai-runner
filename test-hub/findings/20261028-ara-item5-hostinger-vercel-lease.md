# ARA — Hostinger notification emitter, Vercel (item 5)
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / vercel-ara-primary
DATE: 2026-10-28
RUN: none
JOB: user-authorized completion item 5
COMMIT: e32a2bba7ad086d5e0eccd7b7b8d6a54b9e20fda
SUPERSEDES: none
LEASE: 2026-10-28, maximum 30 minutes from creation; only this integration branch.

## BASELINE_PROVEN
Production Vercel READY: e32a2bba7ad086d5e0eccd7b7b8d6a54b9e20fda, same router blob cd59e393d76068df4ad3236da4aec1fa716c741e; protected Production variable ARA_WAKE_NOTIFY_SECRET configured; Hostinger wake broker owner accepted (ITEM4_HOMOLOGADO). GitHub PR #1808 contains an independent Cloudflare transport and concurrent C8 subscriber work, without production deployment.

## FAILED_AVOIDED
Patch only Hostinger emission on isolated branch from exact production commit, preserve concurrent main and Forgejo OIDC. Do not deploy a parallel Cloudflare broker. No queue/schema/lease/heartbeat changes. Default-OFF flag and rollback to production deployment dpl_GnZzoFiPi5BKGCZGayLJD7kU3oet. Never commit or log secret values.

## SUCCESS_SIGNAL
Syntax/tests PASS; Vercel production READY at exact commit including notifier; protected Production flag configured; one harmless canonical MCP command recorded in Neon, confirmed through ARA and Hostinger sequence increment.

## FAILURE_SIGNAL
HEAD drift, HTTP auth failure/503/timeout, failed deployment or regression, missing notification or inconsistent job state.

## TEST_VALIDITY
CI alone or READY alone are insufficient. Keep emission disabled until integration is verified. End lease via append-only finding with exact evidence.
