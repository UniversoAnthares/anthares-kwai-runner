# Android SDK harness path proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37400703605
JOB: matrix
COMMIT: 60b67f56020dc7c1e525ccefefdea47270585047
SUPERSEDES: test-hub/findings/20261005-2142-android-runtime-sdk-30way-running.md

BASELINE_PROVEN: Agent APK build PROVEN; runtime run 37397864424 stopped at sdkmanager not on PATH.
FAILED_AVOIDED: bare sdkmanager invocation is retired.
SUCCESS_SIGNAL: SDK_STRATEGY_PROVEN with executable sdkmanager.
FAILURE_SIGNAL: candidate absent/non-executable.
TEST_VALIDITY: hosted ubuntu-24.04 common precondition reached.

## Resultado
PROVEN independently by variants 2, 11, 12, 16, 17, 20, 28 and 29: /usr/local/lib/android/sdk/cmdline-tools/latest/bin/sdkmanager is executable and answers --version.

## Consequência
Use the absolute cmdline-tools/latest path in the runtime workflow. Do not repeat PATH discovery. Resume the causal runtime layer: install proven APK artifact, boot emulator, install official Kwai, enable AccessibilityService, semantic MAIN/Profile observation.
