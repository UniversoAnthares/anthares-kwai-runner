STATUS: RUNNING
AREA: kwai-login
OWNER: chatgpt-kwai-repair
STARTED_AT_UTC: 2026-10-09T14:55:00Z
EXPIRES_AT_UTC: 2026-10-09T15:25:00Z
SCOPE: Diagnose and repair persistent Kwai Android offline screen, harden remote text entry, and validate with fresh workflow run. Preserve existing PROVEN results; no PC executor; no Android benchmark repetition.

EVIDENCE:
- User-provided diagnostics show Kwai foreground plus the UI error "Please check your Internet connection" while Kwai Cronet/Hodor CDN requests return HTTP 206/OnSucceeded. This is not a total network outage; treat as stale/app-level offline state or Android validation/configuration problem.
- Added kwai_android_network_recovery.sh: Android network preflight, Private DNS/proxy normalization when stale, offline-screen detector, automatic Retry, and delayed Kwai relaunch only after persistent failure while Google SSO is not foreground.
- Workflow now starts network tracing before authentication and runs the offline watchdog during owner login.
- Remote credential entry is masked and cleared immediately after submission.
- Remote UI now re-verifies and suppresses Android show_touches/pointer_location continuously instead of trusting a one-time flag.

COMMITS:
- b181fd90e0a0a4b5387fb8ce2027ce1fcec54b2a network recovery helper
- 5a60830bfe1f7a7417ed8b217958e50035613fb3 workflow integration + pre-auth diagnostics + credential redaction
- 5bea9ed70688e48378ccfd2928ac8be147b2874e continuous touch-marker suppression in remote UI
- 17882d015853e5764ed0cadc6d4b880bdf602fb9 preserve SSO callback before persistent offline relaunch

VALIDATION:
- Fresh run 37947977836 started from 5a60830b (older of the two fixed revisions).
- Fresh run 37948197230 started from 17882d0 and therefore includes all fixes above; currently running.
