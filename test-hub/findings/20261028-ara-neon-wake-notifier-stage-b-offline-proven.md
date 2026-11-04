# ARA wake post-commit notifier — Stage B isolated contracts
STATUS: PROVEN
AREA: anthares-remote / neon-idle-optimization
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40761131838
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40761131838/job/123073051267
COMMIT: 49e4190ba2e4211f7dfd4e0e9f3ac88d64415bfc
SUPERSEDES: 20261028-ara-neon-wake-notifier-stage-b-running.md

## Scope
Isolated source-only post-commit notifier in canonical Vercel ARA router.
A wake notification is triggered only after the database upsert returns a row,
and only if protected ARA_WAKE_NOTIFY_ENABLED=1 is set later. Default OFF.

## Decisive evidence
GitHub Actions job 123073051267 completed success. Isolated Node tests
covered: default-OFF must not call network; absent secret fails closed;
exact HMAC/URL/body and no commands or tokens; delivered=0 unconfirmed;
transport exceptions do not reject a committed job; 401,403,429,503
not treated as success; router JS parses. Source syntax/logic is not
an end-to-end production verification.

## Operational boundary
No Cloudflare Worker deployment, secret, Vercel env, publishing, Windows
binary, C8 supervisor, Neon lease, OAuth or existing polling was altered.
No observed websocket connection, command wake, autosuspend or CU savings.
Main branch moved concurrently after staging; an exact-head reread and
peer reconciliation are mandatory before any merge or deployment.
Stage C canonical agent integration is still pending.
