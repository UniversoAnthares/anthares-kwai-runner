# Item fixo 9 — Harness quota detection window, strict bounded expansion
STATUS: RUNNING
AREA: github-ci/quota-provider-cancel/harness-discovery
DATE: 2026-10-29
RUN: none
JOB: none
COMMIT: b75088574f4570741142e663f484cac00e767b69
SUPERSEDES: none

BASELINE_PROVEN: GitHub owned cancel controlled runs 40502470893 cancelled and 40502486145 succeeded; GitLab quota pipeline 2994547840 independent successor 40510154187 succeeded; current scheduled external watcher 40992530819 succeeded with live Harness/AppVeyor/Bitrise read-only authentication, HARNESS_QUOTA=NO_RECENT_OWNED_RUNS and QUOTA_EVENTS=NO_STRUCTURED_EVENTS. Current Harness discovery inspects only six most recent main commits every 15 min; observed bursts on main exceeded six commits inside an interval.
FAILED_AVOIDED: no quota fabrication, no cancellation of unrelated job, no re-dispatch, no publisher, no additional provider authorization, no broad rewrite of the watcher.
SUCCESS_SIGNAL: on a safe branch, bounded discovery identifies a valid Harness commit status after position six and preserves strict ownership, exact execution identity, structured quota and fail-closed gates; existing CI contracts PASS.
FAILURE_SIGNAL: only first six inspected, unbounded requests causing job timeout, wrong-owner events accepted, any provider-side effects during tests, failing CI.
TEST_VALIDITY: offline unit regression through existing branch-scoped CI; does not prove a real natural Harness quota cancellation. Deployment to main gated on passing check and current HEAD review.
