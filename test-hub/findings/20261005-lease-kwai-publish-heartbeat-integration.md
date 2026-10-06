# Lease kwai-publish heartbeat integration
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: adapter-heartbeat
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-2108-lease-kwai-publish-v16-closed.md
LEASE_AREA: kwai-publish-heartbeat
LEASE_EXPIRES: 2026-10-06T02:45:00Z

BASELINE_PROVEN: control v16 fencing PROVEN; kwai_queue_state.sh v16 adapter PROVEN with lease_generation and renew.
FAILED_AVOIDED: do not mutate Android/login or media hardening; do not Publish; do not use PC as runtime.
SUCCESS_SIGNAL: reusable heartbeat wrapper renews the active generation periodically, fails closed if renew fails, and static/simulated contract test passes without media publication.
FAILURE_SIGNAL: publication command can continue after heartbeat loss, generation is omitted, or wrapper can outlive child execution.
TEST_VALIDITY: shell/static/simulated only; no Kwai credentials, Android session, media or Publish action.
