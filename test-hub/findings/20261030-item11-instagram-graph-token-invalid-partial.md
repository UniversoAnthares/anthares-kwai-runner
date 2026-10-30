# Item 11 — causa real da falha de autenticação oficial Instagram Graph
STATUS: PARTIAL
AREA: architecture/instagram-graph-auth
DATE: 2026-10-30
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41060169645
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41060169645/job/124077621637
COMMIT: f01a204f81058031954f2df208e79e354c2f0ebb
SUPERSEDES: 20261029-instagram-hosted-execution-proven-upstream-auth-open.md

## Verified
PR #1974 merged a diagnostic-only read-only GitHub-hosted probe. Production run 41060169645 on GitHub Actions 1000049842 returned:
- INSTAGRAM_GRAPH_CANDIDATE=direct configured=True
- INSTAGRAM_GRAPH_DIAG=direct:graph.instagram.com:HTTP_401:META_CODE_190:SUBCODE_0
- INSTAGRAM_GRAPH_DIAG=direct:graph.facebook.com:HTTP_401:META_CODE_190:SUBCODE_none
- INSTAGRAM_GRAPH_CANDIDATE=alternate configured=False
- INSTAGRAM_GRAPH_PROFILE_CHECK=4 (job remains failure, correctly fail-closed).

Meta Graph OAuth error 190 denotes invalid/expired/revoked access credential; no numeric subcode explains the exact expiry cause. Both supported Graph hosts rejected the configured token. Existing META_INSTAGRAM_* alternative not provisioned in GitHub. No Graph POST, token disclosure, Neon lease, or social publication. The preflight was already failing under Windows and Ubuntu before PR #1974.

## Existing functional redundancy
Hosted Instagram Buffer run 41036577042 succeeded with 6 SCHEDULED_IN_BUFFER and 4 reconciled confirmations. This proves Buffer account operation, NOT the direct Graph token; publishing source and Neon CAS remain untouched. WordPress read-only authenticated QA accepted in hosted run 41056710386, source=wordpress observations=0, sources_failed=0.

## Independent access checks / blocker
GitHub main existing token and second secret family probed. No META_INSTAGRAM alternate credentials. Browserless existing free account returned 401 quota exhausted, so do not purchase new quota. Connected browser tabs showed no Meta Developer/Instagram Account session. Anthares Remote/A RA disconnected, WinRemote PowerShell locked by another task; MeshCentral connected but remote command timed out in prior attempt. New valid official token requires an authorized OAuth login/reconnection and subsequent protected GitHub secret update. Preserve all active Buffer and publisher paths until the new token passes exact-account readback.

## Acceptance remaining
Replace INSTAGRAM_ACCESS_TOKEN with newly consented valid token for the exact account (using GitHub secret or an authorized existing secrets connection); validate on both appropriate Meta Graph host and exact ID and username without publishing. API error 190 is an auth blocker, not CI quota. No claim of direct Graph release, WordPress publishing credential rotation, or successful media publication.
