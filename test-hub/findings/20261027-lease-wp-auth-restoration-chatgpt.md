# WP-CORTES authenticated QA — isolated lease 2026-10-27
STATUS: RUNNING
AREA: wordpress-qa-auth
DATE: 2026-10-27
RUN: pending
JOB: pending
COMMIT: ed5ae1100535e745ab95555d9ba1b3f778d7734f
SUPERSEDES: none

## Ownership / expiration
Owner: ChatGPT via authorized GitHub connector. Isolated branch: `qa/wp-state-auth-restoration-20261027-chatgpt`. Lease expires 30 minutes after creation; no production mutation, publishing, account change or secret export.

## Baseline and validity
BASELINE_PROVEN: `https://anthares.us/wp-json/anthares/v1/cortes/state` returned anonymous HTTP 401 from Windows on 2026-10-27; `tools/cortes_qa_p0_router.py` already supports Application Password through `WP_SITE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD` GitHub environment variables.
FAILED_AVOIDED: anonymous GET remains 401 by design; no bypass or replay of wrong authentication and no copied secrets.
SUCCESS_SIGNAL: isolated Actions runner confirms all three secret references are present, performs authenticated HTTPS Basic request and records HTTP 200 and valid JSON `items`/`blocker` structure, without payload/credential logging.
FAILURE_SIGNAL: sanitized `AUTH_MISSING`, `HTTP_401`, `HTTP_403`, `HTTP_404`, `NETWORK_UNAVAILABLE`, or `INVALID_RESPONSE`.
TEST_VALIDITY: runner actually starts, checkout succeeds, dependency-free Python probe executes, and output includes `WP_QA_AUTH_RESULT=`; queued/skipped/disabled runner is INVALID, not evidence of auth failure.

## Isolation
Read-only, one-off branch-triggered QA only; no schedule. No modification to production, secrets, privileged profiles, publicators or main branch. Fencing: avoid any concurrent mutation of wordpress-qa-auth area. Preserve existing 12-hour routine QA cadence.
