# CircleCI job 339 — ADB disappears after successful boot step
STATUS: FAILED
AREA: kwai
DATE: 2026-10-06
RUN: https://circleci.com/gh/UniversoAnthares/anthares-kwai-runner/339
JOB: 339
COMMIT: db35ac8fc07691fd1a8336613cd0a598bb107756
SUPERSEDES: test-hub/findings/20261006-circleci-kwai-install-silent-timeout-isolated.md

## Resultado
The API 35 emulator boot step completed successfully in 2m11s. The next step downloaded and verified the 42.2 MB vault, then the instrumented installer printed STEP_ADB_WAIT_START and failed after 30 seconds with FAIL_ADB_WAIT_TIMEOUT, exit status 20.

## Evidência decisiva
The failure is before install-multiple. No APK installation hypothesis was tested in job 339. The ADB device that existed during the previous CircleCI run step was no longer available when the following run step invoked kwai_vault_install.sh.

## Consequência
Do not tune APK splits or package-manager installation based on job 339. First preserve or recreate the emulator/ADB availability across the CircleCI step boundary. Commit 5d9a5ea9ad0599504a2067b2bdcc0d87a66891f8 adds explicit ADB serial/state evidence at the end of the boot step for the next causal run.

## Success signal
The install step reaches STEP_ADB_WAIT_OK and then STEP_INSTALL_MULTIPLE_START.

## Failure signal
The boot step reports a live ADB device but the following step again reports FAIL_ADB_WAIT_TIMEOUT, proving CircleCI step-boundary process lifetime is the cause.