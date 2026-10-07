# Lease — Kwai authenticated local profile runtime
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_OWNER: chatgpt-local-profile-runtime
LEASE_EXPIRES: 2026-10-06T16:06:00Z
RUN: local authorized machine aic-lucas-pc
JOB: none
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: owner completed legitimate authentication in isolated Chrome profile AntharesKwaiChrome; profile and persistent browser stores exist; isolated Chrome process is running. Prior kwai-login leases expired before this lease.
FAILED_AVOIDED: no hidden Activity/deep-link guessing, coordinate spray, OTP/CAPTCHA bypass, cookie/token extraction, or parallel publication.
SUCCESS_SIGNAL: opaque authenticated profile is usable as a local browser runtime and identity/authenticated Studio surface can be verified without exposing session secrets; no publication occurs.
FAILURE_SIGNAL: profile no longer opens authenticated Studio or provider requires fresh owner challenge.
TEST_VALIDITY: isolated profile/process exists and verification does not read/export Cookies, Local Storage, Session Storage, IndexedDB, passwords, tokens, or other credential material.

## Objective
Close kwai-login READY using the already owner-authenticated isolated browser as an opaque runtime. Preserve session material in place and verify only non-secret UI/account state. Publication remains separately fenced under kwai-publish.
