# Kwai login surface reached through semantic main-screen control
STATUS: PROVEN
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37417286394
BASELINE_PROVEN: Android Agent build, Kwai Package Vault, emulator boot and FSM_MAIN_REACHED were already proven. Bare ikwai://login and non-exported/internal Activity routes were discarded.
FAILED_AVOIDED: did not use ikwai://login, hidden Activities, coordinate-only matrices, or infer login from MAIN.
SUCCESS_SIGNAL: LOGIN_SURFACE_REACHED.
FAILURE_SIGNAL: LOGIN_CONTROL_VISIBLE=0 or LOGIN_SURFACE_NOT_REACHED.
TEST_VALIDITY: run reached EMULATOR_BOOTED, APPS_INSTALLED and FSM_MAIN_REACHED before semantic UI inspection; visible Log in control was found from UIAutomator and tapped by its discovered bounds.

## Evidence
Run 37417286394 emitted:
- TEST_VALIDITY=EMULATOR_BOOTED
- TEST_VALIDITY=APPS_INSTALLED
- FSM_MAIN_REACHED
- LOGIN_CONTROL_COUNT=1
- LOGIN_CONTROL_VISIBLE=1
- POST_LOGIN_UI included: Welcome to Kwai; Continue with Google; use Facebook; phone
- SUCCESS_SIGNAL=LOGIN_SURFACE_REACHED

## Conclusion
The remote Android/Kwai runtime can now deterministically reach the real authentication surface without local PC dependence. This does not prove authenticated Kwai session yet. Next causal uncertainty is completing one supported authentication method remotely and verifying authenticated account state before publication.