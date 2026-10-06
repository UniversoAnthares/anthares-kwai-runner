# Android Agent build harness invalid
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396753682
JOB: 112054452765
COMMIT: 15977698b0c2f864d6671387ea675061d63fed65
SUPERSEDES: test-hub/findings/20261005-2100-android-agent-foundation-build-running.md

BASELINE_PROVEN: Android Agent foundation committed under active kwai-login lease.
FAILED_AVOIDED: no Kwai auth route was retested.
SUCCESS_SIGNAL: assembleDebug + APK.
FAILURE_SIGNAL: compiler/resource/manifest rejection.
TEST_VALIDITY: INVALID for Agent hypothesis because failure occurred in SDK setup before Gradle build.

## Resultado
HARNESS_INVALID. android-actions/setup-android invoked sdkmanager tools; current SDK manager returned Failed to find package 'tools' and exited 1. Agent source was not compiled.

## Consequência
Remove the obsolete setup-android dependency and use the hosted runner Android SDK directly; then rerun the same build hypothesis.
