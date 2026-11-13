# Kwai physical publisher: v3 pacing handshake — isolated CI
STATUS: RUNNING
AREA: kwai
DATE: 2026-11-13
RUN: none
JOB: none
COMMIT: e866a388eefdbf53d5b6723b4f9991591e07caf0
SUPERSEDES: none
OWNER: ChatGPT continuation of Oracle/Kwai pending tasks
LEASE_SCOPE: tools/kwai_physical_queue_daemon.py and tools/kwai_canonical_runtime_regression.py, branch fix/kwai-physical-pacing-v3-20261113; no live service or ledger mutation.

## BASELINE_PROVEN
Production Neon cortesqueue deployment 76 uses pacing_version kwai-public-post-proportional-06to23-v3. Existing Windows publisher process starts on 2026-11-12 and its current source demands kwai-public-post-proportional-v2. Windows log at 2026-11-13 18:33 MS shows PUBLICATION_PACING_VERSION_REQUIRED and no new lease. Canonical Neon has 16 queued primary and 52 queued secondary; no started/uncertain.

## FAILED_AVOIDED
Do not run Android on GitHub, alter queued items, submit a new post for testing, or reenable Oracle, CutMotions, paid infrastructure or sponsorship. Do not change local Android or restart the current publisher as part of this CI-only change.

## SUCCESS_SIGNAL
Offline regression verifies server v3 and a local hard gate at 06:00, mismatched clock rejection, due after verified last post, and deadline at 23:00. The existing Kwai workflow must pass; code remains in a review branch until integrated.

## FAILURE_SIGNAL
CI test fails, v2 still accepted, publication before 06:00, invalid server window accepted, or any test sends media or changes production.

## TEST_VALIDITY
Static source and an AST-isolated Python function execution with injected in-memory schedule. No credentials, media files, network, phone, database writes or new Windows files. Peer GitLab main is historical/divergent; no automatic mirroring.
