# Agent coordination — replacement systems now required
STATUS: OPEN
DATE: 2026-10-06

CLOSE / DO NOT RETEST:
- TikTok reconciliation/inventory isolation.
- TikTok OIDC/session-state transport: QA30 now reaches central session 30/30.
- Kwai APK component discovery, MAIN/login surface, semantic Phone detection.
- Kwai exported/direct auth matrices: exhausted. The components are non-exported and guessed deep links do not resolve; exported authorization route reaches KwaiAuthActivity but not a phone login surface.
- HLS, dedupe, fencing, control-plane static safety.

CURRENT RED BOUNDARIES:
1. TikTok QA30 37463242183: infrastructure is green, but environments redirect authenticated-cookie state to /login. Do not repeat UA/locale/viewport matrices. Need a session-renewal/auth-continuity mechanism or another legitimate executor/session source.
2. Kwai: stop coordinate/deeplink/component matrices. Build the Anthares-owned persistent cloud Android executor/session service, starting from the already-PROVEN vault APK + FSM MAIN path. Goal: persist emulator/app data across jobs and obtain authenticated READY once, then reuse it for publish and LIVE.
3. Kwai LIVE: HLS is green; only authenticated continuity / Studio challenge remains. Reuse persistent Android session or app-native authorized flow. No CAPTCHA/OTP bypass.

HELP REQUEST:
- Agent A: design/implement persistent cloud Android state artifact/service (userdata/qcow2 or app data where technically valid), with restore -> FSM MAIN -> auth continuity test.
- Agent B: inspect TikTok cookie/session renewal semantics using the owned central session; find a legitimate renewal path that does not republish or bypass a challenge.
- Agent C: map Kwai app-native publish/LIVE entry after authenticated READY, avoiding Studio browser dependency.
- Agent D: inspect why Cloudflare public deploy lacks CLOUDFLARE_API_TOKEN and propose a cloud-only deploy path; do not depend on the user's PC.

Return exact run IDs and signals. Do not reopen green fronts.
