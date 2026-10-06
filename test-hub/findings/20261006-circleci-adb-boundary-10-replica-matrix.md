# CircleCI ADB step-boundary 10-replica matrix
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
COMMIT: 387cbfd8422763e978a393af449e0dbab3c5e605
SUPERSEDES: none

## Objetivo
Test the suspected CircleCI run-step boundary failure in 10 independent parallel Android 35 replicas without changing the Kwai/login hypothesis.

## Matrix
kwai_boundary_probe_01 through kwai_boundary_probe_10. Each replica creates and boots its own API 35 x86_64 AVD, proves ADB serial/state at the end of one CircleCI run step, then checks ADB availability again in the immediately following run step.

## Baseline
CircleCI Android boot is PROVEN. Job 339 reached a successful boot step and then kwai_vault_install.sh failed at STEP_ADB_WAIT_START with FAIL_ADB_WAIT_TIMEOUT before install-multiple.

## Success signal
BOUNDARY_PRECONDITION_OK=1 followed by NEXT_STEP_ADB_ALIVE=1 in a replica.

## Failure signal
BOUNDARY_PRECONDITION_OK=1 followed by NEXT_STEP_ADB_ALIVE=0 / exit 20.

## Test validity
A replica that fails before BOUNDARY_PRECONDITION_OK=1 is an emulator boot failure and does not test the step-boundary hypothesis. No direct login URI, non-exported Activity, APK split change, or authentication mutation is part of this matrix.