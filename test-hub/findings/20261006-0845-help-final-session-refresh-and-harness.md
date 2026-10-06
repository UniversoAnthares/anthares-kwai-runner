# Help request — final session refresh + autonomous Kwai harness
STATUS: RUNNING
AREA: tiktok, kwai, live
DATE: 2026-10-06
RUN: TikTok 37463242183; Kwai pending f63d98f490adbacc045a4d25d8b0efa5204f500b
JOB: none
COMMIT: f63d98f490adbacc045a4d25d8b0efa5204f500b
SUPERSEDES: test-hub/findings/20261006-0830-help-request-final-own-harness.md

## Closed now
TikTok environment replacement is exhausted: run 37463242183 completed 30/30 infrastructure-success, but every inspected environment had AUTH_COOKIES=6 and redirected /upload to /login. Do not test more locale/viewport/headless permutations. Kwai direct URI/activity guessing remains exhausted.

## Help requested
### TikTok
Work only on obtaining/refeshing a legitimate central session for the owned account and persisting it to /tiktok/session-state. Do not launch another real canary until a read-only upload probe proves authenticated. Prefer supported login/session renewal; do not bypass CAPTCHA/2FA/challenges.

### Kwai
The repository now contains our own autonomous AccessibilityService harness. Current runtime builds the current APK instead of a stale artifact. Help inspect its first run and patch semantic/resource-id transitions until MAIN -> Profile -> login chooser -> Phone reaches Phone/OTP/challenge. If challenge requires owner action, persist all pre-challenge state in cloud so the handoff is one-time and runtime remains no-PC afterward.

### LIVE
Do nothing to HLS. Once Kwai READY/session artifact exists, inject it into LIVE and prove only Studio auth/recovery.

SUCCESS_SIGNAL: TikTok read-only /upload authenticated; Kwai Phone/OTP/challenge or READY via own harness.
