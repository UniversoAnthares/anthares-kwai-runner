# Lease — AOI16 Instagram Buffer run #77, fechamento diagnóstico documental
STATUS: RUNNING
AREA: cortes-instagram-buffer-readback-diagnostics
OWNER: ChatGPT AOI16 2026-11-06
BASE_MAIN_SHA: 739ddf3f695786abb55180722071dcf81a22b611
GOVERNANCE_MANIFEST: 223433740e807a90
TARGET: test-hub/findings/20261106-aoi16-buffer-run77-error-diagnostic-proven.md
DATE_UTC: 2026-11-06
LEASE_EXPIRY: 30 minutes after creation, maximum; documentary mutation only.
BASELINE_PROVEN:
- GitHub PR #2132 merged as 739ddf3f695786abb55180722071dcf81a22b611. Protected publish job is fail-closed.
- Workflow run 42296479923 succeeded on 2026-11-06T21:24:49Z in reconcile-only mode, with 0 new posts and 0 confirmed.
- All 3 prior buffer_scheduled records returned status=error in authenticated Buffer lookup; 7 uncertain records remain in Neon.
FAILED_AVOIDED: No blind resubmit, no manual SQL transition, no new publication, no secrets, no replay of identical readback.
SUCCESS_SIGNAL: Append-only final finding with exact evidence, precise open incident and non-PROVEN production classification; leave queue untouched.
FAILURE_SIGNAL: Unexpected HEAD change or competing lease; abort.
TEST_VALIDITY: Current run logs + read-only Neon counts; not a new media/provider test.
COST_ADDED: R$0
BRANCH: docs/aoi16-instagram-run77-final-20261106
