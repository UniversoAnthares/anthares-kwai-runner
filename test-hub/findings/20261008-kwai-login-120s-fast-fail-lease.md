# Kwai login 120s fast-fail gate
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
LEASE_EXPIRES: 2026-10-08T20:30:00Z

## BASELINE_PROVEN
Android remote executor boot and login UI reach proven; real login not proven.

## FAILED_AVOIDED
Avoid previous 600-second unattended interaction wait and premature claim of authentication.

## SUCCESS_SIGNAL
Workflow has a 120-second upper bound on interactive readiness and emits explicit actionable failure; no automatic publish on login-probe workflow.

## FAILURE_SIGNAL
Workflow still permits 600-second unattended wait or publishes without separate acceptance.

## TEST_VALIDITY
Static workflow review and subsequent isolated fast-fail run; do not count infrastructure failure as authentication failure.

## Scope
Only login workflow and remote login script. No credentials, queue mutation, or publication. Respect existing agent if newer competing lease exists.
