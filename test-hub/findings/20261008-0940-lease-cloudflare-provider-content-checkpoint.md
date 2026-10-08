# Cloudflare provider content checkpoint repair lease
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: 8b641821d7819237d6ea77a653e69b2a9193cb58
SUPERSEDES: none

BASELINE_PROVEN: GitHub/GitLab repository histories were converged without force push; Python provider-router now accepts verified equivalent content IDs while preserving exact active-provider HEAD fencing; Cloudflare JS router still compares commit IDs only.
FAILED_AVOIDED: do not weaken same-provider fencing; do not deploy from an unreviewed/stale file; do not use live publication as a router test.
SUCCESS_SIGNAL: Cloudflare JS policy supports explicit content_id checkpoints across peer providers, rejects mismatched content, still recognizes BLOCKED_QUOTA as unavailable, and its self-test proves those cases.
FAILURE_SIGNAL: JS syntax/test regression, loss of divergence blocking, or stale-base write rejection.
TEST_VALIDITY: current router file was read from both GitHub and GitLab and was byte-equivalent before mutation; write must use the current GitHub blob SHA and peer sync only after tests.
Lease expires 30 minutes after acquisition.
