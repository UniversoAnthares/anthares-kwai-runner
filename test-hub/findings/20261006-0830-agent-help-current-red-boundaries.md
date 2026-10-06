# Agent help — only current red boundaries
STATUS: OPEN
DATE: 2026-10-06

CLOSED: TikTok v15 reconciliation 30-way, inventory isolation, central session baseline, Kwai APK auth component discovery, Phone surface, Android runtime, SHA dedupe, control static safety, public HLS.

TIKTOK:
Run 37461651712 failed uniformly at /tiktok/session-state HTTP 401 before browser testing. Cause isolated: tiktok-15env-replacement.yml was absent from the narrow Cloudflare OIDC workflow allowlist. Source was patched and central deploy triggered. Please verify deployed revision, then rerun the 15-environment diagnostic only if authorization is 200. Do not treat the 15 failures as browser/environment evidence and do not run parallel publications.

KWAI:
Exported Auth Route QA30 and Direct Auth Entry QA30 remain red. Please classify failures into infrastructure-invalid vs route-reached-no-auth-surface using APK discovery evidence. Stop rerunning adb PATH/bootstrap variants once the runtime is proven. If no exported semantic route reaches an authenticatable surface, implement the persistent cloud Android session/bootstrap service rather than another coordinate/deeplink matrix.

LIVE:
Public HLS is closed. Reuse the same authenticated persistent Kwai session for Studio/app-native LIVE. Focus only on authenticated continuity/challenge; no CAPTCHA/OTP bypass.

Please append exact findings and preserve leases before serialized mutation.
