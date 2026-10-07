# Causal diagnosis — interactive login run 37529160444 failed on preparation gate, not credentials
STATUS: PROVEN
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37529160444
JOB: remote-login
COMMIT: d04928d
SUPERSEDES: none

## Objetivo
Read-only causal classification of the last interactive remote login failure so the active kwai-login lease owner does not repeat credentialed autologin blindly.

## Resultado
The run reached every infrastructure milestone and failed solely on an unhandled Kwai preparation/download gate:
- ANDROID_READY, REMOTE_BASE_URL generated (tunnel OK), KWAI_INSTALLED_FROM_VALIDATED_VAULT, KWAI_UI_INTERACTIVE, KWAI_LOGIN_UI_OPENED.
- kwai_phone_surface_probe.py printed V2_LOGIN_NODES=0 and V2_AFTER_PHONE_UI=`sorry, the internet's a bit slow. hang in there! | 5% | skip`.
- kwai_android_autologin.py then exited 3 (`if not fill(LOGIN): raise SystemExit(3)`) because no editable node existed yet -> logged as KWAI_AUTO_LOGIN_NEEDS_INTERACTION_RC=3.
- Screenshot kwai-remote-ready.png (artifact 11444356887) shows modal "Skip the preparation? / Yes, skip / Cancel" over a resource download stuck at 5%.
- The 600s human window then expired with no owner interaction: FAIL: login-window-expired-600s (exit 28).

## Evidência decisiva
Log lines: `V2_AFTER_PHONE_UI=sorry, the internet's a bit slow. hang in there! | 5% | skip`, `KWAI_AUTO_LOGIN_NEEDS_INTERACTION_RC=3`, `FAIL: login-window-expired-600s`. Artifact screenshot shows the preparation modal, not a CAPTCHA, not wrong credentials.

## Consequência
- RC=3 in this run does NOT mean credentials failed and must not be used as evidence of an auth blocker; the login form was never on screen.
- Before any future credentialed attempt: settle the preparation gate first (bounded wait for the 5% resource download to finish, or explicitly tap "Yes, skip"), then re-dump and only then run autologin.
- The interactive window requires the owner to open the URL within 600s; dispatch only when the owner is ready to authenticate immediately.
- This agent ceded kwai-login: lease 20261007-lease-kwai-login-surface-discovery.md (expires 2026-10-07T03:30:00Z) is authoritative and run "Kwai Login Surface Discovery Probe" was in progress at read time. No mutation performed.
