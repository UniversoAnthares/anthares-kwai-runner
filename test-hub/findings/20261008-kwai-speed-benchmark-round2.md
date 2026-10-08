# Kwai speed benchmark round 2: both cache hits proven
STATUS: PARTIAL
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37858866621
JOB: 113589547523
COMMIT: 3900f672deb740bc775127d76918af129fb3bce4
SUPERSEDES: 20261008-kwai-speed-benchmark-round1.md

## PROVEN
Actions logs: Cache hit for kwai-speed-android35-google-apis-x86_64-v1 (~1572 MB); Cache restored successfully. Cache hit for kwai-speed-vault-96650454576a2cf5-v1 (~42 MB); Cache restored successfully. Both cache hits independently confirmed on new hosted runner.

## FAILURE_SIGNAL
Run conclusion failure, because avdmanager reported Error: "emulator" package must be installed! SDK system image cache restored, but emulator package missing. Do not claim successful warm boot.

## FIX
Commit 42b660ef462f7d10decf693bacbd81d259d9579e adds dedicated emulator binary cache and explicit sdkmanager install if missing, before avdmanager creates AVD. New push-triggered benchmark run validates fix. No login workflow modified; other agent retains kwai-login ownership.

## NEXT
Inspect new benchmark run for boot success, and verify emulator cache reuse on subsequent run. No proof of login or publishing.
