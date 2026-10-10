# Kwai main navigation Profile not exposed as exact label or known ID
STATUS: FAILED
AREA: kwai-login
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38080515655
JOB: 114296638804
SUPERSEDES: test-hub/findings/20261010-1922-kwai-ui-main-navigation-profile-selector-mismatch.md

## Evidence
- All 40 targeted synthetic tests passed (20 locator, 12 safe UI classifier, 8 native chooser).
- Android package installed and foreground, 21 valid UI dumps, zero invalid; main_navigation=true.
- `PROFILE_CANDIDATES=exact=0,bottom=0,idhint=1`, PROFILE_TAPS=0, no chooser; exit 34.
- The prior two known Profile tab IDs and exact bottom-label fallback are absent. There is exactly one resource ID containing `profile` that has not yet been classified.
- Next diagnostic change: log only the allowlisted static resource-ID suffix, clickable flag and normalized vertical position for profile-hint nodes, never raw UI text/screenshots or credentials. Then decide whether that node is safe to tap.
- FAILED_AVOIDED: do not repeat 95s diagnostic without new instrumentation; do not blind-tap feed; do not run credentialed publisher until password rotation.
