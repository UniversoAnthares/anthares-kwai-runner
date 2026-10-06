# Kwai MAIN probe — Element truthiness blocked Skip
STATUS: FAILED
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37416568247
JOB: 112116371130
SUPERSEDES: test-hub/findings/20261006-0510-lease-kwai-main-semantic-login-probe.md

BASELINE_PROVEN: APPS_INSTALLED; onboarding INTEREST_SELECT rendered a visible semantic "skip" control.
FAILED_AVOIDED: this is not an authentication hypothesis failure and does not reopen AccessibilityService.
SUCCESS_SIGNAL: FSM_MAIN_REACHED then LOGIN_CONTROL_VISIBLE and login-surface observation.
FAILURE_SIGNAL: visible Skip cannot be activated by the FSM.
TEST_VALIDITY: valid through INTEREST_SELECT; login hypothesis NOT_TESTED.

## Causa
kwai_state_driver.py stores the matching XML Element in n, then tests `if n`. ElementTree Elements without child elements evaluate false. The logs repeatedly show UI text "skip" while printing INTEREST_SELECT_SKIP_NOT_FOUND, proving the semantic match existed but the truthiness branch suppressed tap(n).

## Próxima correção
Use explicit `is not None` for Element presence checks and avoid `a or b` selection on Element truthiness.
