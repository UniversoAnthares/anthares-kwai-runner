# WP QA P0 scheduled SYSTEM post-merge acceptance lease
STATUS: RUNNING
AREA: wordpress-qa-auth
DATE: 2026-10-27
OWNER: ChatGPT GitHub connector
BRANCH: evidence/wp-qa-p0-system-live-20261027
LEASE: 30 minutes
SUPERSEDES: none

BASELINE_PROVEN: PR #1720 was merged after a real SYSTEM SID and SSH read and 28/28 tests. Codeberg mirror remained at known earlier source; local scheduled scanner was still failing AUTH_MISSING until authorized same-host bounded fallback was installed.
FAILED_AVOIDED: No repeat credential probes; no public publishing or WordPress write; no Codeberg divergent or force-push change; only documentation from actual scheduled log and task code 0.
SUCCESS_SIGNAL: real original scheduled SYSTEM task task-result zero and CORTES_QA_ROUTER_OK sources_failed=0, wordpress source logged.
FAILURE_SIGNAL: terminal nonzero or AUTH_MISSING recurrence; needs causal investigation, not retry loop.
TEST_VALIDITY: scheduler log plus Task Scheduler status under actual SYSTEM; no synthetic result.
