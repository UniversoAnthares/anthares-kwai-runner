# AVS GitHub App journal binding — isolated proof
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-video-studio/pull/32
JOB: dpl_DkqtyThA21PaP7ZCUkpnSuonRycM
COMMIT: 9f4bf6ec2ffb3968a4648d7d9f8d1a07434b01bb
SUPERSEDES: none

## Objective
Bind GitHub App installation-token adapter to AVS quota auxiliary evidence wrapper without enabling dispatcher or treating GitHub evidence as a Neon SQL fence.

## Result
GitHub PR #32 updated with createIndependentQuotaEvidence factory in quota_durable_fallback.mjs; tests in quota_github_app_auth.test.mjs. Node execution via authorized Anthares Remote: 6 tests, 6 pass, 0 fail, exit 0; temporary files cleaned. Vercel Staging dpl_DkqtyThA21PaP7ZCUkpnSuonRycM reports READY for exact SHA. No production deployment performed by this operation.

## Limitation
The new factory is opt-in and not yet proven invoked by a live worker. GitHub App real credential exchange, write-once incident creation/readback, Neon migration/fencing, provider remote stop, and end-to-end authorization remain unproven. GitHub PR #32 remains draft and its baseline trails current main; reconcile before merge. A previous attempt to create api/journal-health.mjs was blocked by ChatGPT GitHub tool safety policy and was not repeated.

## Consequence
Keep DISPATCH_PAUSED. Do not mark journal or quota failover production-operational from this static/mock evidence.
