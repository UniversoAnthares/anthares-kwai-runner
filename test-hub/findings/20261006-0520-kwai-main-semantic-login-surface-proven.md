# Kwai MAIN semantic login surface proven
STATUS: PROVEN
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37417154662
JOB: 112118188622
SUPERSEDES: test-hub/findings/20261006-0510-lease-kwai-main-semantic-login-probe.md

BASELINE_PROVEN: remote Android boot and validated Kwai split installation.
SUCCESS_SIGNAL: LOGIN_CONTROL_VISIBLE=1 and SUCCESS_SIGNAL=LOGIN_SURFACE_REACHED.
TEST_VALIDITY: APPS_INSTALLED and FSM_MAIN_REACHED occurred before the login probe.

## Evidence
The state driver crossed onboarding and reached MAIN. UIAutomator found one visible Log in control. A semantic tap opened the real Kwai authentication surface. The resulting UI exposed Welcome to Kwai, Continue with Google, Facebook, and Phone. This proves a cloud-only route from fresh install to the actual login chooser without relying on AccessibilityService.

## Consequence
The next causal step is authentication on one of the exposed providers and independent account/session READY proof. Do not reopen URI or non-exported Activity experiments.
