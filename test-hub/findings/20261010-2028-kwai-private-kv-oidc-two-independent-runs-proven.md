# Private Kwai session vault: deployed and cross-run durable
STATUS: PROVEN
AREA: session
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38083802289
JOB: 114305972140
COMMIT: ebbd6bdc632d7410ddda1ee32b7e499b22e5a9d9
SUPERSEDES: test-hub/coordination/20261010-mobile-private-vault-oidc.md

## Independent live proof
- Cloudflare Worker deployment 38083598163 succeeded after Node tests.
- Cloudflare /health remained v16, persistent_state=true, queue_bound=true, pc_fallback=false.
- Anonymous GET /kwai/session-vault?probe=1 returned 401; OIDC-authorized GitHub workflow 38083420842 returned KWAI_PRIVATE_VAULT_READY=1 and HAS_SESSION=0.
- First hosted run 38083658324 wrote non-sensitive canary into the real Cloudflare KV: KWAI_VAULT_CROSS_RUN_PERSISTENCE=BOOTSTRAP.
- Second independently provisioned hosted run 38083802289 read the first run's canary from Cloudflare KV: KWAI_VAULT_CROSS_RUN_PERSISTENCE=PROVEN, PRIOR_RUN_ID=38083658324, CURRENT_RUN_ID=38083802289.
- Dedicated probe workflow is strictly prohibited by code from reading/writing real encrypted session; it can only inspect readiness and update isolated run-ID canary.
- Publisher workflow has been rewired from public GitHub Actions cache to OIDC-authenticated Cloudflare KV GET/POST for client-side OpenSSL-encrypted session archives. It writes only after observed authenticated UI and exact account proof.
- No extra card, billing, user PC or manual step was used.

## Explicit remaining limitations
- No actual authenticated Kwai session archive exists in the vault yet; this is storage persistence proof, NOT authenticated session restoration proof.
- Real Kwai @lucasrosalem identity after two independent cloud app lifecycles remains NOT PROVEN.
- No independently verified real public Kwai post ID/URL. Publication remains fail-closed.
