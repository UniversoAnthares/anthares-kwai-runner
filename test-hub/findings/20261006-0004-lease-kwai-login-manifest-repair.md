# Lease kwai-login manifest metadata repair
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
RUN: pending
JOB: static manifest metadata
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-06T01:00:00-04:00

BASELINE_PROVEN: test-hub/findings/20261005-2250-kwai-apk-login-resources.md
FAILED_AVOIDED: test-hub/findings/20261006-0001-kwai-login-metadata-harness-invalid.md; the missing script is added before trigger. test-hub/findings/20261006-0002-kwai-direct-login-no-runtime-targets.md; no direct launch is attempted before manifest proof.
SUCCESS_SIGNAL: valid aapt execution plus manifest metadata for at least one known login/auth/profile component.
FAILURE_SIGNAL: valid manifest dump contains none of the known login/auth/profile component candidates.
TEST_VALIDITY: base APK exists; aapt binary exists and prints version; manifest-tree.txt is nonempty. Any failure before these checks is harness invalid.

## Objetivo
Close the manifest evidence gap before any further Android login navigation experiment.

## Resultado
Lease acquired after previous kwai-login lease expired.

## Consequência
No concurrent kwai-login mutation until this causal probe closes.
