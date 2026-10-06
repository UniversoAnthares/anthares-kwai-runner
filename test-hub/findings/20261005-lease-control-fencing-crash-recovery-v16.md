# Lease cloudflare-control: fencing and crash recovery v16
STATUS: RUNNING
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: control-v16
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: cloudflare-control
LEASE_EXPIRES: 2026-10-06T02:30:00Z

BASELINE_PROVEN: production v15 repeated renew heartbeat PROVEN by run 37395158585 / job 112049276852.
FAILED_AVOIDED: do not touch kwai-publish or kwai-login; do not use PC as runtime; do not repeat public-runner Cloudflare deploy without token.
SUCCESS_SIGNAL: monotonic fencing generation per lease; stale holder mutations rejected after reassignment; crash before publication_started safely requeues; crash after publication_started becomes uncertain and never blind-requeues; authenticated production self-test HTTP 200.
FAILURE_SIGNAL: stale generation can renew/start/complete/fail, or started expired job can become queued automatically.
TEST_VALIDITY: isolated __selftest_* jobs only; production deploy uses authenticated Wrangler console from fresh clone.
