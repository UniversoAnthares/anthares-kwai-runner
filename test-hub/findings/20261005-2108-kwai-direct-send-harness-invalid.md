# Kwai direct video ACTION_SEND probe was invalid before the declared precondition
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37391243048
JOB: 112036559526
COMMIT: 08d6a52a7a585b60d0ecefe327ddda7f3e5753e3
SUPERSEDES: test-hub/findings/20261005-2105-kwai-direct-send-runtime-running.md

BASELINE_PROVEN: test-hub/findings/20261005-2054-kwai-uri-router-video-send-contract.md; proven FSM MAIN baseline.
FAILED_AVOIDED: no Publish action occurred and no conclusion about ACTION_SEND is inferred from workflow failure.
SUCCESS_SIGNAL: not reached.
FAILURE_SIGNAL: not reached.
TEST_VALIDITY: INVALID/NOT_TESTED. The emulator booted, then the action wrapper invoked the configured script through `/usr/bin/sh`; the very first `set -euo pipefail` failed with `set: Illegal option -o pipefail`. `kwai_vault_install.sh`, FSM_MAIN_REACHED, media generation/MediaStore identity and ACTION_SEND were never executed in the probe script.

## Resultado
Run 37391243048 failed at the harness shell boundary before any hypothesis-bearing step. The decisive log is `/usr/bin/sh: 1: set: Illegal option -o pipefail`. No evidence files existed because execution stopped before their creation.

## Consequência
Do not classify the direct SEND route as FAILED. Change the workflow script to enter Bash explicitly, preserve the same baseline/success/failure signals, and rerun once. This causal harness change is sufficient to retry under the hub protocol.
