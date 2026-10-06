# TikTok canary v4 lease — superseded by concurrent v12 chain
STATUS: SUPERSEDED
AREA: tiktok-publish
DATE: 2026-10-06
SUPERSEDES: test-hub/findings/20261006-tiktok-canary-v4-fresh-queue-running.md

## Coordination result
Before this QA agent dispatched any v4 publication run, the shared workflow had already been advanced concurrently to v12 by another agent. Current workflow inspection showed JOB_ID/DEDUPE=tiktok-canary-20261006-synthetic-v12. Therefore this QA agent did not dispatch v4 and will not compete for tiktok-publish.

## Current evidence audited
Run 37416752186 (v12) failed before publication because the control request returned HTTP 401. No publication evidence was produced. This is a control/OIDC authorization boundary failure, not a TikTok publisher failure and not production proof.

## Safety consequence
No competing real-publish attempt is launched from this lease. Preserve the concurrent v12 chain and resolve its authorization/deployment state under the owning agent/lease before another canary.