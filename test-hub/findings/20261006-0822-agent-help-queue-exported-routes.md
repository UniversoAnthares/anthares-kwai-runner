# Targeted agent request — queue drain + exported Kwai routes
STATUS: OPEN
DATE: 2026-10-06

Closed permanently: TikTok reconciliation 30-way SUCCESS (37459757627), central session preflight 15/15, Kwai APK auth component discovery SUCCESS (37460279417), Phone surface QA30, Android runtime, SHA dedupe, control safety, public HLS.

TikTok: direct V15 run 37461325735 failed before publication_started because exact lease was unavailable after only 12 safe queue-drain attempts. This is not a browser/session failure. Queue drain was widened to 60 safe prepublication leases and a single serialized retry was triggered. Please inspect only queue ordering if it still cannot acquire the exact canary. Do not start a competing publication and do not rerun reconciliation before publication.

Kwai: exported auth route QA30 is the active indispensable matrix. Please identify which exported route, if any, reaches an editable/authenticatable surface while preserving app state. Consume APK discovery evidence; avoid hidden/non-exported Activity invocation and coordinate tapping. If none succeeds, help implement the custom persistent cloud Android session/bootstrap service (encrypted snapshot/restore + READY health + lease/fencing).

LIVE: HLS is closed/proven. Reuse the Kwai authenticated session/bootstrap for Studio or app-native LIVE; focus only on session continuity/challenge. Do not bypass CAPTCHA/OTP.
