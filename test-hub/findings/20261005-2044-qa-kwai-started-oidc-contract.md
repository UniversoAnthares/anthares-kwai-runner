# Kwai started handshake can use existing GitHub OIDC contract without new secrets
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: read-only contract audit
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2041-qa-kwai-started-handshake-gap.md; test-hub/findings/20261005-2020-control-plane-final-snapshot-proven.md
FAILED_AVOIDED: no new auth mechanism, no control token in GitHub, no publication, no mutation under the active kwai-publish lease.
SUCCESS_SIGNAL: current controller source explicitly allowlists kwai-real-publish.yml for GitHub OIDC and routes POST /github-queue/started to q.started after verified OIDC.
FAILURE_SIGNAL: workflow absent from allowlist or started endpoint requires an unavailable secret.
TEST_VALIDITY: source-contract audit against current main; production Worker remains stale until v12 deploy.

## Resultado
The current v12 snapshot allowlists `kwai-real-publish.yml` in GitHub OIDC verification. POST `/github-queue/started` verifies the bearer OIDC token, forces executor=`github`, and invokes `q.started`. Existing `tiktok-central-session-read.yml` supplies the repository-proven token acquisition pattern: `permissions: id-token: write` plus ACTIONS_ID_TOKEN_REQUEST_URL with audience `https://anthares-control.anthares1.workers.dev`.

## Consequência
The future Kwai publish workflow should reuse this exact OIDC pattern. After media/caption preparation and before the irreversible Publish click, request OIDC, POST `{id: KWAI_QUEUE_JOB_ID}` to `/github-queue/started`, require HTTP success and `ok:true`, then execute commit. Any failed/invalid started response must abort before Publish. No new GitHub secret is needed. This becomes usable in production only after the v12 Worker is deployed and positively version-verified.
