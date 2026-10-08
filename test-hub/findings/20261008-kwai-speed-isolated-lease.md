# Isolated Kwai startup speed benchmark lease
STATUS: RUNNING
AREA: kwai-speed
DATE: 2026-10-08
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none
LEASE_EXPIRES: 2026-10-09T00:10:00Z

## BASELINE_PROVEN
Existing interactive workflow caches Android SDK but boots with -no-snapshot, re-downloads validated vault and has sequential preparation. Other agent owns active kwai-login work.

## FAILED_AVOIDED
No changes to kwai-login workflow or scripts while other agent is active. No blind Profile retries or unauthenticated browser route guessing.

## SUCCESS_SIGNAL
Independent benchmark workflow runs on GitHub hosted runner, records cache hit/miss and SDK, vault, emulator boot timing; no secrets, login, session or publishing.

## FAILURE_SIGNAL
Workflow syntax/runtime fails or timing signals missing.

## TEST_VALIDITY
Hosted workflow must execute; infrastructure failures remain harness failures.

## Scope
New isolated benchmark workflow only. Findings append-only. No user PC.
