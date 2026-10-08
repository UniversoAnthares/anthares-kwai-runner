# Kwai speed benchmark round 1
STATUS: PARTIAL
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37858144818
JOB: 113587205652
COMMIT: d9596b291cbd7dcec5664820c9c62c818d14ac0b
SUPERSEDES: none

## PROVEN
Hosted runner successfully prepared Android 35 and validated the Kwai vault SHA256 concurrently; Android emulator booted and job completed successfully.

## FAILED / BUG
Job post-step logged "Path Validation Error" for cache path, so successful boot does not prove reusable SDK cache. Existing interactive login run 37857901486 also logged Android cache path validation error and failed with FAILURE_SIGNAL=UNEXPECTED_GOOGLE_SSO. These are separate issues.

## FIX
Commit 4c001e5d76017e7aa8af3c7db6e8d5620856765a changed only isolated benchmark SDK cache path to /usr/local/lib/android/sdk/system-images/android-35/google_apis/x86_64. Automatic push triggers repeat run. Do not modify the interactive login workflow while another agent is working on it.

## NEXT VALIDATION
Confirm second run saves both cache entries without Path Validation Error; then a third run must show SDK_CACHE_HIT=true and VAULT_CACHE_HIT=true. Benchmark does not prove Kwai login, snapshot reuse or publication.
