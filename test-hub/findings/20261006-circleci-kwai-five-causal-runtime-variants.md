# CircleCI Kwai five causal runtime variants
STATUS: RUNNING
AREA: kwai-runtime
DATE: 2026-10-06
COMMIT: a719a74f1b6c1b77da91692c4115dce499112c9e

## Purpose
Run five independent causal variants after the validated CircleCI Android baseline without touching the currently owned kwai-login mutation area.

## Variants
- cold: current minimal baseline.
- wait2: add 30 seconds after Android boot before package work.
- restart_adb: deliberately restart ADB after boot and prove reconnect before installation.
- launch_retry: retry the launcher once if the Kwai process is absent after validated installation.
- ui_delay: allow 15 seconds after launch before UIAutomator observation.

## Shared controls
All variants use Android 35 google_apis x86_64, the same validated kwai-package-vault release and SHA-256, and the existing bounded kwai_vault_install.sh. Each emits PID, UI_DUMP_OK and bounded crash/ABI log evidence.

BASELINE_PROVEN: CircleCI Android executor and 10/10 ADB step-boundary persistence.
FAILED_AVOIDED: no ikwai://login, hidden/non-exported Activities, coordinate-only login matrix, credential mutation, or publication attempt.
SUCCESS_SIGNAL: installer reaches KWAI_LAUNCHED and variant reports a non-empty PID plus UI_DUMP_OK=1.
FAILURE_SIGNAL: bounded installer failure, absent PID, or UI_DUMP_OK=0 with crash/runtime evidence.
TEST_VALIDITY: these are runtime/install observations only; kwai-login ownership remains untouched.
