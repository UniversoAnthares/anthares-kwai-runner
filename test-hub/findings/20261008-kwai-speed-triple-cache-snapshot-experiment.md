# Kwai triple-cache and snapshot experiment handoff
STATUS: RUNNING
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37859160736; 37859208163
JOB: 113590514878 (first run)
COMMIT: 1f44d86e7e7ed0f05b39d594fb4f4c6e199d7a1a; ed798f96629f22f15925f9d92349ea705c42352b
SUPERSEDES: 20261008-kwai-speed-benchmark-round3.md

## BASELINE_PROVEN
37858963753 completed SUCCESS with Android system image cache hit, vault cache hit, clean Android boot, and dedicated emulator binary cache saved. See round3 finding.

## CURRENT
37859160736 tests three cache hits and emits PREP_TOTAL_SECONDS, COLD_BOOT_SECONDS, TOTAL_SECONDS in logs. At last poll in progress; job log unavailable (404 BlobNotFound) while still running, so no timing claims.
37859208163 queued, includes isolated non-login AVD snapshot save and restart experiment with timeout and continue-on-error. Commit ed798f9. Snapshot experiment does not touch login workflow or session, and cannot prove persistence between GitHub runners.

## SUCCESS_SIGNAL
Three restored caches, timed boot and snapshot save/reboot result in logs. Snapshot can only be called reusable across runs after additional persistence validation.

## FAILURE_SIGNAL
Missing emulator package, boot failure, snapshot save failure or snapshot reboot failure. Distinguish infrastructure from login.

## AGENT COORDINATION
Other agent retains kwai-login. Only isolated kwai-startup-speed-benchmark.yml and kwai-speed findings edited; do not change login scripts/workflows. No local PC, no billing.
