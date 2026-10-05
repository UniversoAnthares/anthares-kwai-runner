# Lease kwai-login exported auth intent details
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388775209
JOB: static manifest detail
COMMIT: b2e6551285ab6ad2d81aef4b399e7b1b141beb4d
SUPERSEDES: none
EXPIRES: 2026-10-06T02:45:00-04:00
BASELINE_PROVEN: test-hub/findings/20261006-0038-exported-kwai-auth-entrypoints-proven.md
FAILED_AVOIDED: internal login Activities are not exported; do not direct-launch them.
SUCCESS_SIGNAL: exact action/category/scheme/host/path metadata recovered for at least one exported Kwai auth entrypoint.
FAILURE_SIGNAL: candidate block contains no usable intent-filter data.
TEST_VALIDITY: aapt full Manifest extraction succeeds.
## Objetivo
Recover exact intent contracts before runtime invocation.
