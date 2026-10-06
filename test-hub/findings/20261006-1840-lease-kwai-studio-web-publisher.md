# Lease — Kwai Studio web publisher foundation
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-06
LEASE_AREA: kwai-publish
LEASE_OWNER: chatgpt-kwai-studio-web
LEASE_EXPIRES: 2026-10-06T19:20:00Z
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: main Chrome has an owner-authenticated Kwai Studio web session by non-secret UI evidence; canonical Android publisher safety/fencing contracts are proven.
FAILED_AVOIDED: no cookie/token extraction, no OTP/CAPTCHA bypass, no reuse of isolated logged-out profile, no irreversible publication in this lease.
SUCCESS_SIGNAL: repository gains a fail-closed Studio web publisher adapter that verifies authenticated Studio UI, prepares upload deterministically, and stops before irreversible submit unless an explicit fenced commit proof is supplied.
FAILURE_SIGNAL: adapter cannot distinguish authenticated/login surfaces or cannot stop before submit.
TEST_VALIDITY: static/local tests use synthetic DOM/fixtures only and never access credential stores or publish media.

## Objective
Add the distinct Kwai Studio web route while preserving queue fencing, prepare/commit separation, account verification, and fail-closed semantics.
