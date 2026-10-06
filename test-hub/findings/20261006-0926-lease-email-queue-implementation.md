# Lease — email queue implementation
STATUS: RUNNING
AREA: email
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

OWNER: chatgpt-email-queue
EXPIRES: 2026-10-06T13:55:00Z
SCOPE: local/provider-neutral email queue code and tests only; zero real sends.

BASELINE_PROVEN: 20261006-0850-email-infrastructure-baseline-proven.md; DNS/provider baseline proven and docs/email-delivery-architecture.md exists.
FAILED_AVOIDED: no campaign send, no recipient import from unapproved sources, no provider secrets, no Gmail/Hostinger bulk transport assumption.
SUCCESS_SIGNAL: executable tests prove normalized-email dedupe, provenance retention, suppression-before-dispatch, campaign+recipient approval gate, provider isolation and gradual batch cap.
FAILURE_SIGNAL: any test can dispatch without both approvals or suppression can be bypassed.
TEST_VALIDITY: tests use an in-memory fake provider only and perform zero network send calls.
