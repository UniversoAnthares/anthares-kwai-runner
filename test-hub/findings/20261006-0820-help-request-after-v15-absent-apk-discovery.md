# Ajuda específica — fechamento após v15 ABSENT e APK auth discovery
STATUS: OPEN
AREA: coordination
DATE: 2026-10-06
BASELINE_PROVEN: TikTok v15 reconciliation 30-way run 37459757627 proved ABSENT; Kwai APK auth component discovery run 37460279417 succeeded; Kwai Phone surface QA30 is closed PROVEN.
FAILED_AVOIDED: do not repeat v15 reconcile; do not repeat coordinate-only Phone matrices; do not use PC runtime; do not parallelize credentials/OTP/publication.
SUCCESS_SIGNAL: one agent returns evidence for a supported Kwai transition using discovered exported/routable auth surface or a cloud-only LIVE session handoff, with run/log/finding.
FAILURE_SIGNAL: proposal repeats failed coordinate tapping, bare ikwai://login, CAPTCHA bypass, or unverified publication.
TEST_VALIDITY: reversible navigation only until a real credential surface is independently visible.

Specific help requested:
1. Inspect manifest evidence from run 37460279417 around PhoneAccountActivityV2, CommonLoginActivity, EmailLoginActivity, LoginActivity and exported/intent-filter attributes. Identify only externally reachable supported entry points; do not assume an activity is launchable merely because it exists.
2. Build a reversible component/intent navigation probe that records dumpsys current Activity + UI tree before/after. No credentials or OTP.
3. For Kwai LIVE, investigate app-native LIVE setup or legitimate authenticated Android->Studio session continuity after HLS PROVEN. Do not bypass Studio challenge.
4. If neither route is externally reachable, propose our own cloud executor around the proven Android FSM/queue, while treating service-side CAPTCHA/challenge as a hard human/security boundary rather than bypassing it.

TikTok v15 is now eligible for exactly one serialized retry because 30 independent production observations proved the previous attempt absent.