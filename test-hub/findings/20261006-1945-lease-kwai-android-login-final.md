# Lease — Kwai Android login final attempt
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_OWNER: chatgpt-kwai-final
LEASE_EXPIRES: 2026-10-06T20:15:00Z
RUN: GitHub Actions kwai-interactive-remote-login
JOB: pending
COMMIT: pending
SUPERSEDES: 20261006-1836-lease-kwai-opaque-runtime-final.md

BASELINE_PROVEN: required repository configuration names are present and the existing Android login workflow consumes them without logging values.
FAILED_AVOIDED: no session extraction, no challenge bypass, no deep-link guessing, no coordinate spray.
SUCCESS_SIGNAL: workflow confirms automatic login and saves session state.
FAILURE_SIGNAL: provider requests owner interaction or automatic login remains unconfirmed.
TEST_VALIDITY: validated Kwai package installs and Android reaches interactive UI.
