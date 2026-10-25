# CORTES-ISO-06 — signed release intent gate / local isolated QA
STATUS: PARTIAL
AREA: architecture / iso06-release-authority-offline
DATE: 2026-10-25
RUN: local container Python unittest (23 tests PASS); no production deployment
JOB: iso06-release-proof-20261025
COMMIT: anthares-clipper platform/iso06-signed-release-authority-20261025
SUPERSEDES: lease-20261025-iso06-release-proof-chatgpt.md
LEASE_AREA: iso06-release-authority-offline
LEASE_STATUS: CLOSED (no further code mutation on this lease)

## BASELINE_PROVEN
Governance Windows preflight local f6fc9ca59a96e451 PASS, policy audit 218 projects/0 failures; remote GitHub main manifest 2e28d54043d6bad1 with divergent INDICE.md, not overwritten. Independent scope from CI-01 credential-scope and security-denied CI workflow modifications.
Production legacy workflow social-api-publisher.yml still provides Instagram, Threads and X secrets to same job, including shared ANTHARES_VIDEO_SECRET.
PR #1332 remains draft IAM/receipts; PR #1367 remains draft diagnostic environment; no live two-principal denied/allowed proof.

## IMPLEMENTED
New code-only, dormant components on isolated platform branch:
- ci/network_release_identity_gate.py (blob sha 9afd70ba5fd667766ad8cb8e2b3ea5d8fadb73ad)
- tests/test_network_release_identity_gate.py (blob sha 09de0f96d068f6d4b13d70600f8dec7d4ac7a8b8)
Controller-authored signed intents are bound to network, account, repository, workflow, environment, branch/ref, source SHA and artifact SHA256. Rejects mixed/weak signing keys, changed subject, wrong-network replay, forged MAC, malformed claims and expired approvals. Atomic single-host review receipt uses O_EXCL + fsync; no distributed lease inferred. Verify signature again at receipt-write boundary. No credentials stored and no new workflow invoked.

## TESTS AND DECISIVE EVIDENCE
Python unittest in isolated container: Ran 23 tests, OK, exit 0. Git SHA1 content-object verification matched GitHub exact blobs 9afd70ba... and 09de0f96... for BOTH tested files. Tests include signed same-network review candidate accepted but deploy_authorized=false, Threads claim as Instagram rejected, Instagram key as Threads rejected, identity ref/environment/account/repo/workflow substitution denied, tampered SHA denied, expired claim denied, nonce duplicate denied, no receipt for foreign-network attempt. Test fixture principals are synthetic; NOT real IAM enforcement.
Attempt to write isolated Windows QA files through Anthares Remote was explicitly refused by security configuration. No alternative remote channel attempted. Prior unauthenticated raw.githubusercontent.com fetch failed 404, then stopped; local offline validation was independent.
Production, publisher, credentials, IAM rulesets, sessions, live queue, database, deployment and Windows files all unchanged by code-test work.

## ACCEPTANCE STILL OPEN
1. Independently validated OIDC workload identities from the target deploy provider, per-network trust store and protected signing key custody.
2. Configure real independent account-scoped environments/secret permissions and deny principal B cross-network write/installation by provider IAM, with real audit logs.
3. Enforce this authorization in ALL productive deploy paths, backups/fallbacks and promotions, protected approvals, leases/fencing, immutable artifact verification, approved rollback and independent canary.
4. Migrate away from mixed-provider social-api-publisher.yml without affecting active publication or account-specific state.
5. Reconcile GitHub/local governance INDICE.md divergences before sync.

## CONCLUSION
ISO-06 remains PARTIAL. New verified library is a component of isolated release authority, not an integrated provider policy. Never report unit test as production IAM proof, and never use a security refusal workaround.
