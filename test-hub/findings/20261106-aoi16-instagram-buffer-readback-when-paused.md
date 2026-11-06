# AOI #16 — Instagram Buffer: revalidação e reconciliação segura com a publicação pausada
STATUS: RUNNING
AREA: cortes-instagram-buffer-production-readback-gate
ITEMS: [16]
OWNER: ChatGPT AOI16 Instagram 2026-11-06
BASE_MAIN_SHA: b543931ec2c6febc3baf550509d361d8ffcf8d99
GOVERNANCE_MANIFEST: 223433740e807a90
DATE_UTC: 2026-11-06T20:00:00Z
LEASE_EXPIRES_UTC: 2026-11-06T20:40:00Z
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
