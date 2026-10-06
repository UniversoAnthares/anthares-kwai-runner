# Lease kwai-login Anthares Android Agent foundation
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: Android Agent foundation + build validation
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-05T21:25:00-04:00

BASELINE_PROVEN: test-hub/findings/20261005-2405-state-driver-partial-proven.md; test-hub/findings/20261005-2050-qa-kwai-login-router-valid-failure.md
FAILED_AVOIDED: bare authorization and bare ikwai://login routes are closed; direct starts of internal login Activities are blocked as non-exported; pre-normalization click matrices are closed. The causal change is to move state detection/navigation into an AccessibilityService-based Anthares Android Agent and preserve the proven FSM states.
SUCCESS_SIGNAL: repository contains buildable Android Agent with AccessibilityService, semantic node inspection/action primitives, explicit Kwai FSM states including RESOURCE_LOADING/LOGIN_REQUIRED/AUTHENTICATED/READY, telemetry contract, and CI build produces an APK.
FAILURE_SIGNAL: Agent cannot build or service/manifest/protocol contract is internally inconsistent.
TEST_VALIDITY: Gradle/SDK/toolchain failure is HARNESS/INVALID unless Java/Kotlin compilation or Android resource/manifest validation specifically rejects Agent code/configuration.

## Objetivo
Create the first robust Anthares Android Agent foundation around the official Kwai app, replacing fragile external coordinate scripts while preserving the proven MAIN/Profile FSM behavior.
