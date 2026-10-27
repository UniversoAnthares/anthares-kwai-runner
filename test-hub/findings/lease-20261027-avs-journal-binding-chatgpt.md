# Lease — AVS GitHub App journal runtime binding
STATUS: RUNNING
AREA: architecture / avs-quota
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-video-studio/pull/32
JOB: none
COMMIT: cbace6427cb79a8d26b62b68325d95ed2f561eac
SUPERSEDES: none

## Owner and expiration
ChatGPT AVS isolated review session; expires 2026-10-27T17:00:00Z. Target exclusively private Anthares Video Studio PR #32 and Test Hub record. Do not alter production dispatch state or migrate Neon.

## Scope and outcome
Bind authenticated GitHub App factory to existing SQL auxiliary evidence wrapper only in explicit invocation, preserving SQL truth and fail-closed. No journal-health HTTP endpoint creation (prior security tool block), no credential readback, no incident write, no dispatch release. Preserve new main dispatcher concurrently.

## Evidence gates
Run Node tests locally in ephemeral sandbox and record output. PR remains draft until verified runtime. If source drift, conflict or security control denial, stop mutations and record partial finding.
