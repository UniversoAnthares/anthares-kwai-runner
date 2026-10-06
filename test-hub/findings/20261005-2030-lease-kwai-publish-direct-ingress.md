# Lease kwai-publish: close stale direct-send probe and advance deterministic ingress
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: kwai-publish
COMMIT: pending
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2104-kwai-publish-lifecycle-static-proven.md; Cloudflare v12 is production-PROVEN; ACTION_SEND video/* contract is statically proven.
FAILED_AVOIDED: run 37392541208 ended before FSM_MAIN_REACHED with FSM_TIMEOUT, so direct ACTION_SEND remains NOT_TESTED; no repetition is allowed without a causal change to the precondition path. Prior shell and ffmpeg harness failures remain avoided. No Publish action will be used.
SUCCESS_SIGNAL: stale RUNNING is classified from decisive logs; then an independent or causally repaired non-publishing media-ingress test reaches declared preconditions and produces observable editor/media-selection evidence.
FAILURE_SIGNAL: a new test repeats the same FSM timeout without causal repair, mutates login/session, or reaches any Publish action.
TEST_VALIDITY: publication remains quarantined; any media-ingress hypothesis requires FSM_MAIN_REACHED or an explicitly different proven entry precondition, exact media identity, Android intent result, and post-action UI evidence.
LEASE_AREA: kwai-publish
LEASE_EXPIRES: 2026-10-06T01:00:00Z

## Objetivo
Reconcile the stale direct-send experiment, preserve the proven started-before-commit lifecycle, and advance deterministic media ingress without touching kwai-login or publishing real content.
