# CircleCI Kwai post-install probe — process missing or UI missing
STATUS: FAILED
AREA: kwai
DATE: 2026-10-06
SUPERSEDES: none

## Evidence
The CircleCI step `Probe Kwai UI and process` exited with code 1 immediately. Its first strict command was `adb shell pidof com.kwai.video`; because the shell uses `set -Eeuo pipefail`, a missing Kwai PID terminates the step before UI dump collection. This proves the previous probe could not distinguish process death from later UI-dump failure.

## Causal correction
Commit a73f18edd8ba0d7516a295d30c2738e38855a4ff makes PID observation non-fatal, records POST_BOUNDARY_KWAI_PID, performs one launcher relaunch when the process is absent, records POST_RELAUNCH_KWAI_PID, independently records POST_BOUNDARY_UI_DUMP_OK, and returns explicit exit 51 only after both observations.

## Success signal
POST_BOUNDARY_KWAI_PID or POST_RELAUNCH_KWAI_PID is non-empty, POST_BOUNDARY_UI_DUMP_OK=1, then SUCCESS_SIGNAL=KWAI_INSTALL_AND_LAUNCH_OK.

## Failure signal
FAILURE_SIGNAL=KWAI_RUNTIME_OR_UI_NOT_READY with explicit preceding PID/UI evidence.

## Test validity
This changes observation/recovery only. It does not mutate login routes, credentials, authentication, APK selection, or publication.