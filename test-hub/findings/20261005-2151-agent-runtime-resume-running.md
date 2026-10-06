# Android Agent runtime resume after SDK harness proof
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37400814461
JOB: Agent APK install + AccessibilityService + semantic Kwai control
COMMIT: 49661565599e3d4855e8540d383d2ba3b97fccdc
SUPERSEDES: test-hub/findings/20261005-2148-android-sdk-harness-path-proven.md

BASELINE_PROVEN: 20261005-2115 Android Agent APK build PROVEN; 20261005-2148 sdkmanager absolute path PROVEN; official Kwai vault validated.
FAILED_AVOIDED: no rebuild of Agent, no deep links, no non-exported Activity start, no bare sdkmanager PATH dependency. Runtime downloads the proven APK artifact and uses the proven SDK path.
SUCCESS_SIGNAL: proven APK installed; AccessibilityService enabled and present in dumpsys; FSM_MAIN_REACHED; Agent emits STATE=MAIN; semantic ll_profile action leads to Agent PROFILE/RESOURCE_LOADING/LOGIN_REQUIRED/AUTHENTICATED or equivalent resource-loading UI evidence.
FAILURE_SIGNAL: after emulator+apps+service preconditions, Agent cannot observe MAIN/Profile semantic state.
TEST_VALIDITY: failures before emulator boot + both apps installed + accessibility enabled are HARNESS_INVALID and must be repaired without classifying Agent failed.
