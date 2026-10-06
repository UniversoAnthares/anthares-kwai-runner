# QA execution round — four immediate fronts
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37411496459; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37411367637
JOB: 112100709610;112100709753;112100709757;112100709795;112100709814;112100309198
COMMIT: 56e095f07b10c947dc5e6a5e8aae79990c89ca84
SUPERSEDES: none

## Objetivo
Execute the four fronts requested after the previous items 2-4 closure: TikTok OIDC/session investigation, Kwai login investigation, adversarial safety testing, and whole-project audit.

## Resultado

### 1. TikTok OIDC/session
The repository already contains the causal fix that adds `tiktok-reconcile-v2.yml` to the Cloudflare OIDC allowlist. The current deployed control plane still rejects that workflow: run 37411367637 returned HTTP 401 before the queue mutation. Therefore the remaining defect is deployment state, not the GitHub workflow code. The control-worker source in the repository contains the new allowlist entry, but there is no active deployment path available through the current connected tools. Do not retry the same reconciliation until that SHA is deployed.

Render publisher service is healthy and the latest deployment `c57af706086399b058690510cb20c289fa7ab468` is LIVE. The Render-side infrastructure is therefore separate from the current 401.

### 2. Kwai login
The active lease `20261006-0400-lease-kwai-login-final.md` remains authoritative and blocks competing mutation. The current Android 30-way harness continues to fail, so no competing repair was applied. The existing evidence still requires semantic Agent observation after a valid emulator/Agent boot; the previously rejected bare login URI and non-exported Activity routes were not repeated.

### 3. Adversarial safety
Run 37411496459 completed all five final SHA-dedupe cases successfully:
- PROVEN_SAME_SHA_DIFFERENT_SOURCE
- PROVEN_FAILED_SHA_RETRY_ALLOWED
- PROVEN_SAME_SHA_OTHER_PLATFORM
- PROVEN_CONCURRENT_EQUIVALENT
- PROVEN_SHA_CASE_NORMALIZED

This adds current evidence to the already-proven UNCERTAIN, fencing, heartbeat, recovery and publisher-boundary contracts.

The current TikTok reconcile run's HTTP 401 is an authentication/deployment failure of the harness/control boundary, so it is not counted against the reconcile hypothesis.

### 4. Whole-project audit
Recent findings show no unowned immediate implementation gap. Active mutation fronts are `kwai-login`, `control-publisher-integration`, and `tiktok-publish`; these are currently leased and therefore were not modified. The remaining project-level acceptance gaps are exactly the two real remote posts:
- `TIKTOK_REAL_REMOTE_POST=PROVEN`
- `KWAI_REAL_REMOTE_POST=PROVEN`

No new TODO/FIXME or alternate production-publish blocker was found in the repository search.

## Consequence
Next causal action for TikTok is deployment of the already-present Cloudflare OIDC allowlist SHA, followed by a read-only session/reconcile probe before any publication attempt. Next causal action for Kwai is completion of the currently leased Android Agent runtime/login repair. Do not create competing leases or repeat failed login/reconcile routes while those leases remain active.