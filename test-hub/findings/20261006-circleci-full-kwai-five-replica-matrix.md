# CircleCI full Kwai same-step five-replica matrix
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
COMMIT: 956c509680caa46dd47a20839d7b91af846969d6
SUPERSEDES: none

## Objective
Go beyond the ADB-only boundary matrix by running five independent full replicas of Android 35 boot -> validated Kwai vault -> bounded installer -> Kwai launch -> UI dump, all critical install work in one CircleCI run step.

## Replicas
kwai_same_step_probe_01 through kwai_same_step_probe_05.

## Baseline proven
CircleCI Android executor works. ADB across CircleCI run-step boundaries passed 10/10 independent replicas. Job 339 failed before APK installation because ADB was unavailable in that specific run. Therefore this matrix does not assume deterministic step-boundary failure.

## Success signals
BOOT_OK=1, STEP_ADB_WAIT_OK, STEP_INSTALL_MULTIPLE_OK, KWAI_LAUNCHED, INSTALL_OK=1, UI_DUMP_OK=1.

## Failure classification
Failure before BOOT_OK is emulator substrate.
Failure after BOOT_OK but before STEP_INSTALL_MULTIPLE_OK isolates ADB/package install.
Failure after STEP_INSTALL_MULTIPLE_OK but before KWAI_LAUNCHED isolates launch.
Failure after KWAI_LAUNCHED but before UI_DUMP_OK isolates runtime/UI availability.
Post-install liveness is measured in a second step separately.

## Test validity
Each replica owns its AVD. No login route mutation, direct non-exported Activity, bare login URI, credentials, or publication action is performed.