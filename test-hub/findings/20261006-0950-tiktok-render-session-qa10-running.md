# TikTok Render session QA10 — running
STATUS: RUNNING
DATE: 2026-10-06
AREA: tiktok
RUN: 37472870400
COMMIT: 4434654b5b102e2e8248bab2a2b6e050acba9c6b

## Cause from failed predecessor
Run 37472086588 resolved the prior authorization failure: central session HTTP 200 with 21 cookies, Render bootstrap HTTP 200, Render session-status HTTP 200 and bootstrapped=true. The remaining failure was only POST /session-test => HTTP 504, error=session test timeout, identity_verified=false.

## QA10
Ten simultaneous reversible probes now isolate that boundary:
- replicas 1..5: read-only session-test with increasing time budgets;
- replicas 6..10: bootstrap + session-status control group only.
No replica publishes, submits credentials, mutates account auth, or starts LIVE.

Do not repeat the old 403 hypothesis. Classify QA10 by functional signals, not workflow color.
