# kwai-login Android Agent runtime final lease
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
EXPIRES: 2026-10-06T04:20:00-04:00
BASELINE_PROVEN: Android Agent APK build 37397385606; FSM MAIN proven; previous harness failed because avdmanager was absent from PATH.
FAILED_AVOIDED: bare authorization/login URI routes, direct non-exported Activities, pre-normalization coordinate matrices.
SUCCESS_SIGNAL: valid emulator boot + Agent service + MAIN + semantic observation of PROFILE/RESOURCE_LOADING/LOGIN_REQUIRED/AUTHENTICATED.
FAILURE_SIGNAL: all harness preconditions pass and semantic Agent cannot observe or navigate login-relevant state.
TEST_VALIDITY: explicit APK_FETCHED, EMULATOR_BOOTED, APPS_INSTALLED, AGENT_SERVICE_ENABLED, FSM_MAIN_REACHED.
