# Lease — Kwai opaque local profile runtime continuation
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_OWNER: chatgpt-local-profile-runtime-v2
LEASE_EXPIRES: 2026-10-06T17:30:00Z
RUN: local authorized machine aic-lucas-pc
JOB: none
COMMIT: pending
SUPERSEDES: 20261006-1536-lease-kwai-local-profile-runtime.md

BASELINE_PROVEN: owner completed legitimate authentication in isolated Chrome profile AntharesKwaiChrome; profile persistent stores exist and isolated Chrome remains running. Earlier lease is expired.
FAILED_AVOIDED: no cookie/token extraction, no OTP/CAPTCHA bypass, no direct Activity/deep-link guessing, no coordinate spray, no publication.
SUCCESS_SIGNAL: authenticated Studio UI is verified from the opaque profile using non-secret UI evidence and a durable runtime wrapper is installed without exporting credential material.
FAILURE_SIGNAL: authenticated Studio cannot be verified or browser requires a new owner challenge.
TEST_VALIDITY: verification uses only process/window/UI state; session stores remain unread and unexported.

## Objective
Turn the authenticated isolated Chrome profile into a durable local Kwai browser runtime, verify account/UI state without exposing session secrets, and close kwai-login READY if the evidence is sufficient. Publication remains separately fenced.