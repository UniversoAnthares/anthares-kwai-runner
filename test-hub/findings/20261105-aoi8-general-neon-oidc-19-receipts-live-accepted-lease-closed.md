# AOI #8 — Neon free generalized OIDC quota controller: live accepted
STATUS: PARTIAL — controller complete; automatic new quota incident pending policy eligibility
ITEMS: [8]
AREA: ci-quota-failover/oidc-neon-general
DATE_UTC: 2026-11-05T03:38:33.789Z
LEASE: CLOSED
SUPERSEDES: lease-20261105-aoi8-general-neon-failover.md
OWNER: chatgpt-aoi8-20261105
SOURCE_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2115
SOURCE_MERGE: af27c40b9827c3b86348ed529c8b49809228ab87
SOURCE_NEON_BLOB: 07391501864ab039f0a9e06684a7d23383c62a80
FUNCTION: purple-flower-35918989 / br-crimson-unit-b89nau08 / cquotarec deployment 2, active completed, nodejs24
COST_ADDED: R$0
EXTRA_PUBLICATIONS: 0
DUPLICATE_RESCUES: 0

General controller serves /api/gitlab-reserve, /api/gitlab-ack, /api/gitlab-confirm. GitHub OIDC RS256/JWKS, trusted workflow/ref/event, exact three GitLab project mapping, remote terminal/quota validation, GitHub rescue completed/success check, shared Neon CAS and idempotent receipt. Historical exact endpoint retained at root for compatibility. All three unauthorized POSTs return HTTP401. The source code is versioned under infra/neon-ci-quota-confirm/index.mjs.

Watcher URL changed from disabled Vercel deployment HTTP402 to free Neon endpoint. Nine-test offline suite removed from every manual receipt; previous QA already passed. The workflow remains disabled_manually due to owner-wide consumption policy.

**LIVE ACCEPTANCE:** GitHub workflow_dispatch run 41962667638, job 127032426470, completed/success at SHA af27c40b9827c3b86348ed529c8b49809228ab87; log DRY_RUN=false, ANTHARES_RECONCILE_ONLY=true and EXACT_RECONCILIATION_CONFIRMED_BY_OIDC_CONTROLLER. Exact historical original GitLab pipeline 3005500025 and successful GitHub rescue 40942048873 were checked through signed OIDC plus GitHub API. The confirmed row remained stable; the operation returned idempotent success, with **zero new dispatch**.
Independent Neon read: 19 FALLBACK_CONFIRMED, zero pending rows. Workflow readback before/after: disabled_manually.

**Completion scope:** controller code and live OIDC receipt confirmed. **Global AOI #8 still PARTIAL** until a new naturally occurring quota event can exercise reserve and ACK and until policy permits enabling the scheduling watcher. Never synthesize a quota failure or bypass GitLab 403 and prior admin denials. Preserve R$0.
