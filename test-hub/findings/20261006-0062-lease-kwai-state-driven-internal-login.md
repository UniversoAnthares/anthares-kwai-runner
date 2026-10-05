# Lease kwai-login state-driven internal control probe
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37389749589
JOB: Android state-driven login control probe
COMMIT: 50302956da7da5165611b155b83e3094ed684de1
SUPERSEDES: none
EXPIRES: 2026-10-06T03:45:00-04:00

BASELINE_PROVEN: test-hub/findings/20261005-2405-state-driver-partial-proven.md; test-hub/findings/20261005-1959-qa-kwai-exported-auth-runtime-no-login.md
FAILED_AVOIDED: bare exported auth deep links already failed; internal Activities are non-exported; pre-normalization matrices are invalid. This probe reuses the PROVEN FSM and navigates only from MAIN using actual UI controls.
SUCCESS_SIGNAL: after FSM_MAIN_REACHED, a real internal navigation produces explicit auth controls and then an editable login form.
FAILURE_SIGNAL: FSM_MAIN_REACHED is valid, Profile/internal control state is observed, and no explicit auth candidate reaches an editable login form after bounded module handling.
TEST_VALIDITY: FSM_MAIN_REACHED is mandatory; without it the auth hypothesis is NOT_TESTED. Launcher/DFM/harness failure is classified separately.

## Objetivo
Use the proven state driver to test internal UI navigation into login after exported gateways failed.
