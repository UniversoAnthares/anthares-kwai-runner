# Lease kwai-login Android Agent runtime validation
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37397864424
JOB: install + AccessibilityService + Kwai semantic state validation
COMMIT: 1072f7b8d594c60e989bca6004a0e570a5a07b96
SUPERSEDES: none
EXPIRES: 2026-10-05T22:05:00-04:00

BASELINE_PROVEN: test-hub/findings/20261005-2115-android-agent-foundation-build-proven.md; test-hub/findings/20261005-2405-state-driver-partial-proven.md
FAILED_AVOIDED: bare authorization/login deep links are closed; non-exported login Activities are not started externally; no coordinate matrix. This test installs the proven Agent APK and enables its AccessibilityService in the same Android emulator as official Kwai.
SUCCESS_SIGNAL: APK installs; AccessibilityService is enabled/connected; official Kwai launches; Agent telemetry observes semantic Kwai state including MAIN, and after semantic Profile action observes PROFILE or RESOURCE_LOADING without coordinate-only navigation.
FAILURE_SIGNAL: after valid emulator/Kwai/Agent installation, service cannot connect or cannot observe official Kwai window/state despite accessibility being enabled.
TEST_VALIDITY: emulator boot, Kwai vault install and Agent APK build/install must all succeed. Failure before those preconditions is HARNESS_INVALID, not Agent runtime failure.

## Objetivo
Validate the Anthares Android Agent end-to-end on remote Android against the official Kwai app, through MAIN -> Profile/resource state.
