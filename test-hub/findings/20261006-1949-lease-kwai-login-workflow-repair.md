# Lease — Kwai login workflow parser repair
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_OWNER: chatgpt-kwai-login-workflow-repair
LEASE_EXPIRES: 2026-10-06T20:19:00Z
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: interactive remote Android login workflow exists and cloud Android/tunnel harness was previously proven.
FAILED_AVOIDED: no Android auth-route guessing; repair only the duplicated YAML push key that currently makes workflow_dispatch unparsable.
SUCCESS_SIGNAL: GitHub accepts workflow dispatch and starts one serialized interactive login run.
FAILURE_SIGNAL: parser remains invalid or run fails before interactive surface.
TEST_VALIDITY: no publication occurs.
