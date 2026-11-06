# AOI 16 — Buffer Instagram: classificador de erro com leitura única
STATUS: PATCH_READY; ONE_SHOT_READBACK_PENDING
AREA: cortes-instagram-buffer-error-cause
BASE_MAIN_SHA: 23c01164ba02b510b8c35ad537a63f0f2936cbc6
GOVERNANCE_MANIFEST: 223433740e807a90
DATE_UTC: 2026-11-06
LEASE: lease-aoi16-instagram-buffer-error-cause-20261106.md — CLOSED on PR review / merge; no media mutations
BASELINE_PROVEN:
- Real readback #77 at 2026-11-06T21:24Z: all three existing Buffer posts have status=error; 0 confirmed and 0 new posts. Neon retains 7 uncertain (3 with Buffer IDs, 4 without).
- Buffer official GraphQL schema: Post.error: PostPublishingError, fields message (user-facing), rawError (internal), supportUrl. Only message is queried.
IMPLEMENTED:
- Query error { message } for already-recorded Buffer posts, classify into a fixed error category, and redact complete provider message from public logs. Retain channel, schedulingType and public permalink guards.
- Single use of an explicitly tagged merge push AOI16_BUFFER_ERROR_CAUSE_ONCE to run reconciliation readback without new-media writing: CORTES_RECONCILE_ONLY=1 and ANTHARES_SOCIAL_COMMIT=0.
- Other scheduled/push flows stay fail closed while CORTES_INSTAGRAM_BUFFER_PAUSED=true. No permanent new periodic task.
- Two focused isolated classification/redaction cases added; no publication tests.
FAILED_AVOIDED: no Buffer createPost, no media uploading, no manual Neon mutation or blind repost, no user PC, no new paid services.
SUCCESS_SIGNAL: one post-merge workflow run for the tagged push reports three REMOTE_POST_STATE values with error_category and new_posts=0. Provider error category determines next implementation action.
FAILURE_SIGNAL: absence of tagged push, GraphQL schema mismatch, auth denial, or missing remote evidence: remain PAUSED and avoid retry without changing the cause.
TEST_VALIDITY: code-path inspection and mocked unit cases; one readback only on merged tagged push; production result must be read from run logs.
NEXT: classify real Buffer errors and correct cause if possible without duplicating uncertain media.
ROLLBACK: normal revert of this PR; preserve durable Neon ledger.
COST_ADDED: R$0
