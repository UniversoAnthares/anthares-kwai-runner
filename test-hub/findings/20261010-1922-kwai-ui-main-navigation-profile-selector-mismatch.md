# Native Kwai Android diagnosis: MAIN visible but Profile selector missing
STATUS: FAILED
AREA: kwai-login
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38079218107
JOB: 114292488319
COMMIT: 6e705ccf2f8620e43b9fe41fd2ef667e5ecec6c9
SUPERSEDES: test-hub/findings/20261010-1910-kwai-ui-diagnostic-instrumented.md

## Evidence
- Targeted static tests: 15 locator, 10 safe classifier, 8 native Email/Phone method tests all SUCCESS.
- Vault verified, Android booted, Kwai launched.
- 22 valid UIAutomator dumps; 0 invalid; UI_STATE=dump_valid,main_navigation; FOCUS=kwai.
- ONBOARDING_TAPS=0; PROFILE_TAPS=0. Native chooser not reached within 95s; exit 34.
- Therefore the app is interactive and on main navigation; the profile button selector is too narrow. Current selector `profile_tab` accepts only `id_home_bottom_tab_me`; prior Android runs proved alternative `com.kwai.video:id/ll_profile`.
- Do NOT repeat the old 110s blind loop or 40 QA matrix; do not infer account authentication or publication.

## Causal correction
After current kwai-login lease expires or owner yields, extend semantic profile selector and safe classifier to accept `ll_profile` and `id_home_bottom_tab_me`, add targeted fixture, and run one bounded Android diagnosis. If a profile tap exposes the native chooser, the existing exact Email/Phone method selector can proceed. Never blind-tap an unverified feed location.
