# KW-09 — hosted credential authentication, existing workflow only
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-11-09
RUN: pending workflow_dispatch
SUPERSEDES: 20261108-kwai-mobile-auth-identity-timeout.md

BASELINE_PROVEN: Hosted Android and protected login window operational in GitHub run 42519025289; encrypted Cloudflare vault empty and two independent restores not reached.
FAILED_AVOIDED: Repeating an unattended 20-minute interactive window without an automatic authentication attempt.
SUCCESS_SIGNAL: KWAI_HOSTED_ACCOUNT_VERIFIED=1, KWAI_MOBILE_SESSION_STORED=1 and both independently restored identity proofs.
FAILURE_SIGNAL: Authentication challenge, rejected credentials, UI failure, absent session or restore failure.
TEST_VALIDITY: One credential attempt using existing GitHub secrets only, no password output; no queue lease, post or publication performed by auth workflow. Windows publisher unchanged.
