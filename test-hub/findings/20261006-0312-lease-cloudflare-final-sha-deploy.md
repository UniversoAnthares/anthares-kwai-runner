# Lease cloudflare-control final SHA dedupe deployment
STATUS: RUNNING
AREA: cloudflare-control
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: cloudflare-control
EXPIRES: 2026-10-06T03:40:00Z

BASELINE_PROVEN: production Worker v16 is PROVEN; repository SHA-256 secondary dedupe barrier passed 5/5 in run 37407161986; public-runner deploy 37407186640 stopped before Wrangler solely because CLOUDFLARE_API_TOKEN is absent.
FAILED_AVOIDED: do not retry tokenless public-runner deployment. Causal change is to use the already-proven one-time Wrangler OAuth console path from an authorized machine, with production runtime remaining entirely Cloudflare-hosted.
SUCCESS_SIGNAL: Wrangler deploy completes, /health still reports v16 persistent queue/no-PC properties, and deployed controller contains the SHA dedupe snapshot.
FAILURE_SIGNAL: deploy rejected or post-deploy health/control invariants regress.
TEST_VALIDITY: fresh repository checkout at current main, Wrangler authenticated identity available, and no partial deploy is classified as success.

## Objective
Activate the already-proven final SHA dedupe controller snapshot in production without introducing any PC runtime dependency.