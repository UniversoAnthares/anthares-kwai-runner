# AOI #16 — Remover duplicatas idênticas do alerta Codeberg #1
STATUS: RUNNING
AREA: qa-p0-duplicate-issues-codeberg-source-1
DATE_UTC: 2026-11-09T01:57:28.363Z
LEASE_EXPIRES_UTC: 2026-11-09T02:27:28.363Z
OWNER: chatgpt-aoi16-codeberg1-dedupe-20261109
ITEMS: [16]
BASE_GITHUB_HEAD: 7e6ea06e76214da6803e5f381f8d0e9762b17068
PEER_CHECK: GitLab project 87307248 main file absent (404), read only; no GitLab mutation.
BASELINE_PROVEN: GitHub issues #756 #773 #954 #1059 #1565 all open, identical title, body, 24-char fingerprint 3ac3e1aca56a2d755251cbd6, identical stage codeberg_github_hosted_queued_over_20m and identical Codeberg evidence /issues/1. #1565 has 5 historical comments; retain it as canonical, preserving all comments; the other four have 0 comments.
FAILED_AVOIDED: No media, retries, dispatch, workflow activation, session, secrets, Neon, Codeberg or runner actions.
SUCCESS_SIGNAL: Close only GitHub duplicates #756 #773 #954 #1059 with state_reason=duplicate, leave original bodies/labels intact. Keep #1565 open with five comments and original evidence.
FAILURE_SIGNAL: Changed issue body/state/fingerprint/identity, competing lease or missing canonical -> abort without write.
TEST_VALIDITY: Exact provider issue metadata and terminal readback only; no publish or CI.
COST_ADDED: 0.
ROLLBACK: Reopen any wrongly classified duplicate; no contents removed.
NOTE: Closing duplicates does not fix the source Codeberg/GitHub runner fault; AOI #16 remains PARTIAL.
