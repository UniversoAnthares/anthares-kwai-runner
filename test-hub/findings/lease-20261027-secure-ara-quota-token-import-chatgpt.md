# Lease — securely transfer validated CI secret to Anthares Remote
STATUS: RUNNING
AREA: ci-quota/secure-credential-transfer
DATE: 2026-10-27
RUN: GitHub Actions watcher 40549166660 validated AppVeyor account-v1
JOB: none
COMMIT: aee555c7915000a050a02e4baa5dbe986f037f94
SUPERSEDES: test-hub/findings/20261027-ara-quota-standby-rsa-production-auth-live-partial.md

Owner ChatGPT, 30m. Install sealed RSA-3072/OAEP encrypted credential transfer from already-authorized GitHub Actions secret to existing Anthares Remote SYSTEM DPAPI secret. No plaintext in Vercel, Neon, repo, logs or connector arguments. Reuse pinned RSA public JWK on Vercel. Separate restricted Neon table with TTL and receive-once. No other agent tokens, publications, billing or external CI build execution. Preserve existing ARA task and fencing.
Success: GH controlled run verified AppVeyor v1 auth, encrypted payload staged, ARA authenticated consume and local DPAPI protected AppVeyor token, subsequent provider-readonly status VERIFIED. No quota-cancel incident is fabricated.
Failure: if transport rejected or unclear, do not dump secrets or use clipboard, leave GitHub secret as sole configured credential.
