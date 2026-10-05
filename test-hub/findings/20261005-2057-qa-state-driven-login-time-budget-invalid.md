# State-driven Kwai login reached valid MAIN/Profile precondition but discovery was canceled by workflow budget
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37389749589
JOB: 112031754525
COMMIT: 50302956da7da5165611b155b83e3094ed684de1
SUPERSEDES: none

BASELINE_PROVEN: proven kwai_state_driver FSM reaches MAIN; test-hub/findings/20261005-1754-kwai-profile-resource-gate.md documents Profile dynamic loading.
FAILED_AVOIDED: this result is not classified as a login-route failure; exported authorization URIs are not repeated; harness validity is separated from hypothesis outcome.
SUCCESS_SIGNAL: TEST_VALIDITY=FSM_MAIN_REACHED followed by login controls/EditText discovered after stable Profile readiness.
FAILURE_SIGNAL: stable Profile reached within budget and explicit login/control discovery completes with no candidates.
TEST_VALIDITY: run emitted TEST_VALIDITY=FSM_MAIN_REACHED, then the GitHub job was canceled while `kwai_login_control_discovery.py` was still running; the declared login discovery outcome was never reached.

## Resultado
The run traversed INTEREST 1/12 through 12/12, START, then MAIN and emitted `FSM_MAIN_REACHED`. It found the clickable Profile parent and observed the known `resource downloading` dialog. After `TEST_VALIDITY=FSM_MAIN_REACHED`, `kwai_login_control_discovery.py` began at 23:44:03Z. GitHub canceled the operation at 23:48:45Z before that script emitted AUTH_CANDIDATES or LOGIN_FORM_FOUND. The workflow timeout budget includes Android SDK install, emulator boot, APK install, full FSM traversal and Profile stabilization, leaving insufficient time for the discovery script's own bounded Profile wait.

## Consequência
Preserve the FSM. Do not count run 37389749589 as evidence that internal Profile login controls are absent. The next kwai-login iteration must change the harness budget/phase split, or use the newly recovered Manifest-declared `ikwai://login` route as a causally distinct focused probe. The active kwai-login owner should close/revise its lease based on this evidence.
