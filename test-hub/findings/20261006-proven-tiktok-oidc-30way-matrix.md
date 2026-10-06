# TikTok OIDC 30-way matrix — authorization boundary proven
STATUS: PROVEN
AREA: tiktok-control-auth
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37418180347
BASELINE_PROVEN: earlier v12 real-publish chain received HTTP 401 before publication.
FAILED_AVOIDED: this run is not classified as a real publication merely because workflow display name is TikTok Real Publish or because the run is green.
SUCCESS_SIGNAL: authorized OIDC requests reach the deployed control and queue self-test returns all required safety invariants true across the diagnostic matrix.
TEST_VALIDITY: workflow minted GitHub OIDC tokens and called the deployed Cloudflare /queue-self-test endpoint.

## Evidence
The 30-replica diagnostic workflow completed successfully. Inspected replicas received authenticated responses from the deployed control plane. Responses reported true for dedupe, timeline overlap dedupe, premature-complete rejection, reconciliation evidence gates, concurrent uniqueness, single-job double-claim protection, owner-only lease renewal, repeated renewal, invalid/expired renewal rejection, generation increment, stale-generation started/complete/fail rejection, expired-unstarted recovery, started-expiry protection, failure requeue/recovery, confirmation recording, UNCERTAIN reconciliation, reconciled-job recovery, circuit-breaker threshold and reset.

## Classification
This closes the broad OIDC/control-plane authorization uncertainty. It does not establish TIKTOK_REAL_REMOTE_POST=PROVEN because no media publication, independent remote post verification, remote_id or confirmed production ledger was produced by this diagnostic matrix.

## Next
The real-publish workflow must be restored from diagnostic-matrix mode to the canonical single-canary production path under the active tiktok-publish owner/lease. The next canary must preserve exactly-one semantics and production proof gates.