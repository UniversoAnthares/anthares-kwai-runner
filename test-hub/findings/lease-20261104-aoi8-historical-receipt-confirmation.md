# AOI #8 — lease de reconciliação histórica restrita
STATUS: RUNNING
AREA: github-ci/gitlab-quota-successor-confirmation
DATE_UTC: 2026-11-04T20:47:01.442Z
EXPIRES_UTC: 2026-11-04T21:17:01.442Z
OWNER: chatgpt-aoi8-20261104
BASE_HEAD: 9352c070f32e8d8726f63e9633ea8fe028df0ee9
SUPERSEDES: lease-20261030-ci-quota-stale-reconcile-chatgpt.md (expirado)
ITEMS: [8]

BASELINE_PROVEN: GitHub run 40942048873 completed/success, SHA 94ba06e628d0b1ba0bdfeabbdfd9a00b86508759; Neon attempt gitlab:87307248:3005500025 remains FALLBACK_SUBMITTED (18 confirmed, 1 submitted). Deployed Vercel gitlab-confirm validates GitHub OIDC, exact successor flow and existing CAS reservation. PR #2011's 72h GitLab scan cannot reach 29/10; GitLab source read currently 403/404.
FAILED_AVOIDED: no redispatch, no GitLab retry, no direct Neon SQL state promotion, no media publication, no extra paid plan, no alternate channel to bypass GitLab 403.
SUCCESS_SIGNAL: exactly one pre-existing, successful workflow_dispatch run verified by Vercel /api/gitlab-confirm; conditional Neon row becomes FALLBACK_CONFIRMED with receipt matching and no new fallback run.
FAILURE_SIGNAL: OIDC missing, mismatch SHA/project/run, Actions disabled, quota unavailable or reservation mismatch => fail closed; no external side effects.
TEST_VALIDITY: static/isolated Python contracts establish no redispatch. Production receipt independently required.
SCOPE: augment PR #2011 with explicit one-off, bounded reconciliation-only path; no independent new CI dispatcher or universal quota claim.
