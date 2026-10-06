# CircleCI Kwai vault install — silent timeout isolated
STATUS: FAILED
AREA: kwai
DATE: 2026-10-06
RUN: https://circleci.com/gh/UniversoAnthares/anthares-kwai-runner/223
JOB: 223
COMMIT: 5e4ed73200998235060e71b9b6ba7cc06da4f084
SUPERSEDES: test-hub/findings/20261006-circleci-kwai-install-repeated-failure-current-pending.md

## Resultado
The Android executor, API 35 AVD creation and boot all succeeded. The validated 42.2 MB Kwai vault downloaded successfully and SHA-256 verification printed `kwai-vault.zip: OK`. The `Install validated Kwai vault` step then produced no further output and CircleCI terminated it after 10 minutes with `Too long with no output (exceeded 10m0s): context deadline exceeded`.

## Classification
This is a post-download install-path hang. It is not an Android executor failure, vault download failure, or checksum failure. The old installer redirected `adb install-multiple`, `pm path`, and launcher output to a report file and had no per-command timeout, allowing a blocked ADB/package-manager operation to remain silent until CircleCI's no-output deadline.

## Causal fix
Commit db35ac8fc07691fd1a8336613cd0a598bb107756 adds explicit progress markers and bounded timeouts around adb wait-for-device, install-multiple, pm path and launcher. The next run must identify the exact bounded operation and return an explicit failure code instead of a 10-minute opaque timeout.

## Success signal
STEP_INSTALL_MULTIPLE_OK -> STEP_PM_PATH_OK -> STEP_KWAI_LAUNCH_OK -> KWAI_LAUNCHED.

## Failure signal
FAIL_ADB_WAIT_TIMEOUT, FAIL_INSTALL_MULTIPLE_RC, FAIL_PACKAGE_NOT_PRESENT_RC, or FAIL_KWAI_LAUNCH_RC.