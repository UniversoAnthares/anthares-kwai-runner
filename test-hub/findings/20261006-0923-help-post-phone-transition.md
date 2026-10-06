# Help request — exact post-Phone transition
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
RUN: pending
JOB: none
COMMIT: 71d2eb578957860e1b41aa09a13177fd69cb4c60
SUPERSEDES: none

BASELINE_PROVEN: 37465588876 proves MAIN -> real app-native login chooser and Phone is visible.
FAILED_AVOIDED: direct URI/activity guessing is exhausted and is not used here.
SUCCESS_SIGNAL: observe a concrete post-Phone foreground activity/window plus Phone form, editable field, OTP/SMS/challenge or resource-loading prerequisite.
FAILURE_SIGNAL: valid semantic tap remains on the same foreground state with no UI/resource transition.
TEST_VALIDITY: boot, app install, FSM_MAIN_REACHED and LOGIN_SURFACE_REACHED must precede classification.

## Help requested
Inspect the new foreground window/activity observations after the legitimate Phone chooser tap. Correlate them with node ancestry/actions and resource loading. Patch only the causal prerequisite. If the native transition remains opaque, promote the official Studio Phone form to our own cloud session-bootstrap service with a one-time owner challenge and persisted no-PC session. Do not retry direct Activities/deeplinks.

TikTok browser-environment QA30 is closed negative at the auth boundary. Help only with legitimate session renewal/read-only upload proof; do not add more cosmetic browser variants.
