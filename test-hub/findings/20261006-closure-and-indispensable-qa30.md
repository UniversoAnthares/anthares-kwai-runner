# Kwai closure classification + indispensable QA30
STATUS: PROVEN
DATE: 2026-10-06
AREA: Android/Kwai authentication

## Closed subjects
Treat as closed and do not retest absent regression evidence:
- AVD lookup/path and KVM boot.
- Kwai split APK installation.
- Agent APK installation and AccessibilityService.
- onboarding -> MAIN.
- MAIN -> Profile -> real Login chooser.
- semantic login selector QA15.
- READY proof gate QA15.
- publication promotion contract QA15.
- control-plane fencing/exactly-once/reconciliation.

## Discarded / non-indispensable failures
- Kwai Studio via Chrome first-run is not authentication evidence for the Android app; do not block project on it.
- legacy kwai-android-rescue-single and android-adb-boot-30 failures are noisy/superseded unless a new regression points back to them.

## New indispensable diagnosis
Autologin run 37456137350 failed RC=3 while UI showed Resource downloading / all features available when done. Credentials were present. This is pre-auth resource readiness, not credential rejection.
FSM now treats RESOURCE_LOADING explicitly and waits/fails closed rather than navigating blindly.
Runtime 37457624666 then completed SUCCESS and again proved LOGIN_SURFACE_REACHED.

## QA30
Run 37458446525: SUCCESS.
30-case Phone-surface semantic selector matrix passed. Signal KWAI_PHONE_SURFACE_QA30_OK=30.

## Remaining hard boundary
Real Phone authentication form/OTP or password challenge must be completed in a stable cloud Android session. Only a genuine authenticated observation may create READY proof. Do not synthesize READY.
