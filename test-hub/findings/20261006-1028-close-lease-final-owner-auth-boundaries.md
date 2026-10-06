# Close lease — final owner-auth boundaries
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-06
RUN: 37472029269
JOB: 112297688624
COMMIT: 7409893e2125fa1da665795a8cd9ebec63ceb08c
SUPERSEDES: test-hub/findings/20261006-1022-lease-kwai-phone-chrome-fre-closure.md

## Resultado
The attempted pre-Phone Chrome FRE priming was withdrawn after coordination finding 20261006-0958 proved it repeated prior commits 2d30108/55e271b. Repository workflow was restored without that duplicate block. The authoritative causal successor is run 37472029269, which dismisses the independent Chrome notification education dialog and performs 30 reversible Studio/web-auth observations.

## Closed
Do not reopen: Kwai READY QA30; Android MAIN/login chooser; Phone target discovery; direct URI/activity routes; HLS; queue safety/dedupe/fencing; TikTok reconciliation/inventory/browser-environment QA30.

## Remaining external boundaries
TikTok official API client is implemented but the expected account still needs a legitimate developer-app OAuth grant/token with video.publish/video.upload. No token may be fabricated or bypassed.
Kwai final auth may require the account owner's Phone/OTP/challenge after the active read-only run identifies the exact surface. No OTP/CAPTCHA/challenge bypass is authorized or attempted.

## Consequence
No additional exploratory matrices are justified. After the active read-only run, only owner authorization (if demanded by provider) and then one serialized production canary per platform remain. LIVE reuses the proven Kwai session and already-proven HLS.
