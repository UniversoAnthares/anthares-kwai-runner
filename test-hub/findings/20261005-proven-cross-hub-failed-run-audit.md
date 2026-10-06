# Cross-hub failed-run audit and disposition
STATUS: PROVEN
AREA: qa / test-hub
DATE: 2026-10-05
RUN: 37400963267 ; 37401034918 ; historical runs cited below
JOB: audit
COMMIT: pending
SUPERSEDES: none

## Scope
Audit recent FAILED/PARTIAL/INVALID findings to distinguish live blockers from historical harness failures already closed by causal fixes. No active kwai-login lease was mutated and no media publication was performed.

## SUPERSEDED / CLOSED
- Android Agent setup-android/sdkmanager-tools harness failures (37396743483, 37396753682): closed by hosted-SDK build PROVEN run 37397385606 / job 112056483320.
- Cloudflare v12 multi-account selection failure: closed by later authenticated OAuth deployments through v16; current production v16 regression is green.
- Production queue curl harness failure 37392227134: closed by corrected transport and later v14-v16 production OIDC self-tests.
- failure_counter_reset real bug 37392715203: closed by v14 fix; current v16 run 37401034918 reports failure_counter_reset=true.
- heartbeat normal-exit race 37397420475: closed by wrapper fix run 37397505057 and final real publisher wiring run 37400963267.
- old TikTok central-session 401/403/rehydrate blockers: central session read is PROVEN run 37394495580; Render direct prepublish/session identity is PROVEN run 37396243429.
- old private-runner Cloudflare deploy failures: mechanism remains quarantined, but they are not a current Cloudflare blocker because OAuth deployment path has deployed v12-v16.

## VALID BLOCKERS — DO NOT BLIND-RETEST
- Kwai login/runtime navigation remains the highest-failure area, but is under an active independent kwai-login lease. Bare exported auth URIs and pre-normalization route matrices are already causally exhausted.
- TikTok anonymous YouTube caption/media acquisition remains blocked: yt-dlp anti-bot, timedtext empty, Invidious tracks empty/failing, public player response 429, and this repo lacks YOUTUBE_COOKIES/WP/FTP media credentials. Do not repeat anonymous client matrices.
- TikTok real controlled publication remains dependent on a controlled cloud media source/canary, not on publisher readiness; direct Render prepublish path is already PROVEN.

## Current regression evidence
Run 37401034918 / job 112068028605: production Cloudflare v16 OIDC queue self-test HTTP 200; all queue/fencing/renew/crash/reconcile/circuit-breaker flags true.
Run 37400963267 / job 112067807899: heartbeat contract and actual kwai_publish heartbeat wiring both green.

## Decision
No additional safe retest exists that would add causal information without either colliding with the active kwai-login lease or repeating an explicitly exhausted anonymous YouTube path. Historical red runs above are retained append-only as evidence, but must not be counted as current unresolved failures.
