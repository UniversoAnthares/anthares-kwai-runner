# Lease kwai-login launcher recovery then login router
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37395018657
JOB: launcher recovery + single login router probe
COMMIT: 5c8b7b72e7b962d1f8af8ca231a80a8f23be2146
SUPERSEDES: test-hub/findings/20261006-0062-lease-kwai-state-driven-internal-login.md
EXPIRES: 2026-10-06T01:03:00-04:00

BASELINE_PROVEN: FSM reaches MAIN in valid replicas; Manifest proves exported UriRouterActivity route ikwai://login.
FAILED_AVOIDED: run 37392541208 exposed repeated LAUNCHER_ANR because existing recovery only handled the dialog/relaunched Kwai; bare authorization deep links remain discarded; no direct start of non-exported login Activities.
SUCCESS_SIGNAL: if LAUNCHER_ANR occurs, recovery exits that state and reaches FSM_MAIN_REACHED; after valid MAIN, ikwai://login resolves and exposes explicit login UI/EditText/internal LoginActivity.
FAILURE_SIGNAL: launcher remains LAUNCHER_ANR after the new launcher-process recovery, or valid MAIN + ikwai://login resolves without explicit login surface.
TEST_VALIDITY: login-route hypothesis is tested only after FSM_MAIN_REACHED. Boot/ADB/install failure is INVALID. Recovery is PROVEN only if LAUNCHER_ANR is actually observed.

## Objetivo
Repair the now-observed launcher precondition causally, then test exactly one distinct Manifest-declared login route after MAIN.
