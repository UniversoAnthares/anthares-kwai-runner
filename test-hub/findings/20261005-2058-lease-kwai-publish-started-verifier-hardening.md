# Lease kwai-publish: started handshake and verifier hardening
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: none

LEASE_AREA: kwai-publish
LEASE_EXPIRES: 2026-10-06T00:20:00Z

BASELINE_PROVEN: test-hub/findings/20261005-1927-qa-kwai-publish-safety-static-proven.md; test-hub/findings/20261005-1955-queue-confirmation-invariants-proven.md; test-hub/findings/20261005-2044-qa-kwai-started-oidc-contract.md; test-hub/findings/20261005-2047-qa-kwai-profile-loading-reconcile-rule.md; test-hub/findings/20261005-2050-qa-kwai-verifier-false-confirmation-gap.md; test-hub/findings/20261005-2054-kwai-uri-router-video-send-contract.md.
FAILED_AVOIDED: do not trigger real Publish while kwai-login lacks READY; do not treat Home/toast/generic recency marker as confirmation; do not click Publish before central started acknowledgement; do not repeat malformed workflow mutation 071c53e; do not infer post absence from Profile dynamic loading.
SUCCESS_SIGNAL: code path reaches READY_TO_PUBLISH before any irreversible action, central `/github-queue/started` OIDC acknowledgement is mandatory before commit, commit is isolated, verifier requires stable Profile + expected account + intended title, static validation proves ordering/fail-closed invariants, and real workflow remains quarantined.
FAILURE_SIGNAL: any code path can Publish with publication_started=0, generic marker can confirm, missing expected account can confirm, or static harness cannot prove ordering.
TEST_VALIDITY: this lease is code/static/simulated only until kwai-login exposes authenticated READY; no run in this lease may be called real publication proof.

## Objetivo
Close the crash/requeue duplicate window and false-confirmation verifier gap while preserving the current real-publication quarantine. Prepare a deterministic direct-video SEND probe as a separate non-publishing validation after the core lifecycle passes static checks.
