# AOI #16 — Instagram Buffer: revalidação e reconciliação segura com a publicação pausada
STATUS: PARTIAL; READBACK_PATCH_READY
AREA: cortes-instagram-buffer-production-readback-gate
ITEMS: [16]
OWNER: ChatGPT AOI16 Instagram 2026-11-06
BASE_MAIN_SHA: b543931ec2c6febc3baf550509d361d8ffcf8d99
GOVERNANCE_MANIFEST: 223433740e807a90
DATE_UTC: 2026-11-06T20:00:00Z
LEASE_EXPIRES_UTC: 2026-11-06T20:40:00Z (closed)
TARGET_GITHUB: .github/workflows/cortes-buffer-instagram-cloud.yml
TARGET_GITHUB_BLOB_BEFORE: 0491cf3b3d453099dbf8e854ad3dc00a2a104c86
TARGET_GITLAB_MAIN_BLOB_BEFORE: 0491cf3b3d453099dbf8e854ad3dc00a2a104c86
PEER: GitLab project 87307248 main; peer finding path absent before write.
BASELINE_PROVEN:
- Instagram direct Meta Graph preflight run 41060169645 (2026-10-30): HTTP 401 Meta code 190 on graph.instagram.com and graph.facebook.com, alternate family unconfigured; unchanged login cause, no redundant identical auth probes.
- Instagram Buffer workflow currently disabled_manually. Existing code already offers workflow_dispatch reconcile_only=true, but job-level pause variable CORTES_INSTAGRAM_BUFFER_PAUSED=true skips even reconciliation; readback should be permissible without new publication.
- Buffer run 41233189204 (2026-10-31) confirmed three existing posts in Neon; later run 41254823878 (2026-11-01) confirmed zero and created no new posts. Buffer integration last proven at those dates.
- Read-only Neon 2026-11-06: 128 confirmed, seven uncertain (three with Buffer remote IDs, four without), 238 queued; no leased or started. Global Buffer weekday policy 2026-11-06: enabled (Friday), zero of twenty daily slots, no provider cooldown.
- GitHub Actions administrative capability missing from installed GitHub connector; remote GH CLI has no authenticated session; Browserless free quota 0 and no saved persistent session, so cannot enable disabled workflow in this chat.
FAILED_AVOIDED: do not activate a new publisher, bypass disabled workflow or owner pause, alter credentials, send test media, manipulate Neon ledger manually, reuse old Graph auth failure, or run extra tests.
SUCCESS_SIGNAL: existing Buffer workflow supports explicit reconcile_only dispatch even with pause variable=true; schedules and ordinary dispatch remain blocked when paused. GitHub PR merged, finding updated. No production run claimed.
FAILURE_SIGNAL: competing worker, unexpected target blob, security refusal, syntax invalid, provider quota or failed readback: stop and retain disabled state.
TEST_VALIDITY: code gate inspection and PR diff; no media, synthetic uploads, browser logins or workflow executions.
ROLLBACK: restore prior job-level `if` condition via normal PR if readback authorization is withdrawn.
COST_ADDED: R$0

## RESULTADO DA ATUAÇÃO
STATUS_FINAL: PATCH_READY; PRODUCTION_REACTIVATION_WAITING_EXTERNAL
LEASE: CLOSED
WORKFLOW_BLOB_AFTER: 69547ce3f4e150e57e53a14bc958610c47e284b3
IMPLEMENTED: for workflow_dispatch reconcile_only=true, allow the existing Buffer reconciliation job even when CORTES_INSTAGRAM_BUFFER_PAUSED=true. The production pause continues fencing scheduled and normal dispatch jobs.
STATIC_ACCEPTANCE: source readback checked intended condition and CORTES_RECONCILE_ONLY env selection. Five branch-condition truth-table cases PASS; no redundant publisher jobs or media test.
GITHUB_WORKFLOW_STATE: disabled_manually at last provider check 2026-11-06; no actions-management write permission is exposed by the connected GitHub tool. GH CLI remote has no login. No workflow toggled.
AUTH_STATE: 2026-10-30 last direct Graph preflight HTTP_401 META_CODE_190 on both Meta hosts; require real token reauthorization before direct publisher. Instagram alternate Graph token family not configured. Buffer integration separate, last successful authenticated readback 2026-10-31.
QUEUE: 128 confirmed / 238 queued / 7 uncertain. Three uncertain have Buffer remote post IDs, four have none. No leased or started currently. No manual database reconciliation.
CAPACITY: 2026-11-06 read-only Neon weekday=5, buffer_used_today=0, provider_cooldown=false; global Buffer daily capacity 20 shared among Buffer channels and may change.
NEXT_ALLOWED_OPERATION: authorize enable of existing Buffer workflow via GitHub Actions admin UI, preserve CORTES_INSTAGRAM_BUFFER_PAUSED=true for first reconcile_only run, verify remote Instagram permalink and canonical Neon CAS, then release PAUSED only for same single Buffer writer if receipts and quotas match. Keep direct Graph and independent instagram-auto-10day disabled.
SAFETY: no manual ledger rewrite, no media publication, no Workflow rerun, no credential disclosure, no subscription/credit/PC runner.
OTHER_PROVIDER: GitLab main held original workflow blob when patch prepared; synchronization is a separate governed change. Nothing is force-mirrored.
