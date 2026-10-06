# CircleCI Kwai install and login-surface chain
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
COMMIT: 6557b1fcf35c854a4c9dff6565d342ca7261d011
SUPERSEDES: test-hub/findings/20261006-circleci-android-executor-proven.md

## Objetivo
Use the proven CircleCI Android executor as the new remote substrate for the validated Kwai bundle, then test the already-proven semantic Profile path through concrete login controls.

## Baseline
CircleCI Android 35 x86_64 boot is PROVEN. The validated Kwai bundle is base + dfm_ug + config.arm64_v8a + config.xxhdpi, and the Android image previously exposed libndk_translation.so for ARM64 execution. GitHub-hosted Android login harness remains blocked before ADB device availability and is not reused.

## New chain
1. kwai_install_smoke validates executor -> emulator -> vault -> install -> launch.
2. kwai_login_surface_smoke runs only after the install job succeeds, then independently boots the same CircleCI substrate, installs the same validated bundle, and runs kwai_login_control_discovery.py.
3. The login probe is bounded and produces artifacts. It uses the proven semantic Profile control and waits for the dynamic Profile module before testing explicit authentication controls.

## Success signals
KWAI_INSTALL_AND_LAUNCH_OK
LOGIN_FORM_FOUND=1 / LOGIN_SURFACE=EDITABLE_FORM

## Valid failure classes
LOGIN_SURFACE=PROFILE_MODULE_TIMEOUT indicates the Profile dynamic feature did not become ready within the bounded probe and does not invalidate the authentication hypothesis.
Any failure before EMULATOR_BOOTED or APPS_INSTALLED is an executor/install failure and must be classified separately.

## Rule
Do not return to the previously blocked GitHub-hosted emulator harness or discarded bare direct-Activity/URI routes.