# Kwai login runtime harness — boot hang fix
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
RUN: 37411505991
COMMIT: af86458d2dc7de14b8ee0032a6f4ccd5655aba6c
LEASE: 20261006-0400-lease-kwai-login-final.md

## New causal finding
The current Agent runtime reached the `Boot emulator` step and remained RUNNING while all subsequent steps stayed pending. The workflow used an unbounded `adb wait-for-device` before its existing 180-second boot-completion timeout. Therefore the existing timeout did not protect the initial device-wait operation.

## Fix applied
Changed the runtime workflow to:
`timeout 60 adb wait-for-device`
followed by the existing 180-second `sys.boot_completed` timeout.

This prevents a dead ADB/emulator startup from consuming the entire job indefinitely and makes the failure observable.

## Execution rule
The currently running old-SHA job must finish before starting the corrected runtime run. No competing runtime matrix is started while the causal run is RUNNING.

## Success signal
Corrected run reaches `EMULATOR_BOOTED`, then `APPS_INSTALLED`, `AGENT_SERVICE_ENABLED`, `FSM_MAIN_REACHED`, and semantic Profile/resource/login state observation.

## Failure signal
The bounded ADB wait or bounded boot-completion loop fails with an explicit timeout/error. Such a failure is valid evidence about emulator boot, unlike the previous indefinite wait.