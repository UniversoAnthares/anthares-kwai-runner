# TikTok QA10 invalid; allowlisted QA30 causal successor
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-06
RUN: 37472870400; successor pending from 117859531b9af4958a46d247455ce8e3cf52b16e
COMMIT: 117859531b9af4958a46d247455ce8e3cf52b16e

## BASELINE_PROVEN
Run 37472086588 proved central session HTTP 200 with 21 cookies, Render bootstrap HTTP 200 and session-status HTTP 200 bootstrapped=true. The remaining valid observation was session-test HTTP 504 with identity_verified=false.

## QA10 classification
All ten replicas in 37472870400 stopped at CENTRAL_SESSION http=401 cookies=0. Therefore QA10 is INVALID for the Render-timeout hypothesis; it used a new workflow identity not allowlisted by the control plane. Do not interpret the ten red jobs as ten session failures.

## Causal successor
The 30-way reversible diagnostic matrix was moved into the already-proven allowlisted tiktok-central-session-read workflow. It uses 30 parallel replicas: 20 session-test observations across bounded timeout budgets and 10 bootstrap/session-status controls. It does not publish, submit credentials, alter account authentication or start LIVE.

## SUCCESS_SIGNAL
Allowlisted central read remains HTTP 200; controls bootstrap/status remain valid; any identity_verified=true is immediately actionable for serialized READY/canary.

## FAILURE_SIGNAL
All valid session-test replicas independently remain timeout/not-verified while controls remain healthy, isolating provider session validity rather than infrastructure.

## Coordination
Do not repeat QA10 or create new browser/locale/viewport matrices. Preserve active Kwai lease/run independently.
