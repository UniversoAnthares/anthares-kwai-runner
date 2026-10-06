# Agent help request — after QA30 boundary isolation
STATUS: OPEN
DATE: 2026-10-06
AREA: TikTok reconciliation + Kwai auth/LIVE

## Closed — do not repeat
- Kwai Phone label/surface classifier: 30/30 PROVEN, run 37458446525.
- Kwai public HLS: PROVEN; latest run 37458347863 reached valid playlist/segments before Studio auth challenge.
- TikTok inventory isolation: 30-way success, run 37457811374.
- Kwai SHA dedupe and control static safety: success, runs 37459640281 / 37459640265.
- Android Agent Runtime baseline already has successful runs; do not treat old rescue-workflow noise as a new blocker.

## Failed indispensable boundaries
### TikTok
- 30-way v15 reconciliation run 37458261489 failed at protected /tiktok/session-state HTTP 401.
- Source allowlist was patched narrowly for tiktok-v15-reconcile-30.yml (commit dda96ae3b477d76e7f11ce153e14674686efd4dc), but run 37459685223 still showed 401 on deployed control for at least some replicas: source/deployment skew remains.
- A newer reconciliation run 37459757627 is active. Do not launch a competing publication/reconcile mutation.
**Help requested:** identify/deploy the exact Cloudflare Worker revision or reuse an already-deployed allowlisted workflow identity for read-only v15 inventory reconciliation. Preserve narrow OIDC authorization; no wildcard.

### Kwai Phone
- Real Phone Tap QA30 run 37459066864 exhausted 30 coordinate variants without reaching an editable phone form.
- The workflow repeatedly backs out between taps; this suggests the Phone affordance may open a different Activity/dialog/WebView or require semantic child/parent action rather than coordinate offsets.
**Help requested:** inspect after-tap `dumpsys window windows`, `dumpsys activity activities`, package/activity transitions, WebView presence, accessibility node clickability/parent chain, and screenshots. Build a 30-case reversible navigation matrix only; do not submit credentials/OTP.

### Kwai LIVE
- HLS is good; Studio web stops at `KWAI_STUDIO_CHALLENGE_REQUIRED`.
**Help requested:** find supported no-PC continuity: Android authenticated session -> Studio session, or app-native LIVE configuration/start. Do not bypass CAPTCHA/challenge.

## Replacement rule
If a third-party free runtime remains unreliable, prefer building our own control/executor layer on already-proven GitHub Actions + Android emulator + central queue. Production must not depend on Lucas's PC.
