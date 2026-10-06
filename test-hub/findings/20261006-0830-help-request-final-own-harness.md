# Help request — final own-harness path
STATUS: RUNNING
AREA: tiktok, kwai, live
DATE: 2026-10-06
RUN: pending from 06977ed7b3ab13d1b9d9d9fd7641d54bc3ec1baf
JOB: none
COMMIT: 06977ed7b3ab13d1b9d9d9fd7641d54bc3ec1baf
SUPERSEDES: test-hub/findings/20261006-0815-help-request-exported-auth-qa30.md

## Encerrar
TikTok V15 reconcile 30/30 = PROVEN absent. Kwai APK auth component discovery = PROVEN. Kwai direct/exported URI/component routes are now exhausted: run 37462410069 reached DIRECT30_EXHAUSTED; do not repeat URI guessing. Android Agent runtime/build, Phone static selector, control-plane safety, dedupe and LIVE HLS remain closed/PROVEN.

## TikTok — ajuda específica
The 15-environment matrix failed before browser probing because /tiktok/session-state returned 401. The workflow is already in Worker source allowlist; Worker was redeployed and the indispensable matrix was expanded to 30. Analyze only post-deploy QA30. If all 30 reach central session but upload auth is rejected, stop browser-environment permutations and propose a session-refresh mechanism rather than another cosmetic matrix.

## Kwai — ajuda específica
Stop direct URI/activity guessing. Build our own Android harness on top of the PROVEN Anthares Android Agent runtime. It must:
- dismiss launcher/Chrome/system overlays deterministically;
- start Kwai normally;
- drive MAIN -> Profile -> login chooser -> Phone using semantic/resource-id selectors;
- capture UI XML + foreground activity after every transition;
- persist resulting app data/session artifact in cloud storage when READY;
- expose that artifact for both publish and LIVE executors.
Run 30 read-only transition variants inside one healthy runtime or equivalent isolated healthy runtimes; never create 30 real posts.

## SUCCESS_SIGNAL
TikTok: one authenticated upload surface followed later by one fenced canary only.
Kwai: Phone/OTP/challenge or READY observed by our harness; session artifact persisted.
LIVE: reuse Kwai READY artifact; HLS must not be retested.
