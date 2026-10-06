# Lease kwai-login Android Agent runtime harness repair
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: pending
SUPERSEDES: none
LEASE_AREA: kwai-login
EXPIRES: 2026-10-06T03:35:00Z

BASELINE_PROVEN: Android Agent APK build is PROVEN by run 37397385606; FSM MAIN is already PROVEN in prior Kwai runs; latest runtime 37400814461 reached TEST_VALIDITY=PROVEN_AGENT_APK_FETCHED then failed before emulator creation because avdmanager was not on PATH.
FAILED_AVOIDED: do not repeat bare ikwai://login, authorization URI routes, direct starts of non-exported login Activities, or pre-normalization coordinate matrices. Causal change is strictly repairing the Android SDK command-path harness and then using the AccessibilityService semantic Agent.
SUCCESS_SIGNAL: emulator boots, Kwai + Agent install, AccessibilityService enables, FSM_MAIN_REACHED occurs, and Agent observes PROFILE/RESOURCE_LOADING/LOGIN_REQUIRED/AUTHENTICATED or a concrete resource-loading UI.
FAILURE_SIGNAL: after all TEST_VALIDITY preconditions pass, the semantic Agent reaches MAIN but cannot observe or navigate any Profile/login-relevant state.
TEST_VALIDITY: explicit PROVEN_AGENT_APK_FETCHED, EMULATOR_BOOTED, APPS_INSTALLED, AGENT_SERVICE_ENABLED and FSM_MAIN_REACHED markers. Missing marker means HARNESS/INVALID, not a Kwai hypothesis failure.

## Objective
Repair the proven avdmanager PATH harness defect and advance the existing Android Agent to the first valid semantic runtime observation without repeating discarded login routes.