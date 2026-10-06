# Kwai phone-auth follow-up — selector needs semantic containment
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37417529886; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37417516967
SUPERSEDES: none

## Valid preconditions
Both runs reached EMULATOR_BOOTED, APPS_INSTALLED, FSM_MAIN_REACHED, LOGIN_CONTROL_VISIBLE=1, AUTH_EXPLICIT_CONTROLS=1 and SUCCESS_SIGNAL=LOGIN_SURFACE_REACHED.

## New uncertainty
The follow-up Phone probe reported PHONE_CONTROL_COUNT=0. The immediately preceding UI text visibly contained `phone` together with `continue with google` and `use facebook`. The probe required an exact node label in (`phone`, `phone number`, `use phone`, ...). Therefore the result does not prove that Phone authentication is unavailable; it only shows that the exact-label selector did not isolate a Phone node in that UI tree.

## Classification
PHONE_AUTH_FORM_NOT_REACHED is a selector/harness boundary after a proven login surface. Do not classify the phone-auth hypothesis FAILED until the owning kwai-login agent tests a semantic contains/text-desc/resource selector or chooses another supported auth control. No competing kwai-login mutation was made by QA.