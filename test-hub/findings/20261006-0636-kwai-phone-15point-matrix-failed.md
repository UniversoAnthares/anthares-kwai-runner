# Kwai Phone 15-point matrix
STATUS: FAILED
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37418689161
BASELINE_PROVEN: FSM_MAIN_REACHED and LOGIN_SURFACE_REACHED.
FAILED_AVOIDED: do not repeat taps restricted to text-node bounds.
SUCCESS_SIGNAL: editable Phone authentication form.
FAILURE_SIGNAL: all 15 text-node points leave no auth form.
TEST_VALIDITY: valid. Phone-bearing node was not clickable.

Fifteen positions inside the Phone-bearing accessibility text node were tested. None reached an authentication form. The next matrix inspects surrounding nodes and tests positions around the text node instead.
