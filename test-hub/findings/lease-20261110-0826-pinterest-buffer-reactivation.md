# CORTES Pinterest — recuperação operacional do publicador Buffer
STATUS: RUNNING
AREA: pinterest-buffer-publish
ITEMS: [16,21]; NUCLEO: CORTES; OTIMIZACAO: publicacao Pinterest
OWNER: chatgpt-pinterest-restore-20261110-0826
START_UTC: 2026-11-10T12:26:24Z
LEASE_EXPIRES_UTC: 2026-11-10T12:56:24Z
REPOSITORY: UniversoAnthares/anthares-kwai-runner
BASE_GITHUB_HEAD: 4dd28ee3372dad83a6e1cae59287f478d53adf58
WORKFLOW: .github/workflows/cortes-buffer-pinterest-cloud.yml
WORKFLOW_BLOB: fd7ed7a1fd8a9da904ab0b6f045a162eb3120ad3
GITLAB_PEER: 87307248/main, same file blob fd7ed7a1fd8a9da904ab0b6f045a162eb3120ad3
CURRENT_WORKFLOW_STATE: disabled_manually; no running/queued Pinterest workflow
EXPLICIT_OWNER_INTENT: Restore publication accounts one at a time, investigate deeply before changes.
BASELINE_PROVEN: Neon ledger 20 confirmed, 154 queued, 208 failed, 10 uncertain; Pinterest Buffer cooldown inactive; QA issue #507 closed on 2026-11-09 after receipt of prior real Pin. Four queued MP4 source HEAD requests: HTTP 200, content-type video/mp4. OAuth-linked Buffer channel and board IDs are pinned in source; old workflow includes OIDC+Neon CAS and a reconcile_only input.
FAILED_AVOIDED: Do not resubmit any uncertain Pin; preserve exactly-once CAS and cross-account owner; do not use Windows as media staging; do not reactivate other social workflows. Previous weekend run 41256664846 had buffer_weekday_enabled=false and created zero posts; current policy must be checked in live run. Preserve fixed board ID, do not invent second writer.
SUCCESS_SIGNAL: One run with reconcile_only=true confirms signed Neon and authenticated Buffer readback, followed by at most one authorized schedule and, once Buffer reports sent, public Pinterest URL + Neon confirmed CAS for account lucasyahn.
FAILURE_SIGNAL: HTTP 401/403, active Buffer cooldown/429, account/board mismatch, media 404, queue denial, invalid editorial data, bad secret, or no public receipt. If uncertain, preserve as uncertain and reconcile before retry.
TEST_VALIDITY: Only Github-hosted jobs count; a successful GitHub workflow or scheduled Buffer draft is not real publication proof. Document exact run ID, source URL/receipt and external link. Queue policy may legitimately block weekday/day budget; classify, not bypass.
SECURITY: No new services/runners/cron or paid resources, no secret logging, no publication of artificial media, no raw credential copying, no duplicate execution.
NEXT_ACTION: Enable existing Pinterest workflow only, run its read-only reconcile_only=true mode, examine official receipts, then invoke one normal run only after gates pass.
