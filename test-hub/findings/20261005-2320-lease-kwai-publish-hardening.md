# Lease kwai-publish: harden media identity and safe publication state
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-1805-video-dedupe-distribuicao-incidente.md; zero temporal overlap per source is mandatory and file SHA-256 is only a second barrier.
FAILED_AVOIDED: do not touch kwai-login; do not use PC/MEmu; do not repeat Cloudflare private-runner deploy; do not treat workflow green, Publish click, Home return, or toast as confirmation.
SUCCESS_SIGNAL: publication module computes/stages verifiable media identity, selects imported media deterministically, emits structured pre/post-publish state, and never converts ambiguous post-Publish state into confirmed/retry-safe.
FAILURE_SIGNAL: deterministic media identity cannot be preserved through Android import/selection, or any path can mark confirmed without positive verification.
TEST_VALIDITY: this round is non-publishing/static+simulated until kwai-login exposes READY; no simulated result counts as real publication.
LEASE_AREA: kwai-publish
LEASE_EXPIRES: 2026-10-05T23:50:00Z

## Objetivo
Harden the independent Kwai publication chain before authenticated READY: media identity, deterministic import/selection, safe uncertain state, and structured evidence.

## Consequência
Other agents must not mutate kwai-publish while this lease is active. Read-only diagnostics remain allowed.
