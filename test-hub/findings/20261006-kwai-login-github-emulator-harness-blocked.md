# kwai-login Android Agent runtime — GitHub emulator harness blocked
STATUS: FAILED
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37412351170
SUPERSEDES: test-hub/findings/20261006-0400-lease-kwai-login-final.md

## Objetivo
Reach a valid Android Agent runtime, MAIN, and semantic Profile/login observation without repeating discarded URI/direct-Activity paths.

## Resultado
The APK and Kwai vault were fetched successfully and the emulator image installed. The GitHub-hosted runner never produced an ADB device: timeout 180 adb wait-for-device exited 124. The same failure occurred after a causal change from default acceleration to -accel off, -no-snapshot, and -wipe-data.

## Evidência decisiva
The failure occurs before APPS_INSTALLED, AGENT_SERVICE_ENABLED, or FSM_MAIN_REACHED. Therefore this is a harness/environment failure, not evidence that the Kwai login hypothesis failed.

## Consequência
Do not repeat the same GitHub-hosted emulator boot configuration. The next runtime attempt requires a different execution substrate or an emulator service that provides a bootable Android target. The discarded URI and non-exported Activity routes remain discarded.
