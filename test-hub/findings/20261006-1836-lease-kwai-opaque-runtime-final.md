# Lease — Kwai opaque runtime final verification
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_OWNER: chatgpt-opaque-runtime-final
LEASE_EXPIRES: 2026-10-06T19:05:00Z
RUN: local authorized machine aic-lucas-pc
JOB: none
COMMIT: pending
SUPERSEDES: 20261006-1700-lease-kwai-opaque-local-runtime-v2.md

BASELINE_PROVEN: owner completed legitimate authentication in isolated Chrome profile AntharesKwaiChrome; persistent profile stores exist and prior lease expired.
FAILED_AVOIDED: no cookie/token/storage extraction, no OTP/CAPTCHA bypass, no hidden Activity/deep-link guessing, no coordinate spray, no publication.
SUCCESS_SIGNAL: non-secret browser/window/UI evidence proves authenticated Kwai Studio identity and opaque runtime remains launchable from the isolated profile.
FAILURE_SIGNAL: Studio is logged out, identity cannot be observed, or owner challenge is required.
TEST_VALIDITY: inspect only process/window/UI evidence; do not read or export credential/session stores.

## Objective
Finish kwai-login verification from the already authenticated isolated browser and record READY only if non-secret evidence supports it. Publication remains separately fenced under kwai-publish.
